import pytest
from fastapi import Depends
from sqlalchemy import select

from app.errors import ForbiddenError
from app.main import create_app
from app.models import Club, Role, User
from app.security.access import ensure_club_staff, ensure_owner, require_role
from app.seed import seed_clubs

from .conftest import PASSWORD, make_client


@pytest.fixture
def client(db):
    """The real app plus two throwaway routes, so role checks can be tested before the real staff pages exist."""
    app = create_app()

    @app.get("/t/staff")
    def staff_only(user: User = Depends(require_role("staff", "admin"))):
        return {"id": user.id}

    @app.get("/t/admin")
    def admin_only(user: User = Depends(require_role("admin"))):
        return {"id": user.id}

    yield make_client(app, db)


def log_in(client, email):
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_guest_gets_401_on_role_protected_routes(client):
    assert client.get("/t/staff").status_code == 401
    assert client.get("/t/admin").status_code == 401


def test_fan_gets_403_on_staff_routes(client, make_user, activity):
    fan = make_user("fan@example.com")
    log_in(client, "fan@example.com")
    res = client.get("/t/staff")
    assert res.status_code == 403 and res.json()["code"] == "forbidden"
    assert activity.lines[-1][0] == "forbidden" and activity.lines[-1][1]["user_id"] == fan.id


def test_staff_passes_staff_routes_but_not_admin_routes(client, make_user, db):
    seed_clubs(db)
    make_user("staff@example.com", role="staff", club_id=db.scalar(select(Club.id)))
    log_in(client, "staff@example.com")
    assert client.get("/t/staff").status_code == 200
    assert client.get("/t/admin").status_code == 403


def test_admin_passes_everything(client, make_user):
    make_user("admin@example.com", role="admin")
    log_in(client, "admin@example.com")
    assert client.get("/t/staff").status_code == 200
    assert client.get("/t/admin").status_code == 200


def user(role, id=1, club_id=None):
    return User(id=id, club_id=club_id, role=Role(name=role))


def test_owner_check():
    ensure_owner(user("fan", id=1), owner_id=1)
    ensure_owner(user("admin", id=9), owner_id=1)
    with pytest.raises(ForbiddenError):
        ensure_owner(user("fan", id=2), owner_id=1)


def test_staff_are_limited_to_their_own_club():
    ensure_club_staff(user("staff", club_id=5), club_id=5)
    ensure_club_staff(user("admin"), club_id=5)
    for outsider in (user("staff", club_id=6), user("fan")):
        with pytest.raises(ForbiddenError):
            ensure_club_staff(outsider, club_id=5)
