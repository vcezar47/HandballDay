from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # Stored exactly as received (plain text) - lab requirement, see security.py.
    password: Mapped[str] = mapped_column(String(100))
