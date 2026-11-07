from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from ..errors import NotFoundError
from ..models import Club, Fixture
from ..repositories import ClubRepository, FixtureRepository
from ..schemas import ClubOut, FixtureDetail, ZoneOut


def _day_start(d: date) -> datetime:
    return datetime.combine(d, time.min, timezone.utc)


class CatalogService:
    """Read-only public browsing: clubs and fixtures."""

    def __init__(self, db: Session) -> None:
        self.clubs = ClubRepository(db)
        self.fixtures = FixtureRepository(db)

    def list_clubs(self) -> list[Club]:
        return self.clubs.list()

    def get_club_row(self, slug: str) -> Club:
        club = self.clubs.get_by_slug(slug)
        if club is None:
            raise NotFoundError("Club not found")
        return club

    def get_club(self, slug: str) -> ClubOut:
        club = self.get_club_row(slug)
        return ClubOut.model_validate(club).model_copy(update={"capacity": self.clubs.capacity(club)})

    def list_fixtures(
        self, club_slug: str | None = None, date_from: date | None = None, date_to: date | None = None,
        limit: int = 50,
    ) -> list[Fixture]:
        club_id = None
        if club_slug is not None:
            club_id = self.get_club_row(club_slug).id
        return self.fixtures.upcoming(
            datetime.now(timezone.utc), club_id=club_id,
            start=_day_start(date_from) if date_from else None,
            end=_day_start(date_to + timedelta(days=1)) if date_to else None,  # date_to is inclusive
            limit=limit,
        )

    def get_fixture(self, fixture_id: int) -> FixtureDetail:
        fixture = self.fixtures.get(fixture_id)
        if fixture is None:
            raise NotFoundError("Fixture not found")
        return FixtureDetail.model_validate(fixture).model_copy(update={"zones": [ZoneOut(**z) for z in self.fixtures.zones(fixture_id, datetime.now(timezone.utc))]})
