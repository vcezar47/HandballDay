from functools import lru_cache

from ..config import get_config
from ..errors import PaymentError
from .payment import CheckoutSession, FakeGateway, Line, PaymentEvent, PaymentGateway, StripeGateway


@lru_cache
def _stripe(secret_key: str, webhook_secret: str) -> StripeGateway:
    return StripeGateway(secret_key, webhook_secret)


def get_gateway() -> PaymentGateway:
    """FastAPI dependency; tests replace it with a FakeGateway."""
    cfg = get_config()
    if not (cfg.stripe_secret_key and cfg.stripe_webhook_secret):
        raise PaymentError("Payments are not configured on this server")
    return _stripe(cfg.stripe_secret_key, cfg.stripe_webhook_secret)


__all__ = ["CheckoutSession", "FakeGateway", "Line", "PaymentEvent", "PaymentGateway", "StripeGateway", "get_gateway"]
