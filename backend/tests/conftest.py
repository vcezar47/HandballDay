import json
import logging
import os

# Before any app import: tests must never touch the dev database.
os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.activity import LOGGER_NAME, _logger  # noqa: E402
from app.db import ensure_database, get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User  # noqa: E402
from app.repositories import RoleRepository, UserRepository  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.seed import ensure_roles  # noqa: E402

PASSWORD = "correct horse"


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


def make_client(target_app, db, csrf=True) -> TestClient:
    """A client wired to the test session. With csrf=True it sends a valid X-CSRF-Token like the frontend."""
    target_app.dependency_overrides[get_db] = lambda: db
    client = TestClient(target_app)
    if csrf:
        client.headers["X-CSRF-Token"] = client.get("/api/csrf").json()["csrf_token"]
    return client


@pytest.fixture
def client(db):
    yield make_client(app, db)
    app.dependency_overrides.clear()


@pytest.fixture
def raw_client(db):
    """No CSRF token: for testing that the middleware refuses."""
    yield make_client(app, db, csrf=False)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def make(email="user@example.com", role="fan", club_id=None) -> User:
        role_row = RoleRepository(db).get_by_name(role)
        user = UserRepository(db).add(
            User(email=email, display_name="Test", password_hash=hash_password(PASSWORD), role_id=role_row.id, club_id=club_id)
        )
        db.commit()
        return user

    return make


@pytest.fixture
def activity():
    """Activity-log lines written during the test, as (event, fields) pairs."""

    class Capture(logging.Handler):
        def __init__(self):
            super().__init__()
            self.lines: list[tuple[str, dict]] = []

        def emit(self, record):
            event, _, payload = record.getMessage().partition(" ")
            self.lines.append((event, json.loads(payload)))

    _logger()  # make sure the real file handler exists before ours joins it
    handler = Capture()
    logging.getLogger(LOGGER_NAME).addHandler(handler)
    yield handler
    logging.getLogger(LOGGER_NAME).removeHandler(handler)
