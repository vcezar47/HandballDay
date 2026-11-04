import logging
from logging.handlers import RotatingFileHandler

from app.activity import _logger, log_activity

BODY = {"email": "ana@example.com", "display_name": "Ana", "password": "correct horse"}


def test_auth_events_are_logged_without_secrets(client, activity):
    client.post("/api/auth/register", json=BODY)
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": BODY["email"], "password": "wrong password"})
    client.post("/api/auth/login", json={"email": BODY["email"], "password": BODY["password"]})

    assert [e for e, _ in activity.lines] == ["register", "logout", "login_failed", "login"]
    assert activity.lines[2][1]["email"] == "ana@example.com"
    everything = str(activity.lines)
    assert "wrong password" not in everything and BODY["password"] not in everything


def test_a_newline_in_a_value_cannot_forge_a_second_line(activity):
    log_activity("probe", name="x\n2026-01-01 00:00:00 login {\"user_id\": 1}")
    assert len(activity.lines) == 1


def test_log_goes_to_a_rotating_file():
    handlers = [h for h in _logger().handlers if isinstance(h, RotatingFileHandler)]
    assert handlers and handlers[0].backupCount > 0 and handlers[0].maxBytes > 0
    assert logging.getLogger("activity").propagate is False
