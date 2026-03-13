"""Endpoints de facturation Stripe.

Apple App Store compliance
--------------------------
  POST /billing/checkout  -- BLOCKED for iOS clients (HTTP 451).
  GET  /billing/portal    -- BLOCKED for iOS clients (HTTP 451).
  POST /billing/webhook   -- always open (Stripe server-to-server).

The client declares its platform via the X-Client-Platform HTTP header
(injected by Flutter ApiClient). Any value of "ios" is rejected
server-side as a second line of defence against billing regressions.
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.billing import stripe_service

logger = logging.getLogger(__name__)

billing_router = APIRouter(prefix="/billing", tags=["Billing"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = os.getenv(
    "STRIPE_SUCCESS_URL", "http://localhost:3001/dashboard?upgraded=true"
)
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "http://localhost:3001/dashboard")

PLAN_PRICES = {
    "ai": {
        "monthly": os.getenv("STRIPE_PRICE_AI_MONTHLY", ""),
        "yearly": os.getenv("STRIPE_PRICE_AI_YEARLY", ""),
    },
    "performance": {
        "monthly": os.getenv("STRIPE_PRICE_PERF_MONTHLY", ""),
        "yearly": os.getenv("STRIPE_PRICE_PERF_YEARLY", ""),
    },
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    plan_code: str
    billing_interval: str = "monthly"


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    portal_url: str


# ---------------------------------------------------------------------------
# Platform guard
# ---------------------------------------------------------------------------

def _reject_ios(x_client_platform: Optional[str], endpoint: str) -> None:
    """Raise HTTP 451 if the request comes from an iOS client.

    HTTP 451 Unavailable For Legal Reasons is the correct code for content
    that cannot be served due to legal or policy obligations.
    """
    platform = (x_client_platform or "").strip().lower()
    if platform == "ios":
        logger.warning(
            "Blocked iOS billing request to %s -- platform header: %s",
            endpoint, x_client_platform,
        )
        raise HTTPException(
            status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
            detail={
                "error": "ios_billing_not_supported",
                "message": (
                    "Stripe checkout and billing portal are not available "
                    "from iOS App Store builds. Please use the web app to "
                    "manage your subscription."
                ),
                "platform": platform,
                "endpoint": endpoint,
            },
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@billing_router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    x_client_platform: Optional[str] = Header(default=None),
):
    """Cree une session Stripe Checkout. Blocked for iOS clients."""
    _reject_ios(x_client_platform, "POST /billing/checkout")

    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Billing not configured")

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        price_id = PLAN_PRICES.get(payload.plan_code, {}).get(payload.billing_interval, "")
        if not price_id:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown plan or interval: {payload.plan_code}/{payload.billing_interval}",
            )

        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email or "",
                metadata={"user_id": str(current_user.id), "username": current_user.username},
            )
            customer_id = customer.id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=STRIPE_SUCCESS_URL,
            cancel_url=STRIPE_CANCEL_URL,
            metadata={"user_id": str(current_user.id), "plan_code": payload.plan_code},
            subscription_data={"metadata": {"user_id": str(current_user.id)}},
        )

        return CheckoutResponse(checkout_url=session.url, session_id=session.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Stripe checkout error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@billing_router.get("/portal", response_model=PortalResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    x_client_platform: Optional[str] = Header(default=None),
):
    """Cree une session Stripe Customer Portal. Blocked for iOS clients."""
    _reject_ios(x_client_platform, "GET /billing/portal")

    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Billing not configured")
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=STRIPE_CANCEL_URL,
        )
        return PortalResponse(portal_url=session.url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Stripe portal error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@billing_router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Webhook Stripe -- source de verite pour les plans.

    Server-to-server endpoint (Stripe -> backend). Does NOT receive
    X-Client-Platform and is intentionally NOT blocked by _reject_ios.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            logger.error("Webhook signature verification failed: %s", e)
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")
    logger.info("Stripe webhook received: %s", event_type)

    try:
        if event_type == "checkout.session.completed":
            await stripe_service.handle_checkout_completed(event, db)
        elif event_type == "customer.subscription.updated":
            await stripe_service.handle_subscription_updated(event, db)
        elif event_type in ("customer.subscription.deleted", "customer.subscription.canceled"):
            await stripe_service.handle_subscription_deleted(event, db)
        elif event_type == "invoice.payment_failed":
            await stripe_service.handle_invoice_failed(event, db)
        elif event_type == "invoice.paid":
            pass
        else:
            logger.debug("Unhandled Stripe event: %s", event_type)
    except Exception as e:
        logger.error("Error processing webhook %s: %s", event_type, e)
        raise HTTPException(status_code=500, detail="Webhook processing error")

    return {"received": True}
