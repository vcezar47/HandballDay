from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from .config import get_config


def _url(database: str) -> URL:
    cfg = get_config()
    return URL.create(
        "postgresql+psycopg",
        username=cfg.db_user,
        password=cfg.db_password,
        host=cfg.db_host,
        port=cfg.db_port,
        database=database,
    )


@lru_cache
def get_engine() -> Engine:
    return create_engine(_url(get_config().db_name), pool_pre_ping=True)


@lru_cache
def _sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False)


def ensure_database() -> None:
    """Create the target database if it does not exist yet."""
    name = get_config().db_name
    admin = create_engine(_url("postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
            ).scalar()
            if not exists:
                quoted = name.replace('"', '""')
                conn.execute(text(f'CREATE DATABASE "{quoted}"'))
    finally:
        admin.dispose()


def get_db():
    db = _sessionmaker()()
    try:
        yield db
    finally:
        db.close()
