from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .config import get_config
from .db import ensure_database, get_engine
from .errors import AppError, app_error_handler
from .models import Base
from .routers import auth, catalog, csrf, health, jersey, orders, seo, staff
from .security.csrf import CSRFMiddleware
from .seed import ensure_roles


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_database()
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as db:
        ensure_roles(db)
    yield


def create_app() -> FastAPI:
    cfg = get_config()
    app = FastAPI(title="HandballDay API", lifespan=lifespan)
    # Last added runs first: CORS, then CSRF check, then the session cookie is read.
    # shortcut: the session is a signed cookie, so it cannot be revoked server-side before it expires; move to a sessions table if that is needed.
    app.add_middleware(
        SessionMiddleware, secret_key=cfg.secret_key, session_cookie="hd_session",
        max_age=cfg.session_max_age, same_site="lax", https_only=cfg.secure_cookies,
    )
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(health.router)
    app.include_router(csrf.router)
    app.include_router(auth.router)
    app.include_router(catalog.router)
    app.include_router(orders.router)
    app.include_router(jersey.router)
    app.include_router(staff.router)
    app.include_router(seo.router)
    return app


app = create_app()
