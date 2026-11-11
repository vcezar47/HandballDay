"""XSS (9.02): nothing that means markup is accepted as text, and the frontend never turns text into markup."""

import re
from pathlib import Path

import pytest

from app.seed import seed_all

from .conftest import PASSWORD, log_in

FRONTEND_SRC = Path(__file__).resolve().parents[2] / "frontend" / "src"
PAYLOADS = [
    "<script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "<svg/onload=alert(1)>",
    "javascript:alert(1)",
    "';alert(String.fromCharCode(88,83,83))//",
    "{{7*7}}",
    "&lt;b&gt;",
]


@pytest.mark.parametrize("payload", PAYLOADS)
def test_display_name_refuses_markup_payloads(client, db, payload):
    res = client.post("/api/auth/register", json={"email": "x@example.com", "display_name": payload, "password": PASSWORD})
    assert res.status_code == 422


@pytest.mark.parametrize("name", ["Ana Maria", "Ștefan-Ioan", "O'Brien", "Dr. Who_2", "Ion 3rd"])
def test_ordinary_names_still_work(client, name):
    res = client.post("/api/auth/register", json={"email": "x@example.com", "display_name": name, "password": PASSWORD})
    assert res.status_code == 201 and res.json()["user"]["display_name"] == name


@pytest.mark.parametrize("payload", PAYLOADS)
def test_jersey_name_refuses_markup_payloads(client, db, make_user, payload):
    seed_all(db)
    make_user("fan@example.com")
    log_in(client, "fan@example.com")
    fixture = client.get("/api/fixtures?limit=1").json()[0]
    zone = client.get(f"/api/fixtures/{fixture['id']}").json()["zones"][0]["zone_id"]
    template = client.get("/api/jersey-templates").json()["templates"][0]["id"]
    jersey = {"club": "minaur-baia-mare", "template_id": template, "primary_color": "#014698", "secondary_color": "#ffffff", "name_text": payload, "number": 1, "size": "M"}
    res = client.post("/api/checkout", json={"fixture_id": fixture["id"], "zone_id": zone, "quantity": 1, "jersey": jersey})
    assert res.status_code == 422


def test_api_data_is_json_and_not_sniffable(client):
    res = client.get("/api/clubs")
    assert res.headers["content-type"].startswith("application/json") and res.headers["x-content-type-options"] == "nosniff"


def test_the_frontend_never_builds_markup_from_text():
    banned = re.compile(r"dangerouslySetInnerHTML|\.innerHTML|\.outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function\(")
    hits = [f"{p.name}: {m.group()}" for p in FRONTEND_SRC.rglob("*.js*") for m in banned.finditer(p.read_text(encoding="utf-8"))]
    assert hits == []
