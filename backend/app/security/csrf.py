"""CSRF protection (barem 9.01): signed double-submit token on top of SameSite=Lax cookies.

The client calls GET /api/csrf, which sets a cookie and returns the same token in JSON. Every
POST/PUT/PATCH/DELETE must send it back in the X-CSRF-Token header. A page on another site
can make the browser send the cookie but cannot read the token to put it in the header.
The token is signed, so a cookie planted by an attacker (for example from a sibling subdomain) fails too.
"""

import hashlib
import hmac
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..activity import log_activity
from ..config import get_config

COOKIE = "hd_csrf"
HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _sign(nonce: str) -> str:
    key = get_config().secret_key.encode()
    return hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()[:32]


def new_token() -> str:
    nonce = secrets.token_urlsafe(16)
    return f"{nonce}.{_sign(nonce)}"


def is_valid_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    nonce, sig = token.rsplit(".", 1)
    return hmac.compare_digest(sig.encode(), _sign(nonce).encode())


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in SAFE_METHODS:
            cookie = request.cookies.get(COOKIE)
            header = request.headers.get(HEADER)
            if not (cookie and header and hmac.compare_digest(cookie.encode(), header.encode()) and is_valid_token(cookie)):
                log_activity("csrf_failed", path=request.url.path, ip=request.client.host if request.client else None)
                return JSONResponse(
                    {"detail": "CSRF token missing or invalid", "code": "csrf_failed"}, status_code=403
                )
        return await call_next(request)
