import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, IdMixin


def _enum(cls: type[enum.StrEnum]) -> Enum:
    return Enum(cls, native_enum=False, values_callable=lambda e: [m.value for m in e])


class OrderStatus(enum.StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TicketStatus(enum.StrEnum):
    PENDING = "pending"  # seat held while the order waits for payment
    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"


class Order(IdMixin, CreatedAtMixin, Base):
    """No stored total: it is the sum of its ticket and jersey line prices."""

    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(_enum(OrderStatus), default=OrderStatus.PENDING)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Payment(IdMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    provider_ref: Mapped[str] = mapped_column(String(255), unique=True)  # Stripe session id
    amount_bani: Mapped[int]
    status: Mapped[PaymentStatus] = mapped_column(_enum(PaymentStatus), default=PaymentStatus.PENDING)


class Ticket(IdMixin, Base):
    __tablename__ = "tickets"
    # The zone must really be on sale for that fixture.
    __table_args__ = (
        ForeignKeyConstraint(
            ["fixture_id", "zone_id"], ["fixture_zones.fixture_id", "fixture_zones.zone_id"]
        ),
    )

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    fixture_id: Mapped[int] = mapped_column(index=True)
    zone_id: Mapped[int]
    code: Mapped[str] = mapped_column(String(64), unique=True)  # random token, rendered as QR
    price_bani: Mapped[int]  # snapshot: must not change when the fixture is repriced
    status: Mapped[TicketStatus] = mapped_column(_enum(TicketStatus), default=TicketStatus.VALID)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scanned_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
