from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field

from ..models import FixtureStatus
from .catalog import FixtureOut

MAX_TICKETS_PER_ORDER = 6


class CheckoutRequest(BaseModel):
    fixture_id: int
    zone_id: int
    quantity: int = Field(ge=1, le=MAX_TICKETS_PER_ORDER)


class CheckoutResponse(BaseModel):
    checkout_url: str


class TicketOut(BaseModel):
    id: int
    code: str
    status: str
    price_bani: int
    zone: str
    fixture: FixtureOut
    used_at: datetime | None = None


class ScanRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class ScanOut(BaseModel):
    zone: str
    fixture: FixtureOut
    used_at: datetime


class ZoneSaleIn(BaseModel):
    zone_id: int
    price_bani: int = Field(ge=0, le=1_000_000)
    quota: int = Field(ge=0, le=100_000)


class FixtureCreate(BaseModel):
    away_club: str = Field(max_length=100, description="club slug")
    kickoff_at: AwareDatetime
    zones: list[ZoneSaleIn] = Field(min_length=1, max_length=20)


class FixtureUpdate(BaseModel):
    kickoff_at: AwareDatetime | None = None
    status: FixtureStatus | None = None
    zones: list[ZoneSaleIn] | None = Field(None, max_length=20)


class VenueZoneOut(BaseModel):
    id: int
    name: str
    capacity: int
