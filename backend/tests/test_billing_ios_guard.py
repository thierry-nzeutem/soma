"""Tests iOS billing guard (Apple App Store compliance).

Verifies that POST /billing/checkout and GET /billing/portal
return HTTP 451 for X-Client-Platform: ios, and that non-iOS
platforms are not blocked by this guard.
"""
import pytest
import uuid
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _register_and_login(client: AsyncClient) -> str:
    username = f"billing_test_{uuid.uuid4().hex[:8]}"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": f"{username}@test.com", "password": "TestPass123!"},
    )
    assert reg.status_code in (200, 201), f"register failed: {reg.text}"
    login = await client.post(
        "/auth/login",
        json={"username": username, "password": "TestPass123!"},
    )
    assert login.status_code == 200, f"login failed: {login.text}"
    return login.json()["access_token"]


# ---------------------------------------------------------------------------
# POST /billing/checkout -- iOS guard
# ---------------------------------------------------------------------------

class TestCheckoutIosGuard:
    """POST /api/v1/billing/checkout must return 451 for iOS clients."""

    async def test_checkout_blocked_for_ios(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "ai", "billing_interval": "monthly"},
            headers={"Authorization": f"Bearer {token}", "X-Client-Platform": "ios"},
        )
        assert resp.status_code == 451, f"Expected 451, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("detail", {}).get("error") == "ios_billing_not_supported"
        assert body["detail"]["platform"] == "ios"

    async def test_checkout_blocked_ios_case_insensitive(self, client: AsyncClient):
        """Header value iOS or IOS must also be blocked."""
        token = await _register_and_login(client)
        for variant in ("iOS", "IOS", "  ios  "):
            resp = await client.post(
                "/api/v1/billing/checkout",
                json={"plan_code": "ai", "billing_interval": "monthly"},
                headers={"Authorization": f"Bearer {token}", "X-Client-Platform": variant},
            )
            assert resp.status_code == 451, f"Expected 451 for {variant!r}, got {resp.status_code}"

    async def test_checkout_not_blocked_for_android(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "ai", "billing_interval": "monthly"},
            headers={"Authorization": f"Bearer {token}", "X-Client-Platform": "android"},
        )
        # 503 = Stripe not configured in test env; what matters is NOT 451
        assert resp.status_code != 451, "Android should not be blocked by iOS guard"

    async def test_checkout_not_blocked_for_web(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "ai", "billing_interval": "monthly"},
            headers={"Authorization": f"Bearer {token}", "X-Client-Platform": "web"},
        )
        assert resp.status_code != 451, "Web should not be blocked by iOS guard"

    async def test_checkout_not_blocked_without_header(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan_code": "ai", "billing_interval": "monthly"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code != 451, "Missing header should not trigger iOS guard"


# ---------------------------------------------------------------------------
# GET /billing/portal -- iOS guard
# ---------------------------------------------------------------------------

class TestPortalIosGuard:
    """GET /api/v1/billing/portal must return 451 for iOS clients."""

    async def test_portal_blocked_for_ios(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/billing/portal",
            headers={"Authorization": f"Bearer {token}", "X-Client-Platform": "ios"},
        )
        assert resp.status_code == 451, f"Expected 451, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("detail", {}).get("error") == "ios_billing_not_supported"

    async def test_portal_not_blocked_for_android(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/billing/portal",
            headers={"Authorization": f"Bearer {token}", "X-Client-Platform": "android"},
        )
        # 400 expected (no stripe_customer_id) -- what matters is NOT 451
        assert resp.status_code != 451, "Android should not be blocked by iOS guard"

    async def test_portal_not_blocked_for_web(self, client: AsyncClient):
        token = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/billing/portal",
            headers={"Authorization": f"Bearer {token}", "X-Client-Platform": "web"},
        )
        assert resp.status_code != 451, "Web should not be blocked by iOS guard"


# ---------------------------------------------------------------------------
# POST /billing/webhook -- must NOT be blocked (server-to-server)
# ---------------------------------------------------------------------------

class TestWebhookNotBlocked:
    """POST /billing/webhook must not be blocked regardless of platform header."""

    async def test_webhook_not_blocked_for_ios_header(self, client: AsyncClient):
        import json as _json
        fake_event = _json.dumps({"type": "ping", "id": "evt_test"})
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=fake_event,
            headers={"Content-Type": "application/json", "X-Client-Platform": "ios"},
        )
        # Webhook is server-to-server and must never return 451.
        assert resp.status_code != 451, f"Webhook must not return 451: {resp.status_code}"
