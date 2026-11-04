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

    # Cookies only travel over HTTPS in production.
    secure_cookies = False
    session_max_age = 14 * 24 * 3600


class DevConfig(Config):
    pass


class TestConfig(Config):
    name = "test"
    # Fixed on purpose: tests drop and recreate every table, never point them at real data.
    default_db_name = "handballday_test"

    def __init__(self) -> None:
        super().__init__()
        self.db_name = self.default_db_name
        self.log_dir = BACKEND_DIR / "logs" / "test"


class ProdConfig(Config):
    name = "prod"
    cors_origins: list[str] = []  # same origin behind the Apache proxy
    secure_cookies = True

    def __init__(self) -> None:
        super().__init__()
        for var in ("DB_PASSWORD", "SECRET_KEY"):
            if not os.getenv(var):
                raise RuntimeError(f"{var} must be set when APP_ENV=prod")


_CONFIGS = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}


@lru_cache
def get_config() -> Config:
    env = os.getenv("APP_ENV", "dev")
    if env not in _CONFIGS:
        raise RuntimeError(f"APP_ENV must be one of {sorted(_CONFIGS)}, got {env!r}")
    return _CONFIGS[env]()
