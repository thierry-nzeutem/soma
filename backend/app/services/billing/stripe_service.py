"""Service de gestion des abonnements Stripe avec idempotence."""
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)

import os
STRIPE_PRICE_TO_PLAN = {
    os.getenv("STRIPE_PRICE_AI_MONTHLY", "price_ai_monthly"): "ai",
    os.getenv("STRIPE_PRICE_AI_YEARLY", "price_ai_yearly"): "ai",
    os.getenv("STRIPE_PRICE_PERF_MONTHLY", "price_perf_monthly"): "performance",
    os.getenv("STRIPE_PRICE_PERF_YEARLY", "price_perf_yearly"): "performance",
}


async def _is_already_processed(event_id: str, db) -> bool:
    """Verifie si un event Stripe a deja ete traite (idempotence)."""
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT 1 FROM stripe_webhook_events WHERE event_id = :eid"),
        {"eid": event_id},
    )
    return result.fetchone() is not None


async def _mark_as_processed(event_id: str, event_type: str, db) -> None:
    """Enregistre l event comme traite pour eviter le retraitement."""
    from sqlalchemy import text
    await db.execute(
        text(
            "INSERT INTO stripe_webhook_events (event_id, event_type) "
            "VALUES (:eid, :etype) ON CONFLICT (event_id) DO NOTHING"
        ),
        {"eid": event_id, "etype": event_type},
    )


def _plan_from_subscription(subscription: dict) -> str:
    items = subscription.get("items", {}).get("data", [])
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id in STRIPE_PRICE_TO_PLAN:
            return STRIPE_PRICE_TO_PLAN[price_id]
    return "ai"


async def handle_checkout_completed(event: dict, db) -> None:
    """checkout.session.completed -> activer le plan (idempotent)."""
    from sqlalchemy import update
    from app.models.user import User

    event_id = event.get("id", "")
    if await _is_already_processed(event_id, db):
        logger.info(f"Webhook {event_id} already processed, skipping")
        return

    session = event.get("data", {}).get("object", {})
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    metadata = session.get("metadata", {})
    user_id = metadata.get("user_id")
    plan_code = metadata.get("plan_code", "ai")

    if not user_id:
        logger.warning("checkout.session.completed: no user_id in metadata")
        await _mark_as_processed(event_id, event.get("type", ""), db)
        return

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            plan_code=plan_code,
            plan_status="active",
            billing_provider="stripe",
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan_started_at=datetime.now(timezone.utc),
            plan_expires_at=None,
        )
    )
    await _mark_as_processed(event_id, event.get("type", ""), db)
    await db.commit()
    logger.info(f"User {user_id} upgraded to plan '{plan_code}' via checkout (event {event_id})")


async def handle_subscription_updated(event: dict, db) -> None:
    """customer.subscription.updated -> sync statut (idempotent)."""
    from sqlalchemy import update
    from app.models.user import User

    event_id = event.get("id", "")
    if await _is_already_processed(event_id, db):
        logger.info(f"Webhook {event_id} already processed, skipping")
        return

    subscription = event.get("data", {}).get("object", {})
    customer_id = subscription.get("customer")
    stripe_status = subscription.get("status")
    plan_code = _plan_from_subscription(subscription)

    if stripe_status in ("active", "trialing"):
        soma_status = "active"
    elif stripe_status == "past_due":
        soma_status = "past_due"
    else:
        soma_status = "inactive"

    current_period_end = subscription.get("current_period_end")
    expires_at = None
    if current_period_end and soma_status != "active":
        expires_at = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

    update_values = {
        "plan_status": soma_status,
        "stripe_subscription_id": subscription.get("id"),
    }
    if soma_status != "active":
        update_values["plan_code"] = "free"
        update_values["plan_expires_at"] = expires_at
    else:
        update_values["plan_code"] = plan_code
        update_values["plan_expires_at"] = None

    await db.execute(
        update(User)
        .where(User.stripe_customer_id == customer_id)
        .values(**update_values)
    )
    await _mark_as_processed(event_id, event.get("type", ""), db)
    await db.commit()
    logger.info(f"Subscription updated for customer {customer_id}: status={soma_status}, plan={plan_code} (event {event_id})")


async def handle_subscription_deleted(event: dict, db) -> None:
    """customer.subscription.deleted -> retour immediat au plan free (idempotent)."""
    from sqlalchemy import update
    from app.models.user import User

    event_id = event.get("id", "")
    if await _is_already_processed(event_id, db):
        logger.info(f"Webhook {event_id} already processed, skipping")
        return

    subscription = event.get("data", {}).get("object", {})
    customer_id = subscription.get("customer")

    await db.execute(
        update(User)
        .where(User.stripe_customer_id == customer_id)
        .values(
            plan_code="free",
            plan_status="active",
            stripe_subscription_id=None,
            plan_started_at=None,
            plan_expires_at=None,
        )
    )
    await _mark_as_processed(event_id, event.get("type", ""), db)
    await db.commit()
    logger.info(f"Subscription deleted for customer {customer_id}: downgraded to free (event {event_id})")


async def handle_invoice_failed(event: dict, db) -> None:
    """invoice.payment_failed -> plan_status=past_due -> effective plan = FREE (idempotent)."""
    from sqlalchemy import update
    from app.models.user import User

    event_id = event.get("id", "")
    if await _is_already_processed(event_id, db):
        logger.info(f"Webhook {event_id} already processed, skipping")
        return

    invoice = event.get("data", {}).get("object", {})
    customer_id = invoice.get("customer")

    await db.execute(
        update(User)
        .where(User.stripe_customer_id == customer_id)
        .values(plan_status="past_due")
    )
    await _mark_as_processed(event_id, event.get("type", ""), db)
    await db.commit()
    logger.warning(f"Payment failed for customer {customer_id}: plan_status=past_due (event {event_id})")
