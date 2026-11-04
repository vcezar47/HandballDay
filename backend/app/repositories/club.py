from sqlalchemy import select

from ..models import Club, Fixture
from .base import SqlRepository


class ClubRepository(SqlRepository[Club]):
    model = Club

    def get_by_slug(self, slug: str) -> Club | None:
        return self.db.scalar(select(Club).where(Club.slug == slug))


class FixtureRepository(SqlRepository[Fixture]):
    model = Fixture
