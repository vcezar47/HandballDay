from sqlalchemy import select

from app.models import User

NEW = {"email": "Ana@Example.com", "display_name": "Ana", "password": "correct horse"}


def register(client, **overrides):
    return client.post("/api/auth/register", json={**NEW, **overrides})


def test_register_hashes_password_and_makes_a_fan(client, db):
    res = register(client)
    assert res.status_code == 201
    assert res.json()["user"]["email"] == "ana@example.com"
    assert res.json()["user"]["role"] == "fan"
    stored = db.scalar(select(User)).password_hash
    assert stored != NEW["password"] and stored.startswith("$argon2")


def test_duplicate_email_is_a_conflict_whatever_the_case(client):
    register(client)
    res = register(client, email="ANA@example.com")
    assert res.status_code == 409
    assert res.json()["code"] == "conflict"


def test_login_ok(client):
    register(client)
    res = client.post("/api/auth/login", json={"email": "ana@example.com", "password": NEW["password"]})
    assert res.status_code == 200
    assert res.json()["user"]["display_name"] == "Ana"


def test_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    wrong = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "nope"})
    unknown = client.post("/api/auth/login", json={"email": "who@example.com", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_register_rejects_short_password_and_bad_email(client):
    assert register(client, password="short").status_code == 422
    assert register(client, email="not-an-email").status_code == 422


def test_sql_injection_input_is_just_a_wrong_password(client):
    register(client)
    res = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "' OR 1=1 --"})
    assert res.status_code == 401
