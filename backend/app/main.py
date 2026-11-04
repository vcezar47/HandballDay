from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import get_config
from .db import ensure_database, get_engine
from .errors import AppError, app_error_handler
from .models import Base
from .routers import auth, health
from .seed import ensure_roles


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_database()
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as db:
        ensure_roles(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="HandballDay API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_config().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(health.router)
    app.include_router(auth.router)
    return app


app = create_app()
