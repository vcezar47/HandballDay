from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..activity import log_activity
from ..db import get_db
from ..errors import AuthError
from ..models import User
from ..schemas import AuthResponse, Login, Register, UserOut
from ..security.access import SESSION_KEY, current_user
from ..services import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _start_session(request: Request, user: User) -> None:
    request.session.clear()  # never keep anything from a previous session
    request.session[SESSION_KEY] = user.id


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: Register, request: Request, db: Session = Depends(get_db)):
    user = AuthService(db).register(payload.email, payload.display_name, payload.password)
    _start_session(request, user)
    log_activity("register", user_id=user.id, ip=_ip(request))
    return {"message": "Account created", "user": user}


@router.post("/login", response_model=AuthResponse)
def login(payload: Login, request: Request, db: Session = Depends(get_db)):
    try:
        user = AuthService(db).authenticate(payload.email, payload.password)
    except AuthError:
        log_activity("login_failed", email=payload.email, ip=_ip(request))
        raise
    _start_session(request, user)
    log_activity("login", user_id=user.id, ip=_ip(request))
    return {"message": "Logged in", "user": user}


@router.post("/logout")
def logout(request: Request):
    user_id = request.session.get(SESSION_KEY)
    request.session.clear()
    if user_id:
        log_activity("logout", user_id=user_id, ip=_ip(request))
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
