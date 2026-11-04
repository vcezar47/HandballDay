from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import AuthResponse, Login, Register
from ..services import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: Register, db: Session = Depends(get_db)):
    user = AuthService(db).register(payload.email, payload.display_name, payload.password)
    return {"message": "Account created", "user": user}


@router.post("/login", response_model=AuthResponse)
def login(payload: Login, db: Session = Depends(get_db)):
    user = AuthService(db).authenticate(payload.email, payload.password)
    return {"message": "Logged in", "user": user}
