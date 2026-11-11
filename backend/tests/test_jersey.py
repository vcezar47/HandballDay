import json
from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy import func, select

from app.config import get_config
from app.gateways import FakeGateway
from app.models import Order
from app.seed import seed_all
from app.services.orders import JERSEY_PRICE_BANI

from .conftest import log_in


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(get_config(), "upload_dir", tmp_path)


@pytest.fixture
def fan(client, db, make_user):
    seed_all(db)
    user = make_user("fan@example.com")
    log_in(client, "fan@example.com")
    return user


def fixture_detail(client):
    fid = client.get("/api/fixtures?limit=1").json()[0]["id"]
    return client.get(f"/api/fixtures/{fid}").json()


def jersey(client, **over):
    template = client.get("/api/jersey-templates").json()["templates"][0]["id"]
    base = {
        "club": "minaur-baia-mare", "template_id": template, "primary_color": "#014698",
        "secondary_color": "#FFFFFF", "name_text": "Popescu", "number": 10, "size": "M",
    }
    return {**base, **over}


def buy(client, fixture, jersey_body=None, qty=2):
    body = {"fixture_id": fixture["id"], "zone_id": fixture["zones"][0]["zone_id"], "quantity": qty}
    if jersey_body is not None:
        body["jersey"] = jersey_body
    return client.post("/api/checkout", json=body)


def pay(client, session_id, amount):
    body = json.dumps({"kind": "paid", "session_id": session_id, "amount_bani": amount})
    return client.post("/api/webhooks/stripe", content=body, headers={"stripe-signature": FakeGateway.SIGNATURE})


def test_templates_are_public_and_seeded_once(client, db):
    seed_all(db)
    seed_all(db)
    data = client.get("/api/jersey-templates").json()
    assert [t["svg_key"] for t in data["templates"]] == ["classic", "stripes", "sash"]
    assert data["price_bani"] == JERSEY_PRICE_BANI and "XL" in data["sizes"]


def test_jersey_joins_the_same_order_and_payment_as_the_tickets(client, fan, gateway, db):
    fixture = fixture_detail(client)
    price = fixture["zones"][0]["price_bani"]
    assert buy(client, fixture, jersey(client), qty=2).status_code == 200
    ((session_id, _, lines),) = gateway.created  # one Stripe session, two lines
    assert [line.quantity for line in lines] == [2, 1]
    assert lines[1].unit_bani == JERSEY_PRICE_BANI and "#10 POPESCU" in lines[1].name and "size M" in lines[1].name
    assert db.scalar(select(func.count()).select_from(Order)) == 1
    assert client.get("/api/jerseys").json() == []  # not paid yet

    assert pay(client, session_id, 2 * price).status_code == 200  # tickets only: the amount does not match, nothing issued
    assert client.get("/api/jerseys").json() == [] and client.get("/api/tickets").json() == []

    assert pay(client, session_id, 2 * price + JERSEY_PRICE_BANI).status_code == 200
    (mine,) = client.get("/api/jerseys").json()
    assert mine["name_text"] == "POPESCU" and mine["number"] == 10 and mine["size"] == "M"
    assert mine["secondary_color"] == "#ffffff" and mine["template"] == "classic"
    assert mine["pickup"]["id"] == fixture["id"] and mine["club"]["slug"] == "minaur-baia-mare"
    assert mine["price_bani"] == JERSEY_PRICE_BANI
    assert len(client.get("/api/tickets").json()) == 2


def test_a_ticket_alone_still_works(client, fan, gateway):
    assert buy(client, fixture_detail(client)).status_code == 200
    assert len(gateway.created[0][2]) == 1


@pytest.mark.parametrize("over", [
    {"primary_color": "red"}, {"primary_color": "#12345"}, {"secondary_color": "#gggggg"},
    {"primary_color": "javascript:alert(1)"}, {"primary_color": "#014698; background:url(x)"},
    {"name_text": "<script>alert(1)</script>"}, {"name_text": "A\"B"}, {"name_text": "A&B"},
    {"name_text": ""}, {"name_text": "   "}, {"name_text": "X" * 16},
    {"number": 100}, {"number": -1}, {"number": "ten"}, {"size": "XXXL"}, {"size": ""},
])
def test_invalid_jersey_input_is_rejected_and_nothing_is_created(client, fan, db, over):
    assert buy(client, fixture_detail(client), jersey(client, **over)).status_code == 422
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_names_allow_diacritics_and_are_upper_cased(client, fan, gateway):
    assert buy(client, fixture_detail(client), jersey(client, name_text="ștefan \n o'neil")).status_code == 200
    assert "ȘTEFAN O'NEIL" in gateway.created[0][2][1].name


def test_unknown_references_are_404(client, fan, db):
    fixture = fixture_detail(client)
    assert buy(client, fixture, jersey(client, club="nope")).status_code == 404
    assert buy(client, fixture, jersey(client, template_id=999999)).status_code == 404
    assert buy(client, fixture, jersey(client, logo_upload_id=999999)).status_code == 404
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_a_logo_must_be_my_own_upload(client, fan, make_user):
    out = BytesIO()
    Image.new("RGB", (40, 40), (0, 0, 255)).save(out, "PNG")
    logo = client.post("/api/uploads", content=out.getvalue(), headers={"X-Filename": "l.png"}).json()["id"]
    fixture = fixture_detail(client)
    assert buy(client, fixture, jersey(client, logo_upload_id=logo)).status_code == 200

    make_user("other@example.com")
    log_in(client, "other@example.com")
    assert buy(client, fixture, jersey(client, logo_upload_id=logo)).status_code == 404  # someone else's file


def test_jerseys_need_login_and_are_private(client, fan, gateway, make_user):
    fixture = fixture_detail(client)
    buy(client, fixture, jersey(client))
    pay(client, gateway.created[0][0], 2 * fixture["zones"][0]["price_bani"] + JERSEY_PRICE_BANI)
    assert len(client.get("/api/jerseys").json()) == 1
    make_user("other@example.com")
    log_in(client, "other@example.com")
    assert client.get("/api/jerseys").json() == []
    client.post("/api/auth/logout")
    assert client.get("/api/jerseys").status_code == 401
