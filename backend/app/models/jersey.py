from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, IdMixin


class JerseyTemplate(IdMixin, Base):
    __tablename__ = "jersey_templates"

    name: Mapped[str] = mapped_column(String(60), unique=True)
    svg_key: Mapped[str] = mapped_column(String(60))


class Upload(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "uploads"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stored_name: Mapped[str] = mapped_column(String(80), unique=True)
    mime: Mapped[str] = mapped_column(String(40))
    size_bytes: Mapped[int]


class JerseyDesign(IdMixin, Base):
    __tablename__ = "jersey_designs"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    template_id: Mapped[int] = mapped_column(ForeignKey("jersey_templates.id"))
    primary_color: Mapped[str] = mapped_column(String(7))
    secondary_color: Mapped[str] = mapped_column(String(7))
    name_text: Mapped[str] = mapped_column(String(20))
    number: Mapped[int]
    logo_upload_id: Mapped[int | None] = mapped_column(ForeignKey("uploads.id"))


class JerseyItem(IdMixin, Base):
    __tablename__ = "jersey_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("jersey_designs.id"))
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"))  # pickup match
    size: Mapped[str] = mapped_column(String(4))
    price_bani: Mapped[int]  # snapshot
