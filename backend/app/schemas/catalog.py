from datetime import datetime

from pydantic import AliasPath, BaseModel, ConfigDict, Field


class ClubSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    city: str
    primary_color: str
    secondary_color: str


class ClubOut(ClubSummary):
    founded_year: int
    description: str
    venue: str = Field(validation_alias=AliasPath("venue", "name"))
    capacity: int = 0  # filled by the service: it is a sum over the venue's zones


class ZoneOut(BaseModel):
    zone_id: int
    name: str
    price_bani: int
    quota: int
    seats_left: int


class FixtureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kickoff_at: datetime
    status: str
    home: ClubSummary = Field(validation_alias="home_club")
    away: ClubSummary = Field(validation_alias="away_club")
    venue: str = Field(validation_alias=AliasPath("venue", "name"))


class FixtureDetail(FixtureOut):
    zones: list[ZoneOut] = []
