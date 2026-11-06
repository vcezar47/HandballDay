import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin
from .club import Club, Venue


class FixtureStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Fixture(IdMixin, Base):
    __tablename__ = "fixtures"
    __table_args__ = (CheckConstraint("home_club_id <> away_club_id"),)

    home_club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    away_club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[FixtureStatus] = mapped_column(
        Enum(FixtureStatus, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=FixtureStatus.SCHEDULED,
    )

    # Eager: every fixture view shows both clubs and the venue, so avoid one query per row.
    home_club: Mapped[Club] = relationship(foreign_keys=[home_club_id], lazy="joined")
    away_club: Mapped[Club] = relationship(foreign_keys=[away_club_id], lazy="joined")
    venue: Mapped[Venue] = relationship(lazy="joined")


class FixtureZone(Base):
    """A zone put on sale for one fixture, with its price and quota."""

    __tablename__ = "fixture_zones"
    __table_args__ = (CheckConstraint("price_bani >= 0 AND quota >= 0"),)

    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), primary_key=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), primary_key=True)
    price_bani: Mapped[int]
    quota: Mapped[int]
