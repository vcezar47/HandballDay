from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from ..models import FixtureStatus
from .catalog import FixtureOut
from .jersey import JerseyRequest

MAX_TICKETS_PER_ORDER = 6


class CheckoutRequest(BaseModel):
    fixture_id: int
    zone_id: int
    quantity: int | None = Field(None, ge=1, le=MAX_TICKETS_PER_ORDER)  # implied by `seats` when seats are chosen
    seats: list[str] | None = Field(None, min_length=1, max_length=MAX_TICKETS_PER_ORDER)  # seat codes, all in `zone_id`
    jersey: JerseyRequest | None = None  # one optional jersey, picked up at this match

    @model_validator(mode="after")
    def _count(self):
        if self.seats is not None:
            if len(set(self.seats)) != len(self.seats):
                raise ValueError("A seat can only be listed once")
            if self.quantity not in (None, len(self.seats)):
                raise ValueError("quantity does not match the seats")
            self.quantity = len(self.seats)
        elif self.quantity is None:
            raise ValueError("Choose seats or a quantity")
        return self


class CheckoutResponse(BaseModel):
    checkout_url: str


class TicketOut(BaseModel):
    id: int
    code: str
    status: str
    price_bani: int
    zone: str
    seat: str | None = None
    fixture: FixtureOut
    used_at: datetime | None = None


class ScanRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class ScanOut(BaseModel):
    zone: str
    seat: str | None = None
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
