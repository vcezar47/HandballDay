from sqlalchemy import select

from ..models import Club, Role, User
from .base import SqlRepository


class UserRepository(SqlRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def list_with_club(self) -> list[tuple[User, str | None]]:
        """Every user with the slug of the club they work for (staff only)."""
        q = select(User, Club.slug).outerjoin(Club, Club.id == User.club_id).order_by(User.id)
        return [tuple(row) for row in self.db.execute(q)]


class RoleRepository(SqlRepository[Role]):
    model = Role

    def get_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))
