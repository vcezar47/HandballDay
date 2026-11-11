from fastapi import APIRouter

from ..config import get_config

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/config")
def public_config():
    """What the browser needs to know: the Turnstile site key (empty when the CAPTCHA is off)."""
    cfg = get_config()
    return {"turnstile_site_key": cfg.turnstile_site_key if cfg.turnstile_secret_key else ""}
