from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..activity import log_activity
from ..errors import AppValidationError, ConflictError, ForbiddenError, NotFoundError
from ..models import Fixture, FixtureStatus, FixtureZone, TicketStatus, User, Zone
from ..repositories import ClubRepository, FixtureRepository, TicketRepository
from ..schemas import FixtureCreate, FixtureDetail, FixtureOut, FixtureUpdate, ScanOut, ZoneOut, ZoneSaleIn
from ..security.access import ensure_club_staff


def _now() -> datetime:
    return datetime.now(timezone.utc)


class StaffService:
    """What a club's staff do: run their fixtures and scan tickets at the door."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.clubs = ClubRepository(db)
        self.fixtures = FixtureRepository(db)
        self.tickets = TicketRepository(db)

    def _detail(self, fixture: Fixture) -> FixtureDetail:
        zones = [ZoneOut(**z) for z in self.fixtures.zones(fixture.id, _now())]
        return FixtureDetail.model_validate(fixture).model_copy(update={"zones": zones})

    def _home_club(self, user: User):
        club = self.clubs.get(user.club_id) if user.club_id else None
        if club is None:
            raise ForbiddenError("Your account is not attached to a club")
        return club

    def venue_zones(self, user: User) -> list[Zone]:
        return self.fixtures.venue_zones(self._home_club(user).venue_id)

    def list_fixtures(self, user: User) -> list[FixtureDetail]:
        return [self._detail(f) for f in self.fixtures.for_home_club(self._home_club(user).id)]

    def _apply_zones(self, fixture: Fixture, zones: list[ZoneSaleIn]) -> None:
        """Put zones on sale, or change their price and quota. Existing tickets keep the price they were sold at."""
        if len({z.zone_id for z in zones}) != len(zones):
            raise AppValidationError("A zone can only be listed once")
        by_id = {z.id: z for z in self.fixtures.venue_zones(fixture.venue_id)}
        now = _now()
        for entry in sorted(zones, key=lambda z: z.zone_id):  # fixed order, so two editors cannot deadlock
            zone = by_id.get(entry.zone_id)
            if zone is None:
                raise AppValidationError("That zone does not belong to this venue")
            if entry.quota > zone.capacity:
                raise AppValidationError(f"{zone.name} holds {zone.capacity} seats at most")
            sale = self.fixtures.lock_zone(fixture.id, entry.zone_id)
            if sale is None:
                self.db.add(FixtureZone(fixture_id=fixture.id, zone_id=entry.zone_id, price_bani=entry.price_bani, quota=entry.quota))
                continue
            taken = self.tickets.taken(fixture.id, entry.zone_id, now)
            if entry.quota < taken:
                raise ConflictError(f"{zone.name}: {taken} seats are already sold or held")
            sale.price_bani, sale.quota = entry.price_bani, entry.quota
        self.db.flush()

    def create_fixture(self, user: User, payload: FixtureCreate) -> FixtureDetail:
        home = self._home_club(user)
        away = self.clubs.get_by_slug(payload.away_club)
        if away is None:
            raise NotFoundError("Away club not found")
        if away.id == home.id:
            raise AppValidationError("A club cannot play itself")
        if payload.kickoff_at <= _now():
            raise AppValidationError("Kickoff must be in the future")
        fixture = self.fixtures.add(Fixture(
            home_club_id=home.id, away_club_id=away.id, venue_id=home.venue_id, kickoff_at=payload.kickoff_at,
        ))
        self._apply_zones(fixture, payload.zones)
        self.db.commit()
        log_activity("fixture_created", user_id=user.id, fixture_id=fixture.id)
        return self._detail(fixture)

    def update_fixture(self, user: User, fixture_id: int, payload: FixtureUpdate) -> FixtureDetail:
        fixture = self.fixtures.get(fixture_id)
        if fixture is None:
            raise NotFoundError("Fixture not found")
        ensure_club_staff(user, fixture.home_club_id)
        if payload.kickoff_at is not None:
            if payload.kickoff_at <= _now():
                raise AppValidationError("Kickoff must be in the future")
            fixture.kickoff_at = payload.kickoff_at
        if payload.status is not None:
            if payload.status == FixtureStatus.CANCELLED and self.tickets.has_sold(fixture.id, _now()):
                raise ConflictError("Tickets are sold or held for this match, so it cannot be cancelled here")
            fixture.status = payload.status
        if payload.zones:
            self._apply_zones(fixture, payload.zones)
        self.db.commit()
        log_activity("fixture_updated", user_id=user.id, fixture_id=fixture.id)
        return self._detail(fixture)

    def scan(self, user: User, code: str) -> ScanOut:
        """Validate a ticket at the door and mark it used, once."""
        ticket = self.tickets.get_by_code(code, lock=True)  # the lock makes two simultaneous scans of one code take turns
        if ticket is None:
            log_activity("scan_rejected", user_id=user.id, reason="unknown")
            raise NotFoundError("Unknown ticket")
        fixture = self.fixtures.get(ticket.fixture_id)
        ensure_club_staff(user, fixture.home_club_id)
        if ticket.status == TicketStatus.USED:
            log_activity("scan_rejected", user_id=user.id, ticket_id=ticket.id, reason="already_used")
            raise ConflictError(f"Already used at {ticket.used_at:%Y-%m-%d %H:%M} UTC")
        if ticket.status != TicketStatus.VALID:
            log_activity("scan_rejected", user_id=user.id, ticket_id=ticket.id, reason=ticket.status)
            raise ConflictError("This ticket is not valid")
        ticket.status, ticket.used_at, ticket.scanned_by = TicketStatus.USED, _now(), user.id
        self.db.commit()
        log_activity("scan_ok", user_id=user.id, ticket_id=ticket.id)
        zone = self.db.get(Zone, ticket.zone_id)
        return ScanOut(zone=zone.name, fixture=FixtureOut.model_validate(fixture), used_at=ticket.used_at)
