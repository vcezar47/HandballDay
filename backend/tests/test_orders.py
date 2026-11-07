import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import stripe
from sqlalchemy import select

from app.errors import AppValidationError, PaymentError
from app.gateways import FakeGateway, Line, StripeGateway
from app.models import Fixture, FixtureStatus, FixtureZone, Order, OrderStatus, Payment, Ticket, TicketStatus
from app.seed import seed_all

from .conftest import log_in


@pytest.fixture
def seeded(db):
    seed_all(db)


@pytest.fixture
def fan(client, seeded, make_user):
    user = make_user("fan@example.com")
    log_in(client, "fan@example.com")
    return user


def first_fixture(client):
    fid = client.get("/api/fixtures?limit=1").json()[0]["id"]
    return client.get(f"/api/fixtures/{fid}").json()


def buy(client, fixture, qty=1, zone=0):
    body = {"fixture_id": fixture["id"], "zone_id": fixture["zones"][zone]["zone_id"], "quantity": qty}
    return client.post("/api/checkout", json=body)


def send(client, kind, session_id, amount=None, signature=FakeGateway.SIGNATURE):
    body = json.dumps({"kind": kind, "session_id": session_id, "amount_bani": amount})
    return client.post("/api/webhooks/stripe", content=body, headers={"stripe-signature": signature})


def seats_left(client, fixture, zone=0):
    return client.get(f"/api/fixtures/{fixture['id']}").json()["zones"][zone]["seats_left"]


def test_guest_cannot_check_out(client, seeded):
    assert buy(client, first_fixture(client)).status_code == 401


def test_checkout_holds_seats_and_asks_the_gateway_for_the_right_amount(client, fan, gateway, db):
    fixture = first_fixture(client)
    price, before = fixture["zones"][0]["price_bani"], seats_left(client, fixture)
    res = buy(client, fixture, qty=2)
    assert res.status_code == 200 and res.json()["checkout_url"] == "https://pay.example/fake_1"
    ((_, _, lines),) = gateway.created
    assert lines == [Line(lines[0].name, price, 2)] and fixture["zones"][0]["name"] in lines[0].name
    assert seats_left(client, fixture) == before - 2
    payment = db.scalar(select(Payment))
    assert payment.amount_bani == 2 * price and payment.provider_ref == "fake_1"
    assert client.get("/api/tickets").json() == []  # held seats are not tickets yet


@pytest.mark.parametrize("quantity", [0, 7, -1])
def test_quantity_is_limited(client, fan, quantity):
    assert buy(client, first_fixture(client), qty=quantity).status_code == 422


def test_cannot_take_more_seats_than_are_left(client, fan, db):
    fixture = first_fixture(client)
    db.get(FixtureZone, (fixture["id"], fixture["zones"][0]["zone_id"])).quota = 2
    db.commit()
    res = buy(client, fixture, qty=3)
    assert res.status_code == 409 and "Only 2" in res.json()["detail"]
    assert buy(client, fixture, qty=2).status_code == 200
    again = buy(client, fixture, qty=1)
    assert again.status_code == 409 and again.json()["detail"] == "Sold out"


def test_zone_must_be_on_sale_for_that_fixture(client, fan):
    fixture = first_fixture(client)
    other = client.get("/api/fixtures?limit=200").json()[-1]["id"]  # another venue, so other zone ids
    other_zone = client.get(f"/api/fixtures/{other}").json()["zones"][0]["zone_id"]
    res = client.post("/api/checkout", json={"fixture_id": fixture["id"], "zone_id": other_zone, "quantity": 1})
    assert res.status_code == 404
    assert client.post("/api/checkout", json={"fixture_id": 999999, "zone_id": 1, "quantity": 1}).status_code == 404


def test_cancelled_or_started_fixtures_are_not_on_sale(client, fan, db):
    fixture = first_fixture(client)
    row = db.get(Fixture, fixture["id"])
    row.status = FixtureStatus.CANCELLED
    db.commit()
    assert buy(client, fixture).status_code == 409
    row.status, row.kickoff_at = FixtureStatus.SCHEDULED, datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    assert buy(client, fixture).status_code == 409


def test_gateway_failure_gives_the_seats_back(client, fan, gateway):
    fixture = first_fixture(client)
    before = seats_left(client, fixture)
    gateway.fail = True
    res = buy(client, fixture, qty=2)
    assert res.status_code == 402 and res.json()["code"] == "payment_failed"
    assert seats_left(client, fixture) == before


def test_webhook_rejects_a_bad_signature(client, fan):
    buy(client, first_fixture(client))
    assert send(client, "paid", "fake_1", 1, signature="forged").status_code == 422
    assert client.get("/api/tickets").json() == []


def test_paid_webhook_issues_tickets_once(client, fan, db):
    fixture = first_fixture(client)
    price = fixture["zones"][0]["price_bani"]
    buy(client, fixture, qty=2)
    assert send(client, "paid", "fake_1", 2 * price).status_code == 200
    tickets = client.get("/api/tickets").json()
    assert len(tickets) == 2 and {t["status"] for t in tickets} == {"valid"}
    assert len({t["code"] for t in tickets}) == 2 and all(len(t["code"]) >= 32 for t in tickets)
    assert tickets[0]["fixture"]["id"] == fixture["id"] and tickets[0]["zone"] == fixture["zones"][0]["name"]
    paid_at = db.scalar(select(Order.paid_at))
    send(client, "paid", "fake_1", 2 * price)  # Stripe retries; nothing may change
    assert len(client.get("/api/tickets").json()) == 2 and db.scalar(select(Order.paid_at)) == paid_at


