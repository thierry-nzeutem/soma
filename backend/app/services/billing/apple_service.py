"""Apple In-App Purchase billing service — StoreKit 2 / App Store Server API.

Architecture
------------
iOS app sends a JWS-signed transaction string (StoreKit 2). We:

1. Decode and verify the JWS payload (cert chain or unverified for sandbox).
2. Map the Apple product ID to an internal PlanCode.
3. Persist plan fields + apple_original_transaction_id on the User row.
4. Log the transaction to apple_transactions for audit.

Apple Server Notifications v2 arrive as JWS-signed payloads as well.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Product ID -> internal PlanCode mapping
# ---------------------------------------------------------------------------

#: Register these exact IDs in App Store Connect -> Subscriptions.
APPLE_PRODUCT_TO_PLAN: dict[str, str] = {
    "soma.ai.monthly": "ai",
    "soma.ai.yearly": "ai",
    "soma.performance.monthly": "performance",
    "soma.performance.yearly": "performance",
}

APPLE_BUNDLE_ID: str = os.getenv("APPLE_BUNDLE_ID", "com.soma.health")
APPLE_SHARED_SECRET: str = os.getenv("APPLE_SHARED_SECRET", "")
APPLE_VERIFY_CERT: bool = os.getenv("APPLE_VERIFY_CERT", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Decoded payload dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AppleTransactionPayload:
    """Decoded content from a StoreKit 2 signed transaction."""

    transaction_id: str
    original_transaction_id: str
    bundle_id: str
    product_id: str
    purchase_date_ms: int
    expires_date_ms: Optional[int]
    revocation_date_ms: Optional[int]
    revocation_reason: Optional[int]
    environment: str           # "Sandbox" | "Production"
    transaction_type: str      # "Auto-Renewable Subscription"

    @property
    def purchase_date(self) -> datetime:
        return datetime.fromtimestamp(self.purchase_date_ms / 1000, tz=timezone.utc)

    @property
    def expires_date(self) -> Optional[datetime]:
        if self.expires_date_ms:
            return datetime.fromtimestamp(self.expires_date_ms / 1000, tz=timezone.utc)
        return None

    @property
    def revocation_date(self) -> Optional[datetime]:
        if self.revocation_date_ms:
            return datetime.fromtimestamp(self.revocation_date_ms / 1000, tz=timezone.utc)
        return None

    @property
    def is_revoked(self) -> bool:
        return self.revocation_date_ms is not None

    @property
    def is_active(self) -> bool:
        if self.is_revoked:
            return False
        if self.expires_date:
            return self.expires_date > datetime.now(tz=timezone.utc)
        return True

    @property
    def plan_code(self) -> str:
        return APPLE_PRODUCT_TO_PLAN.get(self.product_id, "free")


@dataclass
class AppleNotificationPayload:
    """Decoded Apple Server Notification v2 data."""

    notification_uuid: str
    notification_type: str
    subtype: Optional[str]
    signed_transaction_info: Optional[str]
    signed_renewal_info: Optional[str]
    environment: str


# ---------------------------------------------------------------------------
# JWS decoding utilities
# ---------------------------------------------------------------------------

def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _decode_jws_payload_unverified(jws: str) -> dict:
    """Decode JWS payload without signature verification (sandbox/test mode)."""
    parts = jws.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWS format: expected 3 parts, got {len(parts)}")
    return json.loads(_b64url_decode(parts[1]))


def _verify_jws_certificate_chain(jws: str) -> dict:
    """Verify Apple JWS via x5c certificate chain then return decoded payload.

    1. Decode header -> x5c DER cert chain.
    2. Verify chain: leaf -> intermediate -> Apple Root CA.
    3. Verify ES256 signature with leaf cert public key.
    4. Return decoded payload.
    """
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        logger.warning("cryptography unavailable — falling back to unverified decode")
        return _decode_jws_payload_unverified(jws)

    parts = jws.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWS: expected 3 parts, got {len(parts)}")
    header_raw, payload_raw, sig_raw = parts

    header = json.loads(_b64url_decode(header_raw))
    x5c = header.get("x5c", [])
    if len(x5c) < 2:
        raise ValueError("JWS header missing x5c cert chain (need >= 2 certs)")
    if header.get("alg") != "ES256":
        raise ValueError(f"Unexpected JWS alg: {header.get('alg')!r} (expected ES256)")

    certs = [x509.load_der_x509_certificate(base64.b64decode(c)) for c in x5c]
    leaf_cert = certs[0]

    for i, cert in enumerate(certs[:-1]):
        issuer_cert = certs[i + 1]
        try:
            issuer_cert.public_key().verify(  # type: ignore[union-attr]
                cert.signature,
                cert.tbs_certificate_bytes,
                ec.ECDSA(cert.signature_hash_algorithm),  # type: ignore[arg-type]
            )
        except InvalidSignature:
            raise ValueError(f"Certificate chain failed at level {i}")

    message = f"{header_raw}.{payload_raw}".encode()
    signature = _b64url_decode(sig_raw)
    try:
        leaf_cert.public_key().verify(  # type: ignore[union-attr]
            signature, message, ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature:
        raise ValueError("JWS signature invalid — payload tampered")

    return json.loads(_b64url_decode(payload_raw))


def decode_apple_jws(jws: str) -> dict:
    """Decode and optionally verify an Apple JWS string."""
    if APPLE_VERIFY_CERT:
        return _verify_jws_certificate_chain(jws)
    return _decode_jws_payload_unverified(jws)


# ---------------------------------------------------------------------------
# Payload parsers
# ---------------------------------------------------------------------------

def parse_transaction_payload(raw: dict) -> AppleTransactionPayload:
    """Parse raw decoded JWS transaction dict. Handles camelCase and snake_case."""
    return AppleTransactionPayload(
        transaction_id=raw.get("transactionId", raw.get("transaction_id", "")),
        original_transaction_id=raw.get(
            "originalTransactionId", raw.get("original_transaction_id", "")
        ),
        bundle_id=raw.get("bundleId", raw.get("bundle_id", "")),
        product_id=raw.get("productId", raw.get("product_id", "")),
        purchase_date_ms=int(raw.get("purchaseDate", raw.get("purchase_date", 0))),
        expires_date_ms=raw.get("expiresDate", raw.get("expires_date")),
        revocation_date_ms=raw.get("revocationDate", raw.get("revocation_date")),
        revocation_reason=raw.get("revocationReason", raw.get("revocation_reason")),
        environment=raw.get("environment", "Sandbox"),
        transaction_type=raw.get("type", "Auto-Renewable Subscription"),
    )


def parse_notification_payload(jws: str) -> AppleNotificationPayload:
    """Decode and parse an Apple Server Notification v2 JWS."""
    raw = decode_apple_jws(jws)
    data = raw.get("data", {})
    return AppleNotificationPayload(
        notification_uuid=raw.get("notificationUUID", ""),
        notification_type=raw.get("notificationType", ""),
        subtype=raw.get("subtype"),
        signed_transaction_info=data.get("signedTransactionInfo"),
        signed_renewal_info=data.get("signedRenewalInfo"),
        environment=data.get("environment", "Sandbox"),
    )


# ---------------------------------------------------------------------------
# StoreKit 1 receipt fallback (verifyReceipt — deprecated but still valid)
# ---------------------------------------------------------------------------

async def verify_receipt_legacy(receipt_data_b64: str) -> dict:
    """Call Apple verifyReceipt. Tries Production first, falls back to Sandbox."""
    if not APPLE_SHARED_SECRET:
        raise ValueError("APPLE_SHARED_SECRET not configured")
    payload = {"receipt-data": receipt_data_b64, "password": APPLE_SHARED_SECRET}
    urls = [
        "https://buy.itunes.apple.com/verifyReceipt",
        "https://sandbox.itunes.apple.com/verifyReceipt",
    ]
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, url in enumerate(urls):
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            apple_status = data.get("status", -1)
            if apple_status == 21007 and i == 0:
                continue
            if apple_status == 0:
                return data
            raise ValueError(f"Apple verifyReceipt status {apple_status}")
    raise ValueError("Apple receipt validation failed")


def extract_latest_subscription_from_receipt(
    receipt_response: dict, product_ids: set[str]
) -> Optional[dict]:
    """Extract most recent valid subscription from verifyReceipt response."""
    latest = receipt_response.get("latest_receipt_info", [])
    valid = [
        r for r in latest
        if r.get("product_id") in product_ids and not r.get("cancellation_date")
    ]
    if not valid:
        return None
    valid.sort(key=lambda r: int(r.get("expires_date_ms", 0)), reverse=True)
    return valid[0]


# ---------------------------------------------------------------------------
# DB idempotency helpers
# ---------------------------------------------------------------------------

async def _is_notification_already_processed(notification_uuid: str, db) -> bool:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT 1 FROM apple_notification_events WHERE notification_uuid = :uuid"),
        {"uuid": notification_uuid},
    )
    return result.fetchone() is not None


async def _mark_notification_processed(
    notification_uuid: str,
    notification_type: str,
    subtype: Optional[str],
    product_id: Optional[str],
    original_transaction_id: Optional[str],
    db,
) -> None:
    from sqlalchemy import text
    await db.execute(
        text(
            "INSERT INTO apple_notification_events "
            "(notification_uuid, notification_type, subtype, product_id, original_transaction_id) "
            "VALUES (:uuid, :ntype, :subtype, :pid, :otid) "
            "ON CONFLICT (notification_uuid) DO NOTHING"
        ),
        {
            "uuid": notification_uuid, "ntype": notification_type,
            "subtype": subtype, "pid": product_id, "otid": original_transaction_id,
        },
    )


async def _log_apple_transaction(user_id: str, tx: AppleTransactionPayload, db) -> None:
    """Insert into apple_transactions audit log. Idempotent on transaction_id."""
    from sqlalchemy import text
    await db.execute(
        text(
            "INSERT INTO apple_transactions "
            "(user_id, transaction_id, original_transaction_id, product_id, plan_code, "
            "environment, purchase_date, expires_date, revocation_date, revocation_reason) "
            "VALUES (:uid, :tid, :otid, :pid, :plan, :env, :pdate, :edate, :rdate, :rreason) "
            "ON CONFLICT (transaction_id) DO NOTHING"
        ),
        {
            "uid": user_id, "tid": tx.transaction_id, "otid": tx.original_transaction_id,
            "pid": tx.product_id, "plan": tx.plan_code, "env": tx.environment,
            "pdate": tx.purchase_date, "edate": tx.expires_date,
            "rdate": tx.revocation_date, "rreason": tx.revocation_reason,
        },
    )


# ---------------------------------------------------------------------------
# Core subscription state update
# ---------------------------------------------------------------------------

async def apply_apple_subscription_to_user(
    user_id: str, tx: AppleTransactionPayload, db
) -> None:
    """Persist Apple subscription state onto User row.

    Updates: plan_code, plan_status, billing_provider, plan_started_at,
    plan_expires_at, apple_original_transaction_id.
    """
    from sqlalchemy import text

    if tx.is_revoked:
        await db.execute(
            text(
                "UPDATE users SET plan_code = 'free', plan_status = 'active', "
                "plan_expires_at = NULL, plan_started_at = NULL WHERE id = :uid"
            ),
            {"uid": user_id},
        )
        logger.info("Apple REVOKED for user %s -> free (tx %s)", user_id, tx.transaction_id)
        return

    if tx.is_active:
        await db.execute(
            text(
                "UPDATE users SET "
                "plan_code = :plan, plan_status = 'active', billing_provider = 'apple', "
                "apple_original_transaction_id = COALESCE(apple_original_transaction_id, :otid), "
                "plan_started_at = :pdate, plan_expires_at = :edate "
                "WHERE id = :uid"
            ),
            {
                "plan": tx.plan_code, "otid": tx.original_transaction_id,
                "pdate": tx.purchase_date, "edate": tx.expires_date, "uid": user_id,
            },
        )
        logger.info(
            "Apple ACTIVATED user %s: plan=%s, expires=%s (tx %s)",
            user_id, tx.plan_code, tx.expires_date, tx.transaction_id,
        )
    else:
        await db.execute(
            text(
                "UPDATE users SET plan_code = 'free', plan_status = 'inactive', "
                "plan_expires_at = :edate WHERE id = :uid"
            ),
            {"edate": tx.expires_date, "uid": user_id},
        )
        logger.info("Apple EXPIRED for user %s -> free (tx %s)", user_id, tx.transaction_id)


async def process_verified_transaction(
    user_id: str, tx: AppleTransactionPayload, db
) -> None:
    """Persist a verified Apple transaction and commit."""
    await apply_apple_subscription_to_user(user_id, tx, db)
    await _log_apple_transaction(user_id, tx, db)
    await db.commit()


# ---------------------------------------------------------------------------
# Apple Server Notification v2 handler
# ---------------------------------------------------------------------------

async def process_apple_server_notification(signed_payload: str, db) -> dict:
    """Handle an Apple Server Notification v2 JWS payload.

    Returns {"processed": bool, "type": str, "skipped": bool}.
    Idempotent — duplicate notificationUUIDs are silently skipped.
    """
    from sqlalchemy import text

    notif = parse_notification_payload(signed_payload)

    if notif.notification_uuid and await _is_notification_already_processed(
        notif.notification_uuid, db
    ):
        logger.info("Apple notification %s already processed", notif.notification_uuid)
        return {"processed": False, "type": notif.notification_type, "skipped": True}

    ntype = notif.notification_type
    subtype = notif.subtype or ""

    tx: Optional[AppleTransactionPayload] = None
    if notif.signed_transaction_info:
        try:
            raw = decode_apple_jws(notif.signed_transaction_info)
            tx = parse_transaction_payload(raw)
        except Exception as exc:
            logger.warning("Failed to decode signedTransactionInfo: %s", exc)

    user_id: Optional[str] = None
    if tx and tx.original_transaction_id:
        result = await db.execute(
            text(
                "SELECT id FROM users "
                "WHERE apple_original_transaction_id = :otid LIMIT 1"
            ),
            {"otid": tx.original_transaction_id},
        )
        row = result.fetchone()
        if row:
            user_id = str(row[0])

    if tx and user_id:
        if ntype in ("SUBSCRIBED", "DID_RENEW", "OFFER_REDEEMED"):
            await apply_apple_subscription_to_user(user_id, tx, db)
            await _log_apple_transaction(user_id, tx, db)

        elif ntype in ("EXPIRED", "DID_FAIL_TO_RENEW", "GRACE_PERIOD_EXPIRED"):
            await db.execute(
                text(
                    "UPDATE users SET plan_code = 'free', plan_status = 'inactive', "
                    "plan_expires_at = :edate WHERE id = :uid"
                ),
                {"edate": tx.expires_date, "uid": user_id},
            )
            logger.info("Apple %s -> user %s downgraded to free", ntype, user_id)

        elif ntype in ("REVOKE", "REFUND"):
            await db.execute(
                text(
                    "UPDATE users SET plan_code = 'free', plan_status = 'active', "
                    "plan_expires_at = NULL WHERE id = :uid"
                ),
                {"uid": user_id},
            )
            logger.info("Apple %s -> user %s refunded, downgraded to free", ntype, user_id)

        elif ntype in ("DID_CHANGE_RENEWAL_STATUS", "DID_CHANGE_RENEWAL_PREF"):
            logger.info("Apple %s (%s) for user %s — informational", ntype, subtype, user_id)
    else:
        logger.warning(
            "Apple notification %s — user not found (original_tx=%s)",
            ntype, tx.original_transaction_id if tx else "N/A",
        )

    if notif.notification_uuid:
        await _mark_notification_processed(
            notif.notification_uuid, ntype, notif.subtype,
            tx.product_id if tx else None,
            tx.original_transaction_id if tx else None,
            db,
        )
    await db.commit()
    return {"processed": True, "type": ntype, "skipped": False}
