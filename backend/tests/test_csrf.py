from app.security.csrf import COOKIE, is_valid_token, new_token

BODY = {"email": "ana@example.com", "display_name": "Ana", "password": "correct horse"}


def post(client, headers=None):
    return client.post("/api/auth/register", json=BODY, headers=headers or {})


def test_token_endpoint_sets_an_httponly_samesite_cookie(raw_client):
    res = raw_client.get("/api/csrf")
    cookie = res.headers["set-cookie"].lower()
    assert f"{COOKIE}=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert res.json()["csrf_token"] == raw_client.cookies.get(COOKIE)


def test_token_is_reused_while_the_cookie_is_valid(raw_client):
    first = raw_client.get("/api/csrf").json()["csrf_token"]
    assert raw_client.get("/api/csrf").json()["csrf_token"] == first


def test_post_without_token_is_rejected(raw_client):
    res = post(raw_client)
    assert res.status_code == 403
    assert res.json()["code"] == "csrf_failed"


def test_cookie_without_header_is_rejected(raw_client):
    raw_client.get("/api/csrf")
    assert post(raw_client).status_code == 403


def test_header_that_differs_from_cookie_is_rejected(raw_client):
    raw_client.get("/api/csrf")
    assert post(raw_client, {"X-CSRF-Token": new_token()}).status_code == 403


def test_planted_cookie_with_bad_signature_is_rejected(raw_client):
    raw_client.cookies.set(COOKIE, "attacker.chosen")
    assert post(raw_client, {"X-CSRF-Token": "attacker.chosen"}).status_code == 403


def test_valid_token_is_accepted(raw_client):
    token = raw_client.get("/api/csrf").json()["csrf_token"]
    assert post(raw_client, {"X-CSRF-Token": token}).status_code == 201


def test_safe_methods_need_no_token(raw_client):
    assert raw_client.get("/api/health").status_code == 200


def test_token_signature_check():
    assert is_valid_token(new_token())
    assert not is_valid_token(None) and not is_valid_token("no-dot") and not is_valid_token("a.b")


def test_rejection_is_logged(raw_client, activity):
    post(raw_client)
    assert [e for e, _ in activity.lines] == ["csrf_failed"]
