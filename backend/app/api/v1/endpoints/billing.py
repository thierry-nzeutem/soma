"""Billing endpoints — Stripe (Android/Web) + Apple IAP (iOS).

Platform routing
----------------
  POST /billing/checkout         Stripe only — BLOCKED for iOS (HTTP 451)
  GET  /billing/portal           Stripe only — BLOCKED for iOS (HTTP 451)
  POST /billing/webhook          Stripe server-to-server — never blocked

  POST /billing/apple/verify     Apple only — requires iOS platform header
  POST /billing/apple/restore    Apple only — requires iOS platform header
  POST /billing/apple/notifications  Apple server-to-server — never blocked
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.entitlements import get_user_features, get_effective_plan
from app.models.user import User
from app.services.billing import stripe_service
from app.services.billing import apple_service

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


class AppleVerifyRequest(BaseModel):
    """iOS StoreKit 2: signed JWS transaction string from purchaseDetails.verificationData."""
    transaction_jws: str
    product_id: str


class AppleRestoreRequest(BaseModel):
    """iOS restore purchases: list of signed JWS transaction strings."""
    transaction_jws_list: list[str]


class EntitlementsResponse(BaseModel):
    plan_code: str
    effective_plan: str
    plan_status: str
    features: list[str]
    billing_provider: Optional[str]


# ---------------------------------------------------------------------------
# Platform guards
# ---------------------------------------------------------------------------

def _reject_ios(x_client_platform: Optional[str], endpoint: str) -> None:
    """Raise HTTP 451 if the request comes from an iOS client.

    Used to block Stripe endpoints from iOS App Store builds.
    HTTP 451 = Unavailable For Legal Reasons.
    """
    platform = (x_client_platform or "").strip().lower()
    if platform == "ios":
        logger.warning(
            "Blocked iOS Stripe request to %s -- platform: %s",
            endpoint, x_client_platform,
        )
        raise HTTPException(
            status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
            detail={
                "error": "ios_billing_not_supported",
                "message": (
                    "Stripe checkout and billing portal are not available "
                    "from iOS App Store builds. Use Apple In-App Purchase instead."
                ),
                "platform": platform,
                "endpoint": endpoint,
            },
        )


def _require_ios_or_internal(x_client_platform: Optional[str], endpoint: str) -> None:
    """Reject non-iOS clients from Apple billing endpoints.

    Apple IAP verification must only come from iOS clients. This prevents
    Android or Web clients from hitting Apple endpoints accidentally.
    Internal server-to-server calls (no header) are allowed for restore.
    """
    platform = (x_client_platform or "").strip().lower()
    if platform not in ("ios", ""):
        logger.warning(
            "Non-iOS client attempted Apple billing endpoint %s (platform=%s)",
            endpoint, x_client_platform,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "apple_billing_ios_only",
                "message": "Apple In-App Purchase endpoints are only for iOS clients.",
                "platform": platform,
                "endpoint": endpoint,
            },
        )


def _build_entitlements_response(user: User) -> EntitlementsResponse:
    return EntitlementsResponse(
        plan_code=user.plan_code,
        effective_plan=get_effective_plan(user).value,
        plan_status=user.plan_status,
        features=get_user_features(user),
        billing_provider=user.billing_provider,
    )


# ---------------------------------------------------------------------------
# Stripe endpoints (Android + Web)
# ---------------------------------------------------------------------------

@billing_router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    x_client_platform: Optional[str] = Header(default=None),
):
    """Create a Stripe Checkout session. Blocked for iOS clients (HTTP 451)."""
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
    """Create a Stripe Customer Portal session. Blocked for iOS clients (HTTP 451)."""
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
    """Stripe webhook — source of truth for Stripe-based subscriptions.

    Server-to-server (Stripe -> backend). Not blocked by platform guard.
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


# ---------------------------------------------------------------------------
# Apple IAP endpoints (iOS only)
# ---------------------------------------------------------------------------

