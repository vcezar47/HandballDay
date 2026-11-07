import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.gateways import FakeGateway
from app.models import Club, Fixture, Ticket, TicketStatus
from app.seed import seed_all

from .conftest import log_in


@pytest.fixture
def seeded(db):
    seed_all(db)


@pytest.fixture
def world(db, seeded, make_user):
    """Two clubs' staff, a fan, and the first fixture (hosted by `home`)."""
    fixture = db.scalars(select(Fixture).order_by(Fixture.kickoff_at, Fixture.id)).first()
    home = db.get(Club, fixture.home_club_id)
    rival = db.scalars(select(Club).where(Club.id != home.id)).first()
    make_user("staff@example.com", role="staff", club_id=home.id)
    make_user("rival@example.com", role="staff", club_id=rival.id)
    make_user("fan@example.com")
    return {"fixture": fixture.id, "home": home, "rival": rival}


def kickoff(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def zones_payload(client, price=5000, quota=10):
    zones = client.get("/api/staff/zones").json()
    return [{"zone_id": z["id"], "price_bani": price, "quota": min(quota, z["capacity"])} for z in zones]


def paid(client, gateway, fixture_id, buyer="fan@example.com", qty=1):
    """The fan buys and pays for the first zone; returns their issued tickets."""
    log_in(client, buyer)
    zone = client.get(f"/api/fixtures/{fixture_id}").json()["zones"][0]
    res = client.post("/api/checkout", json={"fixture_id": fixture_id, "zone_id": zone["zone_id"], "quantity": qty})
    assert res.status_code == 200
    body = json.dumps({"kind": "paid", "session_id": gateway.created[-1][0], "amount_bani": zone["price_bani"] * qty})
    client.post("/api/webhooks/stripe", content=body, headers={"stripe-signature": FakeGateway.SIGNATURE})
    return client.get("/api/tickets").json()


# ---- access ----

def test_guest_gets_401(client, world):
    assert client.get("/api/staff/fixtures").status_code == 401
    assert client.get("/api/staff/zones").status_code == 401
    assert client.post("/api/staff/scan", json={"code": "x"}).status_code == 401


def test_fan_gets_403(client, world):
    log_in(client, "fan@example.com")
    assert client.get("/api/staff/fixtures").status_code == 403
    assert client.get("/api/staff/zones").status_code == 403
    assert client.post("/api/staff/fixtures", json={}).status_code == 403


def test_staff_without_a_club_is_refused(client, seeded, make_user):
    make_user("lost@example.com", role="staff")
    log_in(client, "lost@example.com")
    assert client.get("/api/staff/fixtures").status_code == 403


# ---- managing fixtures ----

def test_staff_see_only_their_own_home_fixtures(client, world):
    log_in(client, "staff@example.com")
    fixtures = client.get("/api/staff/fixtures").json()
    assert len(fixtures) == 13
    assert all(f["home"]["slug"] == world["home"].slug for f in fixtures)


def test_staff_create_a_fixture(client, world):
    log_in(client, "staff@example.com")
    away = world["rival"].slug
    res = client.post("/api/staff/fixtures", json={"away_club": away, "kickoff_at": kickoff(), "zones": zones_payload(client)})
    assert res.status_code == 201
    created = res.json()
    assert created["home"]["slug"] == world["home"].slug and created["away"]["slug"] == away
    assert len(created["zones"]) == 3 and all(z["price_bani"] == 5000 for z in created["zones"])
    assert created["id"] in [f["id"] for f in client.get("/api/staff/fixtures").json()]
    assert created["id"] in [f["id"] for f in client.get("/api/fixtures?limit=200").json()]  # public too


def test_create_validation(client, world):
    log_in(client, "staff@example.com")
    zones = zones_payload(client)

    def create(**over):
        body = {"away_club": world["rival"].slug, "kickoff_at": kickoff(), "zones": zones, **over}
        return client.post("/api/staff/fixtures", json=body)

    assert create(away_club="nope").status_code == 404
    assert create(away_club=world["home"].slug).status_code == 422
    assert create(kickoff_at=kickoff(-1)).status_code == 422
    assert create(kickoff_at="2030-01-01T10:00:00").status_code == 422  # no timezone
    assert create(zones=[]).status_code == 422
    assert create(zones=[zones[0], zones[0]]).status_code == 422
    assert create(zones=[{**zones[0], "zone_id": 999999}]).status_code == 422
    assert create(zones=[{**zones[0], "quota": 10**6}]).status_code == 422
    assert create(zones=[{**zones[0], "price_bani": -1}]).status_code == 422


def test_repricing_never_changes_what_a_ticket_cost(client, world, gateway):
    tickets = paid(client, gateway, world["fixture"])
    sold_at = tickets[0]["price_bani"]
    log_in(client, "staff@example.com")
    zone_id = client.get(f"/api/fixtures/{world['fixture']}").json()["zones"][0]["zone_id"]
    res = client.patch(f"/api/staff/fixtures/{world['fixture']}", json={"zones": [{"zone_id": zone_id, "price_bani": sold_at + 1000, "quota": 50}]})
    assert res.status_code == 200
    changed = next(z for z in res.json()["zones"] if z["zone_id"] == zone_id)
    assert changed["price_bani"] == sold_at + 1000 and changed["quota"] == 50
    log_in(client, "fan@example.com")
    assert client.get("/api/tickets").json()[0]["price_bani"] == sold_at


def test_quota_cannot_drop_below_seats_already_sold(client, world, gateway):
    paid(client, gateway, world["fixture"], qty=3)
    log_in(client, "staff@example.com")
    zone = client.get(f"/api/fixtures/{world['fixture']}").json()["zones"][0]
    url = f"/api/staff/fixtures/{world['fixture']}"
    low = {"zone_id": zone["zone_id"], "price_bani": zone["price_bani"], "quota": 2}
    assert client.patch(url, json={"zones": [low]}).status_code == 409
    assert client.patch(url, json={"zones": [{**low, "quota": 3}]}).status_code == 200


def test_other_clubs_staff_and_fans_cannot_edit(client, world):
    url = f"/api/staff/fixtures/{world['fixture']}"
    log_in(client, "rival@example.com")
    assert client.patch(url, json={"status": "cancelled"}).status_code == 403
    log_in(client, "fan@example.com")
    assert client.patch(url, json={"status": "cancelled"}).status_code == 403
    assert client.patch("/api/staff/fixtures/999999", json={}).status_code in (403, 404)


def test_cancel_only_while_nothing_is_sold(client, world, gateway):
    url = f"/api/staff/fixtures/{world['fixture']}"
    paid(client, gateway, world["fixture"])
    log_in(client, "staff@example.com")
    assert client.patch(url, json={"status": "cancelled"}).status_code == 409
    other = client.get("/api/staff/fixtures").json()[1]["id"]
    assert client.patch(f"/api/staff/fixtures/{other}", json={"status": "cancelled"}).json()["status"] == "cancelled"
    assert other not in [f["id"] for f in client.get("/api/fixtures?limit=200").json()]  # off the public list


# ---- scanning ----

def scan(client, code):
    return client.post("/api/staff/scan", json={"code": code})


def test_a_ticket_scans_once(client, world, gateway, activity):
    code = paid(client, gateway, world["fixture"])[0]["code"]
    log_in(client, "staff@example.com")
    first = scan(client, code)
    assert first.status_code == 200 and first.json()["fixture"]["id"] == world["fixture"]
    second = scan(client, code)
    assert second.status_code == 409 and "Already used" in second.json()["detail"]
    assert [e for e, _ in activity.lines if e.startswith("scan")] == ["scan_ok", "scan_rejected"]
    log_in(client, "fan@example.com")
    ticket = client.get("/api/tickets").json()[0]
    assert ticket["status"] == "used" and ticket["used_at"]


def test_scan_rejects_unknown_foreign_and_unpaid_tickets(client, world, gateway, db):
    log_in(client, "fan@example.com")
    detail = client.get(f"/api/fixtures/{world['fixture']}").json()
    client.post("/api/checkout", json={"fixture_id": world["fixture"], "zone_id": detail["zones"][0]["zone_id"], "quantity": 1})
    pending_code = db.scalar(select(Ticket.code).where(Ticket.status == TicketStatus.PENDING))
    code = paid(client, gateway, world["fixture"])[0]["code"]

    log_in(client, "staff@example.com")
    assert scan(client, "no-such-code").status_code == 404
    assert scan(client, pending_code).status_code == 409  # not paid yet
    log_in(client, "rival@example.com")
    assert scan(client, code).status_code == 403  # another club's match
    log_in(client, "fan@example.com")
    assert scan(client, code).status_code == 403
    assert db.scalar(select(Ticket.status).where(Ticket.code == code)) == TicketStatus.VALID  # untouched
