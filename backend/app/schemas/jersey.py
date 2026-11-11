from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .catalog import ClubSummary, FixtureOut

SIZES = ("XS", "S", "M", "L", "XL", "XXL")
NAME_MAX = 15
HEX_COLOUR = r"^#[0-9a-fA-F]{6}$"


class JerseyRequest(BaseModel):
    """A jersey added to a ticket purchase. Everything printed on it is validated here, once."""

    club: str = Field(max_length=100, description="club slug")
    template_id: int
    primary_color: str = Field(pattern=HEX_COLOUR)
    secondary_color: str = Field(pattern=HEX_COLOUR)
    name_text: str = Field(min_length=1, max_length=NAME_MAX)
    number: int = Field(ge=0, le=99)
    size: Literal["XS", "S", "M", "L", "XL", "XXL"]
    logo_upload_id: int | None = None

    @field_validator("name_text")
    @classmethod
    def safe_name(cls, value: str) -> str:
        # Letters (any alphabet, so Romanian diacritics work), space, dot, hyphen, apostrophe: nothing that means markup.
        value = " ".join(value.upper().split())
        if not value or len(value) > NAME_MAX or not all(c.isalpha() or c in " .'-" for c in value):
            raise ValueError("Use letters, spaces, dots, hyphens and apostrophes only")
        return value


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    svg_key: str


class TemplatesOut(BaseModel):
    price_bani: int
    sizes: list[str]
    templates: list[TemplateOut]


class JerseyOut(BaseModel):
    id: int
    size: str
    price_bani: int
    club: ClubSummary
    template: str
    primary_color: str
    secondary_color: str
    name_text: str
    number: int
    logo_upload_id: int | None
    pickup: FixtureOut


class UploadOut(BaseModel):
    id: int
    size_bytes: int
