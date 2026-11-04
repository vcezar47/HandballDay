from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin, IdMixin


class Role(IdMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(20), unique=True)  # fan / staff / admin


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"))  # staff only

    role: Mapped[Role] = relationship(lazy="joined")