@billing_router.post("/apple/verify", response_model=EntitlementsResponse)
async def apple_verify_purchase(
    payload: AppleVerifyRequest,
    current_user: User = Depends(get_current_user),
    x_client_platform: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Verify an Apple StoreKit 2 purchase and activate the user's plan.

    Accepts a JWS-signed transaction string from purchaseDetails.verificationData
    (iOS in_app_purchase package). Decodes and verifies the JWS, maps the
    product ID to an internal plan code, and activates the subscription.

    Returns the updated entitlements payload for immediate UI refresh.
    iOS-only endpoint (rejects Android and Web clients).
    """
    _require_ios_or_internal(x_client_platform, "POST /billing/apple/verify")

    try:
        raw = apple_service.decode_apple_jws(payload.transaction_jws)
        tx = apple_service.parse_transaction_payload(raw)
    except Exception as e:
        logger.error("Apple JWS decode error: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid Apple transaction JWS: {e}")

    # Validate bundle ID
    if tx.bundle_id and tx.bundle_id != apple_service.APPLE_BUNDLE_ID:
        logger.warning(
            "Apple JWS bundle ID mismatch: got %s, expected %s",
            tx.bundle_id, apple_service.APPLE_BUNDLE_ID,
        )
        raise HTTPException(status_code=400, detail="Bundle ID mismatch")

    # Validate product ID
    if tx.product_id not in apple_service.APPLE_PRODUCT_TO_PLAN:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown Apple product ID: {tx.product_id!r}",
        )

    if not tx.is_active:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "transaction_not_active",
                "message": "The provided Apple transaction is expired or revoked.",
                "product_id": tx.product_id,
                "expires_date": tx.expires_date.isoformat() if tx.expires_date else None,
            },
        )

    await apple_service.process_verified_transaction(str(current_user.id), tx, db)

    # Reload user to get updated plan
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :uid"), {"uid": str(current_user.id)}
    )
    updated_row = result.fetchone()

    # Build response from updated row (simpler than re-querying full ORM object)
    logger.info(
        "Apple purchase verified for user %s: product=%s, plan=%s, env=%s",
        current_user.id, tx.product_id, tx.plan_code, tx.environment,
    )

    # Refresh current_user fields for response building
    current_user.plan_code = tx.plan_code
    current_user.plan_status = "active"
    current_user.billing_provider = "apple"
    current_user.plan_expires_at = tx.expires_date
    current_user.plan_started_at = tx.purchase_date

    return _build_entitlements_response(current_user)


@billing_router.post("/apple/restore", response_model=EntitlementsResponse)
async def apple_restore_purchases(
    payload: AppleRestoreRequest,
    current_user: User = Depends(get_current_user),
    x_client_platform: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Restore Apple IAP purchases from a list of JWS transactions.

    Called when the user taps 'Restore Purchases'. Accepts all JWS transactions
    from StoreKit's restorePurchases() result, verifies each one, and activates
    the highest-tier plan found.

    Returns the updated entitlements payload after restoration.
    """
    _require_ios_or_internal(x_client_platform, "POST /billing/apple/restore")

    if not payload.transaction_jws_list:
        raise HTTPException(status_code=400, detail="No transactions provided for restore")

    best_tx: Optional[apple_service.AppleTransactionPayload] = None

    plan_rank = {"free": 0, "ai": 1, "performance": 2}

    for jws in payload.transaction_jws_list:
        try:
            raw = apple_service.decode_apple_jws(jws)
            tx = apple_service.parse_transaction_payload(raw)

            if not tx.is_active:
                continue
            if tx.product_id not in apple_service.APPLE_PRODUCT_TO_PLAN:
                continue

            if best_tx is None:
                best_tx = tx
            elif plan_rank.get(tx.plan_code, 0) > plan_rank.get(best_tx.plan_code, 0):
                best_tx = tx
            elif (
                plan_rank.get(tx.plan_code, 0) == plan_rank.get(best_tx.plan_code, 0)
                and tx.expires_date
                and best_tx.expires_date
                and tx.expires_date > best_tx.expires_date
            ):
                best_tx = tx

        except Exception as exc:
            logger.warning("Skipping invalid JWS during restore: %s", exc)
            continue

    if best_tx is None:
        logger.info(
            "Restore purchases for user %s: no active Apple subscriptions found",
            current_user.id,
        )
        current_user.plan_code = "free"
        current_user.plan_status = "active"
        return _build_entitlements_response(current_user)

    await apple_service.process_verified_transaction(str(current_user.id), best_tx, db)

    current_user.plan_code = best_tx.plan_code
    current_user.plan_status = "active"
    current_user.billing_provider = "apple"
    current_user.plan_expires_at = best_tx.expires_date
    current_user.plan_started_at = best_tx.purchase_date

    logger.info(
        "Restore purchases completed for user %s: plan=%s, expires=%s",
        current_user.id, best_tx.plan_code, best_tx.expires_date,
    )
    return _build_entitlements_response(current_user)


@billing_router.post("/apple/notifications", status_code=200)
async def apple_server_notification(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Apple App Store Server Notifications v2 webhook.

    Server-to-server endpoint (Apple -> backend). Not blocked by platform guard.
    Apple POSTs a JWS-signed payload for subscription lifecycle events:
    SUBSCRIBED, DID_RENEW, EXPIRED, DID_FAIL_TO_RENEW, REVOKE, REFUND, etc.
    """
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty notification payload")

    try:
        import json
        data = json.loads(body)
        signed_payload = data.get("signedPayload", "")
        if not signed_payload:
            raise ValueError("Missing signedPayload field")
    except Exception as e:
        logger.error("Apple notification parse error: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid notification format: {e}")

    try:
        result = await apple_service.process_apple_server_notification(signed_payload, db)
        logger.info("Apple notification processed: %s", result)
        return {"received": True, **result}
    except Exception as e:
        logger.error("Apple notification processing error: %s", e)
        raise HTTPException(status_code=500, detail="Notification processing error")
