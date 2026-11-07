"""Payment gateways. Services depend on `PaymentGateway`, never on Stripe directly (barem 3.02)."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import stripe

from ..errors import AppValidationError, PaymentError


@dataclass
class Line:
    name: str
    unit_bani: int
    quantity: int


@dataclass
class CheckoutSession:
    id: str
    url: str


@dataclass
class PaymentEvent:
    kind: str  # "paid" or "expired"
    session_id: str
    amount_bani: int | None = None


class PaymentGateway(ABC):
    name: str

    @abstractmethod
    def create_checkout(
        self, order_id: int, lines: list[Line], success_url: str, cancel_url: str, expires_at: datetime
    ) -> CheckoutSession:
        """Start a hosted payment page; raises PaymentError if the provider refuses."""

    @abstractmethod
    def read_event(self, payload: bytes, signature: str | None) -> PaymentEvent | None:
        """Verify a webhook call and translate it. Returns None for events we do not act on."""


class StripeGateway(PaymentGateway):
    name = "stripe"

    def __init__(self, secret_key: str, webhook_secret: str) -> None:
        self.client = stripe.StripeClient(secret_key)
        self.webhook_secret = webhook_secret

    def create_checkout(self, order_id, lines, success_url, cancel_url, expires_at):
        try:
            session = self.client.checkout.sessions.create(
                params={
                    "mode": "payment",
                    "client_reference_id": str(order_id),
                    "line_items": [
                        {
                            "quantity": line.quantity,
                            "price_data": {
                                "currency": "ron",
                                "unit_amount": line.unit_bani,
                                "product_data": {"name": line.name},
                            },
                        }
                        for line in lines
                    ],
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "expires_at": int(expires_at.timestamp()),
                }
            )
        except stripe.StripeError as exc:
            raise PaymentError("Could not start the payment, please try again") from exc
        return CheckoutSession(session.id, session.url)

    def read_event(self, payload, signature):
        try:
            event = stripe.Webhook.construct_event(payload, signature or "", self.webhook_secret)
        except (ValueError, stripe.SignatureVerificationError) as exc:
            raise AppValidationError("Invalid webhook signature") from exc
        obj = event["data"]["object"]
        if event["type"] == "checkout.session.completed" and obj["payment_status"] == "paid":
            return PaymentEvent("paid", obj["id"], obj["amount_total"])
        if event["type"] == "checkout.session.expired":
            return PaymentEvent("expired", obj["id"])
        return None


class FakeGateway(PaymentGateway):
    """For tests: remembers what it was asked and takes JSON events signed with SIGNATURE."""

    name = "fake"
    SIGNATURE = "fake-ok"

    def __init__(self) -> None:
        self.created: list[tuple[str, int, list[Line]]] = []  # (session id, order id, lines)
        self.fail = False

    def create_checkout(self, order_id, lines, success_url, cancel_url, expires_at):
        if self.fail:
            raise PaymentError("Could not start the payment, please try again")
        session_id = f"fake_{len(self.created) + 1}"
        self.created.append((session_id, order_id, lines))
        return CheckoutSession(session_id, f"https://pay.example/{session_id}")

    def read_event(self, payload, signature):
        if signature != self.SIGNATURE:
            raise AppValidationError("Invalid webhook signature")
        data = json.loads(payload)
        return PaymentEvent(data["kind"], data["session_id"], data.get("amount_bani"))
