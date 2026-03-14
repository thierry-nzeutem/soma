"""Tests for Apple IAP billing endpoints and apple_service functions.

Tests:
- decode_apple_jws: decode mock JWS payloads
- parse_transaction_payload: field mapping
- POST /billing/apple/verify: iOS-only, valid/invalid transactions
- POST /billing/apple/restore: iOS-only, restore logic
- POST /billing/apple/notifications: server-to-server, idempotent
- Platform guards: Apple endpoints blocked for non-iOS (403)
- Stripe endpoints still blocked for iOS (451)
"""
import base64
import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers — minimal JWS construction (no real Apple signing)
# ---------------------------------------------------------------------------

def _make_jws(payload: dict) -> str:
    """Build a minimal unsigned JWS string (for unit tests only)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "ES256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


def _future_ms(days: int = 30) -> int:
    """Return a timestamp in milliseconds N days from now."""
    dt = datetime.now(tz=timezone.utc) + timedelta(days=days)
    return int(dt.timestamp() * 1000)


def _past_ms(days: int = 1) -> int:
    """Return a timestamp in milliseconds N days ago."""
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days)
    return int(dt.timestamp() * 1000)


VALID_AI_PAYLOAD = {
    "transactionId": "1000000012345678",
    "originalTransactionId": "1000000099999999",
    "bundleId": "com.soma.health",
    "productId": "soma.ai.monthly",
    "purchaseDate": int(datetime.now(tz=timezone.utc).timestamp() * 1000),
    "expiresDate": _future_ms(30),
    "environment": "Sandbox",
    "type": "Auto-Renewable Subscription",
}

EXPIRED_AI_PAYLOAD = {
    **VALID_AI_PAYLOAD,
    "transactionId": "1000000012345679",
    "expiresDate": _past_ms(2),
}

VALID_PERFORMANCE_PAYLOAD = {
    **VALID_AI_PAYLOAD,
    "transactionId": "1000000012345680",
    "originalTransactionId": "1000000099999998",
    "productId": "soma.performance.monthly",
}


# ---------------------------------------------------------------------------
# Unit tests for apple_service functions (no DB, no HTTP)
# ---------------------------------------------------------------------------

class TestDecodeAppleJws:
    def test_decode_valid_jws(self):
        from app.services.billing.apple_service import _decode_jws_payload_unverified
        jws = _make_jws({"test": "value", "num": 42})
        result = _decode_jws_payload_unverified(jws)
        assert result["test"] == "value"
        assert result["num"] == 42

    def test_decode_invalid_jws_raises(self):
        from app.services.billing.apple_service import _decode_jws_payload_unverified
        with pytest.raises(ValueError, match="Invalid JWS"):
            _decode_jws_payload_unverified("not.a.jws.with.extra.parts.here")

    def test_decode_two_part_jws_raises(self):
        from app.services.billing.apple_service import _decode_jws_payload_unverified
        with pytest.raises(ValueError):
            _decode_jws_payload_unverified("header.payload")


class TestParseTransactionPayload:
    def test_parse_valid_ai_monthly(self):
        from app.services.billing.apple_service import parse_transaction_payload
        tx = parse_transaction_payload(VALID_AI_PAYLOAD)
        assert tx.product_id == "soma.ai.monthly"
        assert tx.plan_code == "ai"
        assert tx.environment == "Sandbox"
        assert tx.transaction_id == "1000000012345678"
        assert tx.original_transaction_id == "1000000099999999"
        assert tx.bundle_id == "com.soma.health"

    def test_parse_performance_plan(self):
        from app.services.billing.apple_service import parse_transaction_payload
        tx = parse_transaction_payload(VALID_PERFORMANCE_PAYLOAD)
        assert tx.plan_code == "performance"

    def test_is_active_for_future_expiry(self):
        from app.services.billing.apple_service import parse_transaction_payload
        tx = parse_transaction_payload(VALID_AI_PAYLOAD)
        assert tx.is_active is True
        assert tx.is_revoked is False

    def test_is_not_active_for_past_expiry(self):
        from app.services.billing.apple_service import parse_transaction_payload
        tx = parse_transaction_payload(EXPIRED_AI_PAYLOAD)
        assert tx.is_active is False

    def test_plan_code_unknown_product(self):
        from app.services.billing.apple_service import parse_transaction_payload
        payload = {**VALID_AI_PAYLOAD, "productId": "com.unknown.app.product"}
        tx = parse_transaction_payload(payload)
        assert tx.plan_code == "free"  # Fallback


class TestAppleProductMapping:
    def test_all_products_map_to_plans(self):
        from app.services.billing.apple_service import APPLE_PRODUCT_TO_PLAN
        assert APPLE_PRODUCT_TO_PLAN["soma.ai.monthly"] == "ai"
        assert APPLE_PRODUCT_TO_PLAN["soma.ai.yearly"] == "ai"
        assert APPLE_PRODUCT_TO_PLAN["soma.performance.monthly"] == "performance"
        assert APPLE_PRODUCT_TO_PLAN["soma.performance.yearly"] == "performance"


# ---------------------------------------------------------------------------
# Integration tests — HTTP endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def ios_headers():
    return {"X-Client-Platform": "ios"}


@pytest.fixture
def android_headers():
    return {"X-Client-Platform": "android"}


@pytest.fixture
def no_platform_headers():
    return {}


class TestAppleVerifyEndpoint:
    """POST /billing/apple/verify"""

    @pytest.mark.asyncio
    async def test_verify_blocked_for_android(self, client, android_headers):
        """Android clients must receive 403 from Apple verify endpoint."""
        jws = _make_jws(VALID_AI_PAYLOAD)
        resp = await client.post(
            "/api/v1/billing/apple/verify",
            json={"transaction_jws": jws, "product_id": "soma.ai.monthly"},
            headers=android_headers,
        )
        assert resp.status_code == 403, (
            f"Expected 403 for Android on Apple endpoint, got {resp.status_code}"
        )
        data = resp.json()
        assert data["detail"]["error"] == "apple_billing_ios_only"

    @pytest.mark.asyncio
    async def test_verify_requires_auth(self, client, ios_headers):
        """Unauthenticated requests must receive 401."""
        jws = _make_jws(VALID_AI_PAYLOAD)
        resp = await client.post(
            "/api/v1/billing/apple/verify",
            json={"transaction_jws": jws, "product_id": "soma.ai.monthly"},
            headers=ios_headers,
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_rejects_expired_transaction(self, client, ios_headers):
        """Expired Apple transactions must return 422."""
        jws = _make_jws(EXPIRED_AI_PAYLOAD)
        # Register and log in
        await client.post("/api/v1/auth/register", json={
            "username": "apple_test_expired",
            "password": "Str0ngPass!",
        })
        login = await client.post("/api/v1/auth/login", json={
            "username": "apple_test_expired",
            "password": "Str0ngPass!",
        })
        token = login.json()["access_token"]
        auth_headers = {**ios_headers, "Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/billing/apple/verify",
            json={"transaction_jws": jws, "product_id": "soma.ai.monthly"},
            headers=auth_headers,
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"] == "transaction_not_active"

    @pytest.mark.asyncio
    async def test_verify_rejects_unknown_product(self, client, ios_headers):
        """Unknown Apple product IDs must return 400."""
        jws = _make_jws({
            **VALID_AI_PAYLOAD,
            "productId": "com.unknown.product",
        })
        await client.post("/api/v1/auth/register", json={
            "username": "apple_test_product",
            "password": "Str0ngPass!",
        })
        login = await client.post("/api/v1/auth/login", json={
            "username": "apple_test_product",
            "password": "Str0ngPass!",
        })
        token = login.json()["access_token"]
        auth_headers = {**ios_headers, "Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/billing/apple/verify",
            json={"transaction_jws": jws, "product_id": "com.unknown.product"},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestAppleRestoreEndpoint:
    """POST /billing/apple/restore"""

    @pytest.mark.asyncio
    async def test_restore_blocked_for_android(self, client, android_headers):
        resp = await client.post(
            "/api/v1/billing/apple/restore",
            json={"transaction_jws_list": ["a.b.c"]},
            headers=android_headers,
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["error"] == "apple_billing_ios_only"

    @pytest.mark.asyncio
    async def test_restore_requires_auth(self, client, ios_headers):
        resp = await client.post(
            "/api/v1/billing/apple/restore",
            json={"transaction_jws_list": ["a.b.c"]},
            headers=ios_headers,
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_restore_empty_list_returns_400(self, client, ios_headers):
        await client.post("/api/v1/auth/register", json={
            "username": "apple_restore_empty",
            "password": "Str0ngPass!",
        })
        login = await client.post("/api/v1/auth/login", json={
            "username": "apple_restore_empty",
            "password": "Str0ngPass!",
        })
        token = login.json()["access_token"]
        auth_headers = {**ios_headers, "Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/billing/apple/restore",
            json={"transaction_jws_list": []},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestAppleNotificationsEndpoint:
    """POST /billing/apple/notifications — server-to-server, never blocked."""

    @pytest.mark.asyncio
    async def test_notifications_not_blocked_for_any_platform(self, client):
        """Apple Server Notifications must work regardless of platform header."""
        payload = _make_jws({
            "notificationUUID": "test-uuid-12345",
            "notificationType": "SUBSCRIBED",
            "data": {},
        })
        for platform_header in [{"X-Client-Platform": "ios"}, {"X-Client-Platform": "android"}, {}]:
            resp = await client.post(
                "/api/v1/billing/apple/notifications",
                content=json.dumps({"signedPayload": payload}).encode(),
                headers={**platform_header, "Content-Type": "application/json"},
            )
            assert resp.status_code != 403, (
                f"Apple notifications must not return 403 for platform {platform_header}"
            )

    @pytest.mark.asyncio
    async def test_notifications_returns_400_for_empty_body(self, client):
        resp = await client.post(
            "/api/v1/billing/apple/notifications",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400


class TestStripeEndpointsStillBlockIos:
    """Stripe endpoints must still return 451 for iOS (regression guard)."""

    @pytest.mark.asyncio
    async def test_checkout_still_blocked_for_ios(self, client, ios_headers):
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "ai", "billing_interval": "monthly"},
            headers=ios_headers,
        )
        assert resp.status_code == 451
        assert resp.json()["detail"]["error"] == "ios_billing_not_supported"

    @pytest.mark.asyncio
    async def test_portal_still_blocked_for_ios(self, client, ios_headers):
        resp = await client.get(
            "/api/v1/billing/portal",
            headers=ios_headers,
        )
        assert resp.status_code == 451
        assert resp.json()["detail"]["error"] == "ios_billing_not_supported"

    @pytest.mark.asyncio
    async def test_checkout_not_blocked_for_android(self, client, android_headers):
        """Android must NOT be blocked from Stripe checkout (regression guard)."""
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "ai", "billing_interval": "monthly"},
            headers=android_headers,
        )
        assert resp.status_code != 451, "Android must not be blocked by iOS guard"