def test_wrong_amount_issues_nothing(client, fan, db, activity):
    buy(client, first_fixture(client))
    send(client, "paid", "fake_1", 1)
    assert client.get("/api/tickets").json() == []
    assert db.scalar(select(Order.status)) == OrderStatus.PENDING
    assert activity.lines[-1][0] == "payment_rejected"


def test_expired_session_releases_seats_and_cannot_be_paid_later(client, fan, db):
    fixture = first_fixture(client)
    price, before = fixture["zones"][0]["price_bani"], seats_left(client, fixture)
    buy(client, fixture, qty=2)
    send(client, "expired", "fake_1")
    assert seats_left(client, fixture) == before
    send(client, "paid", "fake_1", 2 * price)
    assert client.get("/api/tickets").json() == []
    assert set(db.scalars(select(Ticket.status))) == {TicketStatus.CANCELLED}


def test_unknown_session_is_ignored(client, seeded):
    assert send(client, "paid", "nope", 1).status_code == 200


def test_webhook_needs_no_csrf_token_but_other_posts_do(raw_client):
    assert send(raw_client, "paid", "nope", 1).status_code == 200
    assert raw_client.post("/api/checkout", json={}).status_code == 403


def test_unpaid_holds_lapse(client, fan, db):
    fixture = first_fixture(client)
    before = seats_left(client, fixture)
    buy(client, fixture, qty=3)
    assert seats_left(client, fixture) == before - 3
    db.execute(Order.__table__.update().values(created_at=datetime.now(timezone.utc) - timedelta(hours=1)))
    assert seats_left(client, fixture) == before


def test_my_tickets_lists_only_my_own(client, fan, make_user):
    fixture = first_fixture(client)
    buy(client, fixture)
    send(client, "paid", "fake_1", fixture["zones"][0]["price_bani"])
    assert len(client.get("/api/tickets").json()) == 1
    make_user("other@example.com")
    log_in(client, "other@example.com")
    assert client.get("/api/tickets").json() == []


# ---- the real Stripe gateway, without the network ----

SECRET = "whsec_test_secret"


def signed(payload: dict, secret=SECRET):
    body = json.dumps(payload)
    t = int(time.time())
    sig = hmac.new(secret.encode(), f"{t}.{body}".encode(), hashlib.sha256).hexdigest()
    return body.encode(), f"t={t},v1={sig}"


def stripe_event(kind, **obj):
    session = {"id": "cs_1", "object": "checkout.session", **obj}
    return {"id": "evt_1", "object": "event", "type": kind, "data": {"object": session}}


def test_stripe_gateway_verifies_signatures_and_maps_events():
    gw = StripeGateway("sk_test_x", SECRET)
    body, sig = signed(stripe_event("checkout.session.completed", payment_status="paid", amount_total=4500))
    event = gw.read_event(body, sig)
    assert (event.kind, event.session_id, event.amount_bani) == ("paid", "cs_1", 4500)
    assert gw.read_event(*signed(stripe_event("checkout.session.expired"))).kind == "expired"
    unpaid = stripe_event("checkout.session.completed", payment_status="unpaid", amount_total=1)
    assert gw.read_event(*signed(unpaid)) is None
    with pytest.raises(AppValidationError):
        gw.read_event(body, sig.replace("v1=", "v1=0"))  # tampered signature
    with pytest.raises(AppValidationError):
        gw.read_event(body + b" ", sig)  # tampered body
    with pytest.raises(AppValidationError):
        gw.read_event(*signed(stripe_event("checkout.session.expired"), secret="whsec_other"))


def test_stripe_gateway_builds_a_ron_checkout_session():
    seen = {}

    def create(params):
        seen.update(params)
        return SimpleNamespace(id="cs_9", url="https://checkout.stripe.com/c/pay/cs_9")

    gw = StripeGateway("sk_test_x", SECRET)
    gw.client = SimpleNamespace(checkout=SimpleNamespace(sessions=SimpleNamespace(create=create)))
    expires = datetime(2030, 1, 1, tzinfo=timezone.utc)
    session = gw.create_checkout(7, [Line("A vs B, VIP", 8000, 2)], "https://x/ok", "https://x/back", expires)
    assert (session.id, session.url) == ("cs_9", "https://checkout.stripe.com/c/pay/cs_9")
    item = seen["line_items"][0]
    assert item["quantity"] == 2 and item["price_data"]["unit_amount"] == 8000
    assert item["price_data"]["currency"] == "ron"
    assert seen["client_reference_id"] == "7" and seen["expires_at"] == int(expires.timestamp())
    assert seen["mode"] == "payment"

    def refuse(params):
        raise stripe.APIConnectionError("down")

    gw.client.checkout.sessions.create = refuse
    with pytest.raises(PaymentError):
        gw.create_checkout(7, [], "https://x/ok", "https://x/back", expires)
