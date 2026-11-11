"""Rate limiting (10.01), CAPTCHA (10.02) and security headers (10.04)."""

import re
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.config import get_config
from app.errors import AppValidationError
from app.limits import limiter
from app.main import create_app
from app.security.captcha import CaptchaVerifier, NoCaptcha, TurnstileVerifier, get_captcha
from app.security.headers import API_CSP, SPA_CSP

from .conftest import PASSWORD, log_in, make_client

BODY = {"email": "ana@example.com", "display_name": "Ana", "password": PASSWORD}
VITE_CONFIG = Path(__file__).resolve().parents[2] / "frontend" / "vite.config.js"


@pytest.fixture
def limited():
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()


# ---- rate limiting ----

def test_login_is_limited_after_ten_attempts(client, limited):
    wrong = {"email": "ana@example.com", "password": "wrong password"}
    assert [client.post("/api/auth/login", json=wrong).status_code for _ in range(10)] == [401] * 10
    res = client.post("/api/auth/login", json=wrong)
    assert res.status_code == 429 and res.json()["code"] == "rate_limited" and res.headers["retry-after"] == "60"


def test_register_is_limited(client, limited):
    codes = [client.post("/api/auth/register", json={**BODY, "email": f"u{i}@example.com"}).status_code for i in range(11)]
    assert codes[:10] == [201] * 10 and codes[10] == 429


def test_checkout_is_limited(client, limited, make_user):
    make_user("fan@example.com")
    log_in(client, "fan@example.com")
    body = {"fixture_id": 999999, "zone_id": 1, "quantity": 1}  # reaches the handler, then 404
    assert [client.post("/api/checkout", json=body).status_code for _ in range(10)] == [404] * 10
    assert client.post("/api/checkout", json=body).status_code == 429


def test_every_other_route_has_a_loose_default_limit(client, limited):
    assert all(client.get("/api/health").status_code == 200 for _ in range(300))
    assert client.get("/api/health").status_code == 429


def test_limits_are_per_route_not_shared(client, limited):
    wrong = {"email": "ana@example.com", "password": "wrong password"}
    for _ in range(11):
        client.post("/api/auth/login", json=wrong)
    assert client.get("/api/health").status_code == 200  # a locked-out login does not lock the site


# ---- CAPTCHA ----

class NeedsToken(CaptchaVerifier):
    def check(self, token, ip):
        if token != "good-token":
            raise AppValidationError("Please complete the CAPTCHA")


@pytest.fixture
def strict_captcha(client):
    from app.main import app

    app.dependency_overrides[get_captcha] = lambda: NeedsToken()
    return client


def test_register_and_login_need_a_captcha_token(strict_captcha):
    assert strict_captcha.post("/api/auth/register", json=BODY).status_code == 422
    assert strict_captcha.post("/api/auth/register", json={**BODY, "captcha_token": "bad"}).status_code == 422
    assert strict_captcha.post("/api/auth/register", json={**BODY, "captcha_token": "good-token"}).status_code == 201
    login = {"email": BODY["email"], "password": PASSWORD}
    assert strict_captcha.post("/api/auth/login", json=login).status_code == 422
    assert strict_captcha.post("/api/auth/login", json={**login, "captcha_token": "good-token"}).status_code == 200


def test_upload_needs_a_captcha_token(strict_captcha, make_user, tmp_path, monkeypatch):
    monkeypatch.setattr(get_config(), "upload_dir", tmp_path)
    make_user("fan@example.com")
    login = {"email": "fan@example.com", "password": PASSWORD, "captcha_token": "good-token"}
    assert strict_captcha.post("/api/auth/login", json=login).status_code == 200
    assert strict_captcha.post("/api/uploads", content=b"x", headers={"X-Filename": "a.png"}).status_code == 422
    res = strict_captcha.post("/api/uploads", content=b"x", headers={"X-Filename": "a.png", "X-Captcha-Token": "good-token"})
    assert res.status_code == 422 and "valid image" in res.json()["detail"]  # got past the CAPTCHA, then failed on the bytes


