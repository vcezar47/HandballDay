from datetime import datetime

from sqlalchemy import func, select

from ..models import Club, Fixture, FixtureStatus, FixtureZone, Ticket, Zone
from .base import SqlRepository
from .order import taken_seats


class ClubRepository(SqlRepository[Club]):
    model = Club

    def get_by_slug(self, slug: str) -> Club | None:
        return self.db.scalar(select(Club).where(Club.slug == slug))

    def list(self) -> list[Club]:
        return list(self.db.scalars(select(Club).order_by(Club.name)))

    def capacity(self, club: Club) -> int:
        return self.db.scalar(select(func.coalesce(func.sum(Zone.capacity), 0)).where(Zone.venue_id == club.venue_id))


class FixtureRepository(SqlRepository[Fixture]):
    model = Fixture

    def upcoming(
        self, now: datetime, *, club_id: int | None = None, start: datetime | None = None,
        end: datetime | None = None, limit: int = 50,
    ) -> list[Fixture]:
        """Scheduled fixtures from `now` on, soonest first; `end` is exclusive."""
        q = select(Fixture).where(Fixture.status == FixtureStatus.SCHEDULED, Fixture.kickoff_at >= now)
        if club_id is not None:
            q = q.where((Fixture.home_club_id == club_id) | (Fixture.away_club_id == club_id))
        if start is not None:
            q = q.where(Fixture.kickoff_at >= start)
        if end is not None:
            q = q.where(Fixture.kickoff_at < end)
        return list(self.db.scalars(q.order_by(Fixture.kickoff_at, Fixture.id).limit(limit)))

    def zones(self, fixture_id: int, now: datetime) -> list[dict]:
        """Zones on sale for a fixture, dearest first, with the seats not yet taken."""
        sold = (
            select(func.count(Ticket.id))
            .where(Ticket.fixture_id == FixtureZone.fixture_id, Ticket.zone_id == FixtureZone.zone_id, taken_seats(now))
            .scalar_subquery()
        )
        rows = self.db.execute(
            select(FixtureZone.zone_id, Zone.name, FixtureZone.price_bani, FixtureZone.quota, sold.label("sold"))
            .join(Zone, Zone.id == FixtureZone.zone_id)
            .where(FixtureZone.fixture_id == fixture_id)
            .order_by(FixtureZone.price_bani.desc(), Zone.id)
        )
        return [
            {"zone_id": r.zone_id, "name": r.name, "price_bani": r.price_bani, "quota": r.quota,
             "seats_left": max(r.quota - r.sold, 0)}
            for r in rows
        ]

    def lock_zone(self, fixture_id: int, zone_id: int) -> FixtureZone | None:
        """The zone's sale row, locked until the transaction ends so only one buyer counts seats at a time."""
        q = select(FixtureZone).where(FixtureZone.fixture_id == fixture_id, FixtureZone.zone_id == zone_id)
        return self.db.scalar(q.with_for_update())

    def get_zone(self, fixture_id: int, zone_id: int) -> FixtureZone | None:
        return self.db.get(FixtureZone, (fixture_id, zone_id))

    def venue_zones(self, venue_id: int) -> list[Zone]:
        return list(self.db.scalars(select(Zone).where(Zone.venue_id == venue_id).order_by(Zone.id)))

    def for_home_club(self, club_id: int) -> list[Fixture]:
        """Every fixture a club hosts, past and cancelled included."""
        return list(self.db.scalars(select(Fixture).where(Fixture.home_club_id == club_id).order_by(Fixture.kickoff_at, Fixture.id)))
