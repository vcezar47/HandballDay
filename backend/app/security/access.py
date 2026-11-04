"""Who is asking (authentication) and what they may touch (authorization). The server is the real check."""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..activity import log_activity
from ..db import get_db
from ..errors import AuthError, ForbiddenError
from ..models import User
from ..repositories import UserRepository

SESSION_KEY = "user_id"


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get(SESSION_KEY)
    user = UserRepository(db).get(user_id) if isinstance(user_id, int) else None
    if not user:
        raise AuthError("Please log in")
    return user


def require_role(*roles: str):
    """Dependency factory: `Depends(require_role("staff", "admin"))`."""

    def dependency(request: Request, user: User = Depends(current_user)) -> User:
        if user.role.name not in roles:
            log_activity("forbidden", user_id=user.id, role=user.role.name, path=request.url.path)
            raise ForbiddenError("You do not have access to this")
        return user

    return dependency


def ensure_owner(user: User, owner_id: int) -> None:
    """For tickets, orders and designs: only the owner, or an admin."""
    if user.id != owner_id and user.role.name != "admin":
        raise ForbiddenError("You do not have access to this")


def ensure_club_staff(user: User, club_id: int) -> None:
    """Staff manage only their own club; admins manage any."""
    if user.role.name == "admin":
        return
    if user.role.name != "staff" or user.club_id != club_id:
        raise ForbiddenError("You do not have access to this club")
