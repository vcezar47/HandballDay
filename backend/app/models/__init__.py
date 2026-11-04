# Importing every model registers its table on Base.metadata.
from .base import Base
from .club import Club, League, Venue, Zone
from .fixture import Fixture, FixtureStatus, FixtureZone
from .jersey import JerseyDesign, JerseyItem, JerseyTemplate, Upload
from .order import Order, OrderStatus, Payment, PaymentStatus, Ticket, TicketStatus
from .user import Role, User

__all__ = [
    "Base", "Club", "Fixture", "FixtureStatus", "FixtureZone", "JerseyDesign", "JerseyItem",
    "JerseyTemplate", "League", "Order", "OrderStatus", "Payment", "PaymentStatus", "Role",
    "Ticket", "TicketStatus", "Upload", "User", "Venue", "Zone",
]
