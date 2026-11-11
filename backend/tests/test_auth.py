from sqlalchemy import select

from app.models import User

NEW = {"email": "Ana@Example.com", "display_name": "Ana", "password": "correct horse"}


def register(client, **overrides):
    return client.post("/api/auth/register", json={**NEW, **overrides})


def login(client, email="ana@example.com", password=NEW["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_hashes_password_and_logs_the_user_in(client, db):
    res = register(client)
    assert res.status_code == 201
    assert res.json()["user"]["email"] == "ana@example.com"
    assert res.json()["user"]["role"] == "fan"
    stored = db.scalar(select(User)).password_hash
    assert stored != NEW["password"] and stored.startswith("$argon2")
    assert client.get("/api/auth/me").json()["email"] == "ana@example.com"


def test_session_cookie_is_httponly_and_samesite(client):
    header = register(client).headers["set-cookie"].lower()
    assert "hd_session=" in header and "httponly" in header and "samesite=lax" in header


def test_duplicate_email_is_a_conflict_whatever_the_case(client):
    register(client)
    res = register(client, email="ANA@example.com")
    assert res.status_code == 409
    assert res.json()["code"] == "conflict"


def test_login_ok(client):
    register(client)
    client.post("/api/auth/logout")
    res = login(client)
    assert res.status_code == 200
    assert client.get("/api/auth/me").json()["display_name"] == "Ana"


def test_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    wrong = login(client, password="nope")
    unknown = login(client, email="who@example.com", password="nope")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_failed_login_does_not_start_a_session(client):
    register(client)
    client.post("/api/auth/logout")
    login(client, password="nope")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_ends_the_session(client):
    register(client)
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_guest_gets_401_on_me(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.json()["code"] == "unauthenticated"


def test_register_rejects_short_password_and_bad_email(client):
    assert register(client, password="short").status_code == 422
    assert register(client, email="not-an-email").status_code == 422


def test_sql_injection_in_login_is_just_a_wrong_password(client):
    register(client)
    assert login(client, password="' OR 1=1 --").status_code == 401
    assert login(client, email="' OR 1=1 --").status_code == 422  # not an email at all


def test_sql_injection_in_text_field_is_stored_as_plain_text(client, db):
    assert register(client, display_name="Robert'); DROP TABLE users;--").status_code == 422  # punctuation is refused outright
    name = "O'Brien' OR 'a'-'a"  # SQL-shaped but within the allowed characters: it must still be only data
    register(client, display_name=name)
    assert client.get("/api/auth/me").json()["display_name"] == name  # table still there, value untouched
    assert db.scalar(select(User.display_name)) == name
