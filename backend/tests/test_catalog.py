from datetime import date, timedelta

import pytest

from app.models import Fixture, Order, Ticket, TicketStatus
from app.seed import ZONES, seed_all


@pytest.fixture
def seeded(db):
    seed_all(db)


def test_clubs_are_listed_by_name(client, seeded):
    clubs = client.get("/api/clubs").json()
    assert len(clubs) == 14
    assert [c["name"] for c in clubs] == sorted(c["name"] for c in clubs)
    assert {"name", "slug", "city", "primary_color", "secondary_color"} <= clubs[0].keys()


def test_club_detail_has_venue_and_capacity(client, seeded):
    club = client.get("/api/clubs/minaur-baia-mare").json()
    assert club["venue"] and club["founded_year"] == 2015
    assert club["capacity"] == 2218  # sum of the three zones


@pytest.mark.parametrize("slug", ["nope", "' OR 1=1 --"])
def test_unknown_club_is_404(client, seeded, slug):
    r = client.get(f"/api/clubs/{slug}")
    assert r.status_code == 404 and r.json()["code"] == "not_found"


def test_fixtures_are_upcoming_and_sorted(client, seeded):
    fixtures = client.get("/api/fixtures?limit=200").json()
    assert len(fixtures) == 182
    kickoffs = [f["kickoff_at"] for f in fixtures]
    assert kickoffs == sorted(kickoffs)
    first = fixtures[0]
    assert first["home"]["slug"] != first["away"]["slug"] and first["venue"]


def test_fixtures_limit(client, seeded):
    assert len(client.get("/api/fixtures?limit=5").json()) == 5
    assert client.get("/api/fixtures?limit=0").status_code == 422
    assert client.get("/api/fixtures?limit=201").status_code == 422


def test_fixtures_filtered_by_club(client, seeded):
    fixtures = client.get("/api/fixtures?club=csm-bucuresti&limit=200").json()
    assert len(fixtures) == 26  # 13 home, 13 away
    assert all("csm-bucuresti" in (f["home"]["slug"], f["away"]["slug"]) for f in fixtures)
    assert client.get("/api/fixtures?club=nope").status_code == 404


def test_fixtures_filtered_by_dates(client, seeded):
    all_fixtures = client.get("/api/fixtures?limit=200").json()
    day = all_fixtures[0]["kickoff_at"][:10]
    one_round = client.get(f"/api/fixtures?date_from={day}&date_to={day}&limit=200").json()
    assert len(one_round) == 7  # one round: all 14 clubs, 7 matches, same kickoff
    later = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    assert all(f["kickoff_at"][:10] >= later for f in client.get(f"/api/fixtures?date_from={later}&limit=200").json())
    assert client.get("/api/fixtures?date_from=not-a-date").status_code == 422


def test_fixture_detail_lists_zones_with_seats_left(client, seeded, db):
    fixture_id = client.get("/api/fixtures?limit=1").json()[0]["id"]
    detail = client.get(f"/api/fixtures/{fixture_id}").json()
    assert [z["price_bani"] for z in detail["zones"]] == sorted((p for *_, p in ZONES), reverse=True)
    assert all(z["seats_left"] == z["quota"] for z in detail["zones"])


def test_sold_tickets_reduce_seats_left_but_cancelled_do_not(client, seeded, db, make_user):
    fixture = db.get(Fixture, client.get("/api/fixtures?limit=1").json()[0]["id"])
    zone = client.get(f"/api/fixtures/{fixture.id}").json()["zones"][0]
    order = Order(user_id=make_user().id)
    db.add(order)
    db.flush()
    for i, status in enumerate([TicketStatus.VALID, TicketStatus.USED, TicketStatus.CANCELLED]):
        db.add(Ticket(order_id=order.id, fixture_id=fixture.id, zone_id=zone["zone_id"], code=f"c{i}",
                      price_bani=zone["price_bani"], status=status))
    db.flush()
    after = client.get(f"/api/fixtures/{fixture.id}").json()["zones"][0]
    assert after["seats_left"] == zone["quota"] - 2


def test_unknown_fixture_is_404(client, seeded):
    assert client.get("/api/fixtures/999999").status_code == 404
    assert client.get("/api/fixtures/abc").status_code == 422


def test_robots_and_sitemap(client, seeded):
    robots = client.get("/robots.txt")
    assert "Disallow: /api/" in robots.text and "/sitemap.xml" in robots.text
    sitemap = client.get("/sitemap.xml")
    assert sitemap.headers["content-type"].startswith("application/xml")
    assert sitemap.text.count("<url>") == 3 + 14 + 182
    assert "/clubs/minaur-baia-mare</loc>" in sitemap.text
