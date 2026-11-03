from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import config, models, schemas
from .db import Base, engine, ensure_database, get_db
from .security import prepare_password, verify_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_database()
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="DAW Project API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post(
    "/api/signup",
    response_model=schemas.AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(payload: schemas.Credentials, db: Session = Depends(get_db)):
    taken = db.scalar(select(models.User).where(models.User.username == payload.username))
    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken")

    user = models.User(
        username=payload.username,
        password=prepare_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two requests raced for the same username
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken")
    db.refresh(user)
    return {"message": "Account created", "user": user}


@app.post("/api/login", response_model=schemas.AuthResponse)
def login(payload: schemas.Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.username == payload.username))
    # Same error for unknown user and wrong password.
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return {"message": "Logged in", "user": user}
