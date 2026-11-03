from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from . import config


def _url(database: str) -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=database,
    )


engine = create_engine(_url(config.DB_NAME), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def ensure_database() -> None:
    """Create the target database if it does not exist yet."""
    admin = create_engine(_url("postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": config.DB_NAME},
            ).scalar()
            if not exists:
                quoted = config.DB_NAME.replace('"', '""')
                conn.execute(text(f'CREATE DATABASE "{quoted}"'))
    finally:
        admin.dispose()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
