"""
Tests d'intégration — flux auth complet (register → login → refresh → protected endpoint).

Nécessite : SOMA_TEST_DATABASE_URL=postgresql+asyncpg://...
"""
import pytest
import pytest_asyncio
import httpx
import uuid


pytestmark = pytest.mark.asyncio


# Import des fixtures depuis conftest_pg
# Note : pytest découvre automatiquement conftest_pg si placé dans le même répertoire
# mais il faut l'importer explicitement si le nom n'est pas "conftest.py"
from tests.integration.conftest_pg import client, engine, db_session  # noqa (fixtures)


# ── Tests register ─────────────────────────────────────────────────────────────

class TestRegister:

    async def test_register_success(self, client: httpx.AsyncClient):
        username = f"user_{uuid.uuid4().hex[:8]}"
        resp = await client.post("/api/v1/auth/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "SecurePass123!",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_username(self, client: httpx.AsyncClient):
        username = f"dup_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "SecurePass123!",
        }
        await client.post("/api/v1/auth/register", json=payload)
        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_invalid_email(self, client: httpx.AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "username": f"u_{uuid.uuid4().hex[:8]}",
            "email": "not-an-email",
            "password": "SecurePass123!",
        })
        assert resp.status_code == 422  # Validation error


# ── Tests login ────────────────────────────────────────────────────────────────

class TestLogin:

    async def test_login_success(self, client: httpx.AsyncClient):
        username = f"login_{uuid.uuid4().hex[:8]}"
        await client.post("/api/v1/auth/register", json={
            "username": username, "email": f"{username}@test.com", "password": "Pass123!",
        })

        resp = await client.post("/api/v1/auth/login", json={
            "username": username, "password": "Pass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    async def test_login_wrong_password(self, client: httpx.AsyncClient):
        username = f"wrongpw_{uuid.uuid4().hex[:8]}"
        await client.post("/api/v1/auth/register", json={
            "username": username, "email": f"{username}@test.com", "password": "RealPass123!",
        })

        resp = await client.post("/api/v1/auth/login", json={
            "username": username, "password": "WrongPass!",
        })
        assert resp.status_code == 401

    async def test_login_unknown_user(self, client: httpx.AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "ghost_user_xyz_123", "password": "Pass123!",
        })
        assert resp.status_code == 401


# ── Tests refresh ──────────────────────────────────────────────────────────────

class TestRefresh:

    async def test_refresh_success(self, client: httpx.AsyncClient):
        username = f"refresh_{uuid.uuid4().hex[:8]}"
        tokens = (await client.post("/api/v1/auth/register", json={
            "username": username, "email": f"{username}@test.com", "password": "Pass123!",
        })).json()

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert "access_token" in new_tokens

    async def test_refresh_invalid_token(self, client: httpx.AsyncClient):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert resp.status_code in (401, 422)


# ── Tests protected endpoints ──────────────────────────────────────────────────

class TestProtectedEndpoints:

    async def test_profile_requires_auth(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_profile_with_valid_token(self, client: httpx.AsyncClient):
        username = f"profile_{uuid.uuid4().hex[:8]}"
        tokens = (await client.post("/api/v1/auth/register", json={
            "username": username, "email": f"{username}@test.com", "password": "Pass123!",
        })).json()

        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == username

    async def test_dashboard_requires_auth(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/dashboard/today")
        assert resp.status_code == 401

    async def test_dashboard_with_valid_token(self, client: httpx.AsyncClient):
        username = f"dash_{uuid.uuid4().hex[:8]}"
        tokens = (await client.post("/api/v1/auth/register", json={
            "username": username, "email": f"{username}@test.com", "password": "Pass123!",
        })).json()

        resp = await client.get(
            "/api/v1/dashboard/today",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recovery" in data
        assert "hydration" in data
        assert "sleep" in data


# ── Test flux complet register → login → refresh → protected ──────────────────

class TestCompleteAuthFlow:

    async def test_full_flow(self, client: httpx.AsyncClient):
        """
        Flux complet : register → login → accès profil → refresh → accès profil avec nouveau token.
        """
        username = f"flow_{uuid.uuid4().hex[:8]}"
        password = "FlowTestPass123!"

        # 1. Register
        reg_resp = await client.post("/api/v1/auth/register", json={
            "username": username, "email": f"{username}@test.com", "password": password,
        })
        assert reg_resp.status_code == 201
        reg_tokens = reg_resp.json()

        # 2. Accès profil avec le token de register
        profile_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {reg_tokens['access_token']}"},
        )
        assert profile_resp.status_code == 200
        assert profile_resp.json()["username"] == username

        # 3. Login
        login_resp = await client.post("/api/v1/auth/login", json={
            "username": username, "password": password,
        })
        assert login_resp.status_code == 200
        login_tokens = login_resp.json()

        # 4. Refresh du token
        refresh_resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": login_tokens["refresh_token"],
        })
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()

        # 5. Accès profil avec le nouveau token
        profile_resp2 = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert profile_resp2.status_code == 200
        assert profile_resp2.json()["username"] == username