def post_spy(monkeypatch, result):
    seen = {}

    def fake_post(url, data, timeout):
        seen.update(url=url, data=data)
        if isinstance(result, Exception):
            raise result
        return SimpleNamespace(json=lambda: result)

    monkeypatch.setattr(httpx, "post", fake_post)
    return seen


def test_turnstile_verifier_asks_cloudflare_and_fails_closed(monkeypatch, activity):
    verifier = TurnstileVerifier("secret-xyz")
    seen = post_spy(monkeypatch, {"success": True})
    verifier.check("tok", "1.2.3.4")
    assert seen["url"].startswith("https://challenges.cloudflare.com/") and seen["data"] == {"secret": "secret-xyz", "response": "tok", "remoteip": "1.2.3.4"}

    with pytest.raises(AppValidationError):
        verifier.check(None, "1.2.3.4")  # no token: never even asks
    post_spy(monkeypatch, {"success": False, "error-codes": ["invalid-input-response"]})
    with pytest.raises(AppValidationError, match="failed"):
        verifier.check("tok", None)
    assert activity.lines[-1][0] == "captcha_failed"
    post_spy(monkeypatch, httpx.ConnectError("down"))
    with pytest.raises(AppValidationError, match="could not be checked"):
        verifier.check("tok", None)
    assert activity.lines[-1][0] == "captcha_unavailable"
    post_spy(monkeypatch, {"success": "true"})  # only a real boolean counts
    with pytest.raises(AppValidationError):
        verifier.check("tok", None)


def test_captcha_is_off_without_a_secret_and_the_site_key_is_hidden(client, monkeypatch):
    assert isinstance(get_captcha(), NoCaptcha)
    assert client.get("/api/config").json() == {"turnstile_site_key": ""}
    monkeypatch.setattr(get_config(), "turnstile_site_key", "site-key")
    assert client.get("/api/config").json() == {"turnstile_site_key": ""}  # a key without a secret changes nothing
    monkeypatch.setattr(get_config(), "turnstile_secret_key", "secret")
    assert isinstance(get_captcha(), TurnstileVerifier)
    assert client.get("/api/config").json() == {"turnstile_site_key": "site-key"}


# ---- security headers ----

def expect_headers(res):
    h = res.headers
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in h["permissions-policy"] and h["content-security-policy"] == API_CSP


def test_every_kind_of_response_carries_the_headers(client, raw_client):
    expect_headers(client.get("/api/health"))
    expect_headers(client.get("/api/clubs/nope"))  # an error response
    expect_headers(raw_client.post("/api/auth/login", json={}))  # rejected by CSRF before reaching a route
    assert "strict-transport-security" not in client.get("/api/health").headers  # plain HTTP: no HSTS promise


def test_hsts_is_sent_in_production_mode_only(db, monkeypatch):
    monkeypatch.setattr(get_config(), "secure_cookies", True)
    res = make_client(create_app(), db).get("/api/health")
    assert res.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"


def test_api_docs_still_load_in_development(client):
    res = client.get("/docs")
    assert res.status_code == 200 and "content-security-policy" not in res.headers and res.headers["x-frame-options"] == "DENY"


def test_the_spa_policy_is_strict_and_matches_the_vite_preview_config():
    script = next(p for p in SPA_CSP.split("; ") if p.startswith("script-src"))
    assert "unsafe" not in script and "unsafe-eval" not in SPA_CSP and "style-src 'self';" in SPA_CSP
    assert "frame-ancestors 'none'" in SPA_CSP and "object-src 'none'" in SPA_CSP and "default-src 'self'" in SPA_CSP
    block = VITE_CONFIG.read_text(encoding="utf-8").split("const SPA_CSP =")[1].split("\n\n")[0]  # the string is split over lines there
    assert "".join(re.findall(r'"([^"]*)"', block)) == SPA_CSP, "update frontend/vite.config.js to match SPA_CSP"
