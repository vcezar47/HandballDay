"""CAPTCHA (barem 10.02): Cloudflare Turnstile, checked on the server. The browser's say-so is never enough."""

from abc import ABC, abstractmethod

import httpx

from ..activity import log_activity
from ..config import get_config
from ..errors import AppValidationError

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class CaptchaVerifier(ABC):
    @abstractmethod
    def check(self, token: str | None, ip: str | None) -> None:
        """Return if the visitor passed; raise AppValidationError if not."""


class NoCaptcha(CaptchaVerifier):
    """No Turnstile secret configured: local development and tests."""

    def check(self, token, ip):
        return None


class TurnstileVerifier(CaptchaVerifier):
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def check(self, token, ip):
        if not token:
            raise AppValidationError("Please complete the CAPTCHA")
        try:
            res = httpx.post(VERIFY_URL, data={"secret": self.secret, "response": token, "remoteip": ip or ""}, timeout=5)
            passed = res.json().get("success") is True
        except (httpx.HTTPError, ValueError):
            # Fail closed: if Cloudflare cannot be reached, nobody gets through unchecked.
            log_activity("captcha_unavailable", ip=ip)
            raise AppValidationError("The CAPTCHA could not be checked, please try again") from None
        if not passed:
            log_activity("captcha_failed", ip=ip)
            raise AppValidationError("CAPTCHA failed, please try again")


def get_captcha() -> CaptchaVerifier:
    """FastAPI dependency; tests replace it."""
    secret = get_config().turnstile_secret_key
    return TurnstileVerifier(secret) if secret else NoCaptcha()
