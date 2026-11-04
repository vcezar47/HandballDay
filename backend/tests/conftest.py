import os

# Before any app import: tests must never touch the dev database.
os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import ensure_database, get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.seed import ensure_roles  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    """handballday_test is created if missing, then rebuilt from the models on every run."""
    ensure_database()
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        ensure_roles(db)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """A session whose work, commits included, is rolled back after each test."""
    conn = engine.connect()
    outer = conn.begin()
    session = Session(conn, join_transaction_mode="create_savepoint", autoflush=False)
    yield session
    session.close()
    outer.rollback()
    conn.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
