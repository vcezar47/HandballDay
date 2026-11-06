from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin


class League(IdMixin, Base):
    __tablename__ = "leagues"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    country: Mapped[str] = mapped_column(String(60))


class Venue(IdMixin, Base):
    __tablename__ = "venues"

    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(String(200))


class Club(IdMixin, Base):
    __tablename__ = "clubs"

    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    city: Mapped[str] = mapped_column(String(80))
    founded_year: Mapped[int]
    description: Mapped[str] = mapped_column(Text)
    primary_color: Mapped[str] = mapped_column(String(7))  # "#rrggbb"
    secondary_color: Mapped[str] = mapped_column(String(7))

    venue: Mapped[Venue] = relationship(lazy="joined")


class Zone(IdMixin, Base):
    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("venue_id", "name"),)

    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    name: Mapped[str] = mapped_column(String(60))
    capacity: Mapped[int]
