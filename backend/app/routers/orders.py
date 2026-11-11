from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..limits import STRICT, limiter
from ..gateways import PaymentGateway, get_gateway
from ..models import User
from ..schemas import CheckoutRequest, CheckoutResponse, TicketOut
from ..security.access import current_user
from ..services import OrderService

router = APIRouter(prefix="/api", tags=["orders"])


@router.post("/checkout", response_model=CheckoutResponse)
@limiter.limit(STRICT)
def checkout(
    request: Request, payload: CheckoutRequest, user: User = Depends(current_user), db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
):
    return {"checkout_url": OrderService(db, gateway).checkout(user, payload)}


@router.get("/tickets", response_model=list[TicketOut])
def my_tickets(user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Only the caller's own tickets are ever queried, so there is no id to tamper with.
    return OrderService(db).my_tickets(user)


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db), gateway: PaymentGateway = Depends(get_gateway)):
    # Exempt from CSRF (see security/csrf.py); the signature check is what authenticates Stripe.
    event = gateway.read_event(await request.body(), request.headers.get("stripe-signature"))
    if event is not None:
        service = OrderService(db, gateway)
        if event.kind == "paid":
            service.fulfil(event.session_id, event.amount_bani)
        elif event.kind == "expired":
            service.expire(event.session_id)
    return {"received": True}
