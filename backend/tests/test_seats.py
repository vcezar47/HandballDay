import pytest

from app.arena import build_layout, find_sector, seat_codes
from app.seed import seed_all

from .conftest import log_in


@pytest.mark.parametrize("zones", [
    {"VIP": 443, "Main stand": 1109, "End stand": 666},
    {"VIP": 300, "Main stand": 750, "End stand": 450},
    {"VIP": 1, "Main stand": 2, "End stand": 1},
])
def test_seats_of_each_zone_add_up_to_its_capacity(zones):
    layout = build_layout(zones)
    for name, capacity in zones.items():
        assert sum(s.seats for s in layout if s.zone == name) == capacity
    codes = [c for s in layout for c in seat_codes(s)]
    assert len(codes) == len(set(codes)) == sum(zones.values())


def test_find_sector_rejects_seats_that_do_not_exist():
    layout = build_layout({"VIP": 100, "Main stand": 200, "End stand": 100})
    assert find_sector(layout, "M1-1-1")[0].code == "M1"
    for bad in ["M1-0-1", "M1-1-0", "M1-99-1", "M1-1-99", "X9-1-1", "M1-1", "M1-a-b", "", "M1-1-1-1"]:
        assert find_sector(layout, bad) is None


@pytest.fixture
def fan(client, db, make_user):
    seed_all(db)
    make_user("fan@example.com")
    log_in(client, "fan@example.com")


def fixture_and_map(client):
    fid = client.get("/api/fixtures?limit=1").json()[0]["id"]
    return client.get(f"/api/fixtures/{fid}").json(), client.get(f"/api/fixtures/{fid}/seats").json()


def buy_seats(client, fixture, zone_id, seats):
    return client.post("/api/checkout", json={"fixture_id": fixture["id"], "zone_id": zone_id, "seats": seats})


def test_seat_map_lists_every_zone_of_the_venue(client, fan):
    fixture, seat_map = fixture_and_map(client)
    by_zone = {}
    for s in seat_map["sectors"]:
        by_zone[s["zone_id"]] = by_zone.get(s["zone_id"], 0) + sum(s["rows"])
    assert by_zone == {z["zone_id"]: z["quota"] for z in fixture["zones"]}
    assert seat_map["taken"] == []
    assert client.get("/api/fixtures/999999/seats").status_code == 404


def test_a_seat_can_only_be_bought_once_and_shows_on_the_ticket(client, fan, gateway):
    fixture, seat_map = fixture_and_map(client)
    sector = seat_map["sectors"][0]
    seats = [f"{sector['code']}-1-1", f"{sector['code']}-1-2"]
    assert buy_seats(client, fixture, sector["zone_id"], seats).status_code == 200
    assert client.get(f"/api/fixtures/{fixture['id']}/seats").json()["taken"] == seats  # held while unpaid
    again = buy_seats(client, fixture, sector["zone_id"], seats[1:])
    assert again.status_code == 409 and seats[1] in again.json()["detail"]
    ((_, _, lines),) = gateway.created
    assert lines[0].quantity == 2 and seats[0] in lines[0].name


@pytest.mark.parametrize("seats", [["M1-99-1"], ["nonsense"], ["M1-1-1", "M1-1-1"]])
def test_bad_seats_are_refused(client, fan, seats):
    fixture, seat_map = fixture_and_map(client)
    main = next(s for s in seat_map["sectors"] if s["code"] == "M1")
    assert buy_seats(client, fixture, main["zone_id"], seats).status_code in (409, 422)


def test_seat_from_another_zone_is_refused(client, fan):
    fixture, seat_map = fixture_and_map(client)
    vip = next(s for s in seat_map["sectors"] if s["code"] == "V1")
    main = next(s for s in seat_map["sectors"] if s["code"] == "M1")
    res = buy_seats(client, fixture, vip["zone_id"], ["M1-1-1"])
    assert res.status_code == 422 and main["zone_id"] != vip["zone_id"]


def test_quantity_must_match_the_seats(client, fan):
    fixture, seat_map = fixture_and_map(client)
    zone = seat_map["sectors"][0]["zone_id"]
    body = {"fixture_id": fixture["id"], "zone_id": zone, "seats": ["M1-1-1"], "quantity": 2}
    assert client.post("/api/checkout", json=body).status_code == 422
    assert client.post("/api/checkout", json={"fixture_id": fixture["id"], "zone_id": zone}).status_code == 422
