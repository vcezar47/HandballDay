"""Rate limits (barem 10.01): strict on the endpoints worth abusing, loose everywhere else.

shortcut: counters live in this process's memory, so they reset on restart and are not shared
between workers; point slowapi at Redis (storage_uri) if the app ever runs more than one process.
Behind the Apache proxy uvicorn reads X-Forwarded-For from 127.0.0.1, so the key is the visitor's address.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_config

STRICT = "10/minute"  # login, register, checkout
UPLOAD = "20/minute"
LOOSE = "300/minute"  # every other route

limiter = Limiter(key_func=get_remote_address, default_limits=[LOOSE], enabled=get_config().rate_limit)


async def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Same JSON shape as every other error; the windows are one minute long, so a minute is a safe wait.
    return JSONResponse(
        {"detail": "Too many requests, please slow down and try again in a minute", "code": "rate_limited"},
        status_code=429, headers={"Retry-After": "60"},
    )
