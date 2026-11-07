from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_, select

from ..models import Fixture, Order, Payment, Ticket, TicketStatus, Zone
from .base import SqlRepository

# A pending ticket holds its seat this long. Longer than the Stripe session (31 min) so a
# payment can never complete after the hold has lapsed.
HOLD = timedelta(minutes=35)


def taken_seats(now: datetime):
    """SQL for the tickets that occupy a seat: paid ones, and unexpired holds."""
    held = and_(Ticket.status == TicketStatus.PENDING, Order.created_at >= now - HOLD)
    return (Ticket.order_id == Order.id) & or_(Ticket.status.in_([TicketStatus.VALID, TicketStatus.USED]), held)


class OrderRepository(SqlRepository[Order]):
    model = Order


class PaymentRepository(SqlRepository[Payment]):
    model = Payment

    def get_by_ref(self, provider_ref: str, *, lock: bool = False) -> Payment | None:
        q = select(Payment).where(Payment.provider_ref == provider_ref)
        return self.db.scalar(q.with_for_update() if lock else q)


class TicketRepository(SqlRepository[Ticket]):
    model = Ticket

    def taken(self, fixture_id: int, zone_id: int, now: datetime) -> int:
        q = select(func.count(Ticket.id)).select_from(Ticket).join(Order, taken_seats(now))
        return self.db.scalar(q.where(Ticket.fixture_id == fixture_id, Ticket.zone_id == zone_id))

    def for_order(self, order_id: int) -> list[Ticket]:
        return list(self.db.scalars(select(Ticket).where(Ticket.order_id == order_id)))

    def get_by_code(self, code: str, *, lock: bool = False) -> Ticket | None:
        q = select(Ticket).where(Ticket.code == code)
        return self.db.scalar(q.with_for_update() if lock else q)

    def paid_for_user(self, user_id: int) -> list[tuple[Ticket, Fixture, str]]:
        """Issued tickets of one user with their fixture and zone name, next match first."""
        q = (
            select(Ticket, Fixture, Zone.name)
            .join(Order, Order.id == Ticket.order_id)
            .join(Fixture, Fixture.id == Ticket.fixture_id)
            .join(Zone, Zone.id == Ticket.zone_id)
            .where(Order.user_id == user_id, Ticket.status.in_([TicketStatus.VALID, TicketStatus.USED]))
            .order_by(Fixture.kickoff_at, Ticket.id)
        )
        return [tuple(row) for row in self.db.execute(q)]

    def has_sold(self, fixture_id: int, now: datetime) -> bool:
        """True if any ticket for the fixture is paid or held by an open checkout."""
        q = select(Ticket.id).join(Order, taken_seats(now)).where(Ticket.fixture_id == fixture_id)
        return self.db.scalar(q.limit(1)) is not None
