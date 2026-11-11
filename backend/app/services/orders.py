import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..activity import log_activity
from ..config import get_config
from ..errors import ConflictError, NotFoundError, PaymentError
from ..gateways import Line, PaymentGateway
from ..models import (
    FixtureStatus, JerseyDesign, JerseyItem, Order, OrderStatus, Payment, PaymentStatus, Ticket, TicketStatus,
    User, Zone,
)
from ..repositories import (
    ClubRepository, FixtureRepository, JerseyRepository, JerseyTemplateRepository, OrderRepository,
    PaymentRepository, TicketRepository, UploadRepository,
)
from ..schemas import CheckoutRequest, FixtureOut, TicketOut

SESSION_LIFETIME = timedelta(minutes=31)  # Stripe accepts 30 minutes at the least
# shortcut: one fixed price for every jersey; move it to the jersey templates or clubs when prices should differ.
JERSEY_PRICE_BANI = 15000


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OrderService:
    """Buying tickets: reserve seats, hand over to the payment page, issue tickets when paid."""

    def __init__(self, db: Session, gateway: PaymentGateway | None = None) -> None:  # no gateway needed to read tickets
        self.db = db
        self.gateway = gateway
        self.fixtures = FixtureRepository(db)
        self.orders = OrderRepository(db)
        self.payments = PaymentRepository(db)
        self.tickets = TicketRepository(db)
        self.clubs = ClubRepository(db)
        self.jerseys = JerseyRepository(db)
        self.templates = JerseyTemplateRepository(db)
        self.uploads = UploadRepository(db)

    def checkout(self, user: User, req: CheckoutRequest, now: datetime | None = None) -> str:
        """Hold the seats, start the payment, and return the URL to send the buyer to."""
        now = now or _now()
        fixture = self.fixtures.get(req.fixture_id)
        if fixture is None:
            raise NotFoundError("Fixture not found")
        if fixture.status != FixtureStatus.SCHEDULED or fixture.kickoff_at <= now:
            raise ConflictError("Tickets for this match are no longer on sale")

        jersey_club = self._check_jersey(user, req)  # before the lock: do not hold seats while validating

        # The row lock makes "count the seats, then take them" one step: two buyers of the last seat queue up here.
        sale = self.fixtures.lock_zone(req.fixture_id, req.zone_id)
        if sale is None:
            raise NotFoundError("That zone is not on sale for this match")
        left = sale.quota - self.tickets.taken(req.fixture_id, req.zone_id, now)
        if left < req.quantity:
            raise ConflictError("Sold out" if left <= 0 else f"Only {left} seats left in this zone")

        order = self.orders.add(Order(user_id=user.id))
        for _ in range(req.quantity):
            self.tickets.add(Ticket(
                order_id=order.id, fixture_id=req.fixture_id, zone_id=req.zone_id,
                code=secrets.token_urlsafe(24), price_bani=sale.price_bani, status=TicketStatus.PENDING,
            ))
        # Read everything needed after the commit now: commit expires the loaded objects.
        order_id, price, amount = order.id, sale.price_bani, sale.price_bani * req.quantity
        match = f"{fixture.home_club.name} vs {fixture.away_club.name}"
        lines = [Line(f"{match}, {self.db.get(Zone, req.zone_id).name}", price, req.quantity)]
        if req.jersey:
            j = req.jersey
            design = self.jerseys.add_design(JerseyDesign(
                user_id=user.id, club_id=jersey_club.id, template_id=j.template_id, primary_color=j.primary_color.lower(),
                secondary_color=j.secondary_color.lower(), name_text=j.name_text, number=j.number, logo_upload_id=j.logo_upload_id,
            ))
            self.jerseys.add(JerseyItem(order_id=order_id, design_id=design.id, fixture_id=req.fixture_id, size=j.size, price_bani=JERSEY_PRICE_BANI))
            amount += JERSEY_PRICE_BANI
            lines.append(Line(f"Jersey {jersey_club.name} #{j.number} {j.name_text}, size {j.size}, pickup at {match}", JERSEY_PRICE_BANI, 1))
        self.db.commit()  # releases the lock before the slow call to the payment provider

        public = get_config().public_url
        try:
            session = self.gateway.create_checkout(
                order_id, lines,
                success_url=f"{public}/tickets?paid=1", cancel_url=f"{public}/fixtures/{req.fixture_id}",
                expires_at=now + SESSION_LIFETIME,
            )
        except PaymentError:
            self._cancel(order_id)
            self.db.commit()
            raise
        self.payments.add(Payment(order_id=order_id, provider=self.gateway.name, provider_ref=session.id, amount_bani=amount))
        self.db.commit()
        log_activity("checkout_started", user_id=user.id, order_id=order_id, amount_bani=amount)
        return session.url

    def _check_jersey(self, user: User, req: CheckoutRequest):
        """Look up what the jersey refers to; returns its club, or None when there is no jersey."""
        j = req.jersey
        if j is None:
            return None
        club = self.clubs.get_by_slug(j.club)
        if club is None:
            raise NotFoundError("Jersey club not found")
        if self.templates.get(j.template_id) is None:
            raise NotFoundError("Jersey template not found")
        if j.logo_upload_id is not None:
            upload = self.uploads.get(j.logo_upload_id)
            if upload is None or upload.user_id != user.id:  # someone else's upload looks the same as a missing one
                raise NotFoundError("Logo not found")
        return club

    def _cancel(self, order_id: int) -> None:
        order = self.orders.get(order_id)
        order.status = OrderStatus.CANCELLED
        for ticket in self.tickets.for_order(order_id):
            ticket.status = TicketStatus.CANCELLED

    def fulfil(self, session_id: str, amount_bani: int | None, now: datetime | None = None) -> None:
        """Payment succeeded: issue the tickets. Safe to call again for the same session (Stripe retries)."""
        payment = self.payments.get_by_ref(session_id, lock=True)
        if payment is None or payment.status == PaymentStatus.SUCCEEDED:
            return
        order = self.orders.get(payment.order_id)
        if amount_bani != payment.amount_bani or order.status != OrderStatus.PENDING:
            # Never issue tickets for money we cannot match to a live order; a human must look.
            log_activity("payment_rejected", order_id=order.id, paid_bani=amount_bani, expected_bani=payment.amount_bani, order_status=order.status)
            return
        payment.status = PaymentStatus.SUCCEEDED
        order.status = OrderStatus.PAID
        order.paid_at = now or _now()
        for ticket in self.tickets.for_order(order.id):
            ticket.status = TicketStatus.VALID
        self.db.commit()
        log_activity("payment_succeeded", user_id=order.user_id, order_id=order.id, amount_bani=payment.amount_bani)

    def expire(self, session_id: str) -> None:
        """The buyer never paid: give the seats back."""
        payment = self.payments.get_by_ref(session_id, lock=True)
        if payment is None or payment.status != PaymentStatus.PENDING:
            return
        payment.status = PaymentStatus.FAILED
        self._cancel(payment.order_id)
        self.db.commit()
        log_activity("payment_expired", order_id=payment.order_id)

    def my_tickets(self, user: User) -> list[TicketOut]:
        return [
            TicketOut(
                id=t.id, code=t.code, status=t.status, price_bani=t.price_bani, zone=zone,
                fixture=FixtureOut.model_validate(f), used_at=t.used_at,
            )
            for t, f, zone in self.tickets.paid_for_user(user.id)
        ]
