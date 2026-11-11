from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy import select

from app.config import get_config
from app.models import Club, JerseyDesign, JerseyTemplate, Upload
from app.seed import seed_all

from .conftest import log_in


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(get_config(), "upload_dir", tmp_path)
    return tmp_path


@pytest.fixture
def admin(client, db, make_user):
    seed_all(db)
    user = make_user("admin@example.com", role="admin")
    log_in(client, "admin@example.com")
    return user


ENDPOINTS = [
    ("get", "/api/admin/users", None), ("patch", "/api/admin/users/1", {"role": "fan"}),
    ("patch", "/api/admin/clubs/minaur-baia-mare", {}), ("get", "/api/admin/uploads", None),
    ("delete", "/api/admin/uploads/1", None), ("get", "/api/admin/activity", None),
]


def call(client, method, path, body):
    return getattr(client, method)(path, **({"json": body} if body is not None else {}))


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
def test_only_admins_get_in(client, db, make_user, method, path, body):
    seed_all(db)
    assert call(client, method, path, body).status_code == 401
    make_user("fan@example.com")
    make_user("staff@example.com", role="staff", club_id=db.scalar(select(Club.id)))
    for who in ("fan@example.com", "staff@example.com"):
        log_in(client, who)
        res = call(client, method, path, body)
        assert res.status_code == 403 and res.json()["code"] == "forbidden"


def test_users_are_listed_with_role_and_club(client, admin, make_user, db):
    club = db.scalars(select(Club)).first()
    make_user("staff@example.com", role="staff", club_id=club.id)
    rows = {u["email"]: u for u in client.get("/api/admin/users").json()}
    assert rows["admin@example.com"]["role"] == "admin" and rows["admin@example.com"]["club"] is None
    assert rows["staff@example.com"]["role"] == "staff" and rows["staff@example.com"]["club"] == club.slug
    assert "password_hash" not in rows["staff@example.com"]


def test_admin_can_make_staff_and_the_new_role_works(client, admin, make_user, db):
    fan = make_user("fan@example.com")
    slug = db.scalars(select(Club.slug)).first()
    res = client.patch(f"/api/admin/users/{fan.id}", json={"role": "staff", "club": slug})
    assert res.status_code == 200 and res.json()["role"] == "staff" and res.json()["club"] == slug
    log_in(client, "fan@example.com")
    assert client.get("/api/staff/fixtures").status_code == 200  # the role change is real, not just displayed
    log_in(client, "admin@example.com")
    back = client.patch(f"/api/admin/users/{fan.id}", json={"role": "fan", "club": slug})
    assert back.json()["role"] == "fan" and back.json()["club"] is None  # only staff belong to a club


def test_role_change_rules(client, admin, make_user, activity):
    fan = make_user("fan@example.com")
    assert client.patch(f"/api/admin/users/{fan.id}", json={"role": "staff"}).status_code == 422  # staff need a club
    assert client.patch(f"/api/admin/users/{fan.id}", json={"role": "staff", "club": "nope"}).status_code == 422
    assert client.patch(f"/api/admin/users/{fan.id}", json={"role": "owner"}).status_code == 422
    assert client.patch("/api/admin/users/999999", json={"role": "fan"}).status_code == 404
    mine = client.patch(f"/api/admin/users/{admin.id}", json={"role": "fan"})
    assert mine.status_code == 409  # an admin cannot demote themself
    assert client.patch(f"/api/admin/users/{fan.id}", json={"role": "admin"}).status_code == 200
    assert activity.lines[-1][0] == "role_changed" and activity.lines[-1][1]["user_id"] == fan.id


def test_admin_edits_club_details(client, admin):
    res = client.patch("/api/admin/clubs/minaur-baia-mare", json={"description": "New text", "primary_color": "#AABBCC", "founded_year": 1999})
    assert res.status_code == 200
    public = client.get("/api/clubs/minaur-baia-mare").json()
    assert public["description"] == "New text" and public["primary_color"] == "#aabbcc" and public["founded_year"] == 1999
    assert public["secondary_color"] == "#ffffff"  # untouched
    assert client.patch("/api/admin/clubs/minaur-baia-mare", json={}).status_code == 200  # nothing to change is fine
    assert client.patch("/api/admin/clubs/nope", json={"description": "x"}).status_code == 404
    for bad in ({"primary_color": "red"}, {"description": ""}, {"founded_year": 3000}, {"description": "x" * 2001}):
        assert client.patch("/api/admin/clubs/minaur-baia-mare", json=bad).status_code == 422


def make_upload(client, email):
    log_in(client, email)
    out = BytesIO()
    Image.new("RGB", (30, 30), (10, 200, 10)).save(out, "PNG")
    return client.post("/api/uploads", content=out.getvalue(), headers={"X-Filename": "l.png"}).json()["id"]


def test_admin_moderates_uploads(client, admin, make_user, db, upload_dir):
    fan = make_user("fan@example.com")
    upload_id = make_upload(client, "fan@example.com")
    design = JerseyDesign(
        user_id=fan.id, club_id=db.scalar(select(Club.id)), template_id=db.scalar(select(JerseyTemplate.id)), primary_color="#000000",
        secondary_color="#ffffff", name_text="X", number=1, logo_upload_id=upload_id,
    )
    db.add(design)
    db.commit()

    log_in(client, "admin@example.com")
    (row,) = client.get("/api/admin/uploads").json()
    assert row["id"] == upload_id and row["owner_email"] == "fan@example.com" and row["in_use"] is True
    assert client.get(f"/api/uploads/{upload_id}").status_code == 200  # an admin may look at what they moderate
    assert len(list(upload_dir.iterdir())) == 1

    assert client.delete(f"/api/admin/uploads/{upload_id}").status_code == 204
    assert list(upload_dir.iterdir()) == [] and db.scalar(select(Upload.id)) is None
    db.refresh(design)
    assert design.logo_upload_id is None  # the jersey stays, without its logo
    assert client.get(f"/api/uploads/{upload_id}").status_code == 404
    assert client.delete(f"/api/admin/uploads/{upload_id}").status_code == 404


def test_activity_log_viewer(client, admin, make_user):
    fan = make_user("fan@example.com")
    client.patch(f"/api/admin/users/{fan.id}", json={"role": "admin"})
    log_in(client, "admin@example.com")
    entries = client.get("/api/admin/activity?limit=20").json()
    assert entries and {"time", "event", "fields"} <= entries[0].keys()
    assert [e["time"] for e in entries] == sorted((e["time"] for e in entries), reverse=True)  # newest first
    changes = client.get("/api/admin/activity?event=role_changed&limit=500").json()
    assert changes and {e["event"] for e in changes} == {"role_changed"}
    assert any(e["fields"].get("user_id") == fan.id for e in changes)
    assert client.get("/api/admin/activity?limit=0").status_code == 422
    assert client.get("/api/admin/activity?limit=501").status_code == 422
    assert client.get("/api/admin/activity?event=no_such_event").json() == []

