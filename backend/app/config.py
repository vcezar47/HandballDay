"""Environment-based settings. Pick one with APP_ENV=dev|test|prod (default dev)."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Config:
    name = "dev"
    default_db_name = "handballday"
    cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    def __init__(self) -> None:
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", self.default_db_name)
        self.port = int(os.getenv("PORT", "3000"))
        self.secret_key = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
        self.log_dir = BACKEND_DIR / "logs"
        self.upload_dir = BACKEND_DIR / "uploads"  # not served as static files: only through the owner-checked route
        # Absolute URL of the site, for sitemap.xml and robots.txt.
        self.public_url = os.getenv("PUBLIC_URL", "http://localhost:5173").rstrip("/")
        # Stripe test-mode keys (sk_test_..., whsec_...); empty means payments are not configured.
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        # Cloudflare Turnstile. No secret means no CAPTCHA (handy locally); prod requires both keys.
        self.turnstile_site_key = os.getenv("TURNSTILE_SITE_KEY", "")
        self.turnstile_secret_key = os.getenv("TURNSTILE_SECRET_KEY", "")

    # Cookies only travel over HTTPS in production.
    secure_cookies = False
    rate_limit = True
    session_max_age = 14 * 24 * 3600


class DevConfig(Config):
    pass


class TestConfig(Config):
    name = "test"
    rate_limit = False  # one client address for every test; the rate-limit tests switch it on themselves
    # Fixed on purpose: tests drop and recreate every table, never point them at real data.
    default_db_name = "handballday_test"

    def __init__(self) -> None:
        super().__init__()
        self.db_name = self.default_db_name
        self.log_dir = BACKEND_DIR / "logs" / "test"
        self.upload_dir = BACKEND_DIR / "uploads" / "test"
        self.stripe_secret_key = self.stripe_webhook_secret = ""  # tests never reach the real Stripe
        self.turnstile_site_key = self.turnstile_secret_key = ""


class ProdConfig(Config):
    name = "prod"
    cors_origins: list[str] = []  # same origin behind the Apache proxy
    secure_cookies = True

    def __init__(self) -> None:
        super().__init__()
        for var in ("DB_PASSWORD", "SECRET_KEY", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "TURNSTILE_SITE_KEY", "TURNSTILE_SECRET_KEY"):
            if not os.getenv(var):
                raise RuntimeError(f"{var} must be set when APP_ENV=prod")


_CONFIGS = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}


@lru_cache
def get_config() -> Config:
    env = os.getenv("APP_ENV", "dev")
    if env not in _CONFIGS:
        raise RuntimeError(f"APP_ENV must be one of {sorted(_CONFIGS)}, got {env!r}")
    return _CONFIGS[env]()
