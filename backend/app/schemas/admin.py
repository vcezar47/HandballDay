from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .jersey import HEX_COLOUR


class AdminUserOut(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    club: str | None  # club slug, staff only
    created_at: datetime


class AdminUserUpdate(BaseModel):
    role: Literal["fan", "staff", "admin"]
    club: str | None = Field(None, max_length=100, description="club slug; required for staff, ignored otherwise")


class ClubUpdate(BaseModel):
    """What an admin may edit. Name and slug stay fixed: the slug is in every public URL."""

    description: str | None = Field(None, min_length=1, max_length=2000)
    primary_color: str | None = Field(None, pattern=HEX_COLOUR)
    secondary_color: str | None = Field(None, pattern=HEX_COLOUR)
    founded_year: int | None = Field(None, ge=1800, le=2100)


class AdminUploadOut(BaseModel):
    id: int
    owner_email: str
    size_bytes: int
    created_at: datetime
    in_use: bool


class ActivityEntry(BaseModel):
    time: str
    event: str
    fields: dict
