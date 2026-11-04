from sqlalchemy import select

from ..models import Role, User
from .base import SqlRepository


class UserRepository(SqlRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))


class RoleRepository(SqlRepository[Role]):
    model = Role

    def get_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))
