"""Activity log (barem 7.01): one line per security-relevant event, in a rotating file.

    2026-11-04 10:15:02 login {"user_id": 3, "ip": "127.0.0.1"}

Fields are JSON-encoded, so a newline typed by an attacker cannot forge a second log line.
Never pass passwords, tokens or ticket codes.
"""

import json
import logging
from logging.handlers import RotatingFileHandler

from .config import get_config

LOGGER_NAME = "activity"


def _logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        log_dir = get_config().log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_dir / "activity.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_activity(event: str, **fields) -> None:
    _logger().info("%s %s", event, json.dumps(fields, ensure_ascii=False, default=str))


def read_activity(limit: int = 200, event: str | None = None) -> list[dict]:
    """The newest entries of the current log file, newest first, optionally of one event type."""
    path = get_config().log_dir / "activity.log"
    if not path.is_file():
        return []
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            when, _, rest = line.rstrip().partition(" ")
            clock, _, rest = rest.partition(" ")
            name, _, payload = rest.partition(" ")
            if event and name != event:
                continue
            try:
                fields = json.loads(payload)
            except ValueError:  # a line from something else in the file: show it rather than hide it
                fields = {"raw": payload}
            entries.append({"time": f"{when} {clock}", "event": name, "fields": fields})
    return entries[-limit:][::-1]
