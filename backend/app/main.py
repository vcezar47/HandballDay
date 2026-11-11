from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .config import get_config
from .db import ensure_database, get_engine
from .errors import AppError, app_error_handler
from .limits import limiter, rate_limit_handler
from .models import Base
from .routers import admin, auth, catalog, csrf, health, jersey, orders, seo, staff
from .security.csrf import CSRFMiddleware
from .security.headers import SecurityHeadersMiddleware
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
    docs = None if cfg.name == "prod" else "/docs"  # no public API explorer in production
    app = FastAPI(title="HandballDay API", lifespan=lifespan, docs_url=docs, redoc_url=None, openapi_url=None if docs is None else "/openapi.json")
    app.state.limiter = limiter
    # Last added runs first: CORS, then CSRF check, then the session cookie is read.
    # shortcut: the session is a signed cookie, so it cannot be revoked server-side before it expires; move to a sessions table if that is needed.
    app.add_middleware(
        SessionMiddleware, secret_key=cfg.secret_key, session_cookie="hd_session",
        max_age=cfg.session_max_age, same_site="lax", https_only=cfg.secure_cookies,
    )
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(SlowAPIMiddleware)  # outside CSRF, so rejected requests count against the limit too
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)  # added last = outermost: covers every response, errors included
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.include_router(health.router)
    app.include_router(csrf.router)
    app.include_router(auth.router)
    app.include_router(catalog.router)
    app.include_router(orders.router)
    app.include_router(jersey.router)
    app.include_router(staff.router)
    app.include_router(admin.router)
    app.include_router(seo.router)
    return app


app = create_app()
