"""
Tests d'intégration PostgreSQL — Score Longévité (LOT 5).

Vérifie que le pipeline longevity fonctionne avec une vraie DB :
  - GET /scores/longevity retourne un score valide
  - algorithm_version est présent dans la réponse
  - GET /home/summary inclut le résumé longévité
  - Le lazy compute de DailyMetrics est déclenché si nécessaire

Usage :
    SOMA_TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/soma_test \
    pytest tests/integration/test_longevity_integration.py -v
"""
import pytest
import pytest_asyncio
import uuid
from datetime import date, timedelta

from tests.integration.conftest_pg import (  # noqa: F401
    db_session, engine, anyio_backend, client, register_and_login, auth_headers,
)

pytestmark = pytest.mark.anyio


# ── Helpers ─────────────────────────────────────────────────────────────────────

async def _register_with_profile(client, username: str) -> dict:
    """Crée un utilisateur avec profil minimal et retourne les tokens."""
    tokens = await register_and_login(client, username)
    # Créer un profil pour que le score longévité ait des données
    await client.put(
        "/api/v1/profile",
        headers=auth_headers(tokens["access_token"]),
        json={
            "age": 30,
            "sex": "male",
            "height_cm": 180,
            "activity_level": "moderate",
            "primary_goal": "maintenance",
        },
    )
    return tokens


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestLongevityEndpoint:
    """Vérifie le endpoint GET /scores/longevity."""

    async def test_longevity_returns_200_without_data(self, client):
        """GET /scores/longevity retourne 200 même sans données historiques."""
        tokens = await register_and_login(client, "longevity_user1")
        resp = await client.get(
            "/api/v1/scores/longevity",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200

    async def test_longevity_response_has_required_fields(self, client):
        """La réponse a les champs obligatoires."""
        tokens = await _register_with_profile(client, "longevity_user2")
        resp = await client.get(
            "/api/v1/scores/longevity",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "longevity_score" in data
        assert "user_id" in data
        assert "score_date" in data
        assert "algorithm_version" in data

    async def test_longevity_algorithm_version_is_v1(self, client):
        """algorithm_version == 'v1.0' dans la réponse."""
        tokens = await register_and_login(client, "longevity_user3")
        resp = await client.get(
            "/api/v1/scores/longevity",
            headers=auth_headers(tokens["access_token"]),
        )
        data = resp.json()
        assert data["algorithm_version"] == "v1.0"

    async def test_longevity_score_between_0_and_100(self, client):
        """Si longevity_score est présent, il est entre 0 et 100."""
        tokens = await _register_with_profile(client, "longevity_user4")
        resp = await client.get(
            "/api/v1/scores/longevity",
            headers=auth_headers(tokens["access_token"]),
        )
        data = resp.json()

        if data.get("longevity_score") is not None:
            assert 0.0 <= data["longevity_score"] <= 100.0

    async def test_longevity_with_days_param(self, client):
        """Le paramètre ?days= est accepté."""
        tokens = await register_and_login(client, "longevity_user5")
        resp = await client.get(
            "/api/v1/scores/longevity?days=7",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200

    async def test_longevity_requires_auth(self, client):
        """Sans token, 401 retourné."""
        resp = await client.get("/api/v1/scores/longevity")
        assert resp.status_code == 401


class TestHomeSummaryEndpoint:
    """Vérifie le endpoint GET /home/summary (LOT 5)."""

    async def test_home_summary_returns_200(self, client):
        """GET /home/summary retourne 200."""
        tokens = await register_and_login(client, "home_user1")
        resp = await client.get(
            "/api/v1/home/summary",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200

    async def test_home_summary_schema_complete(self, client):
        """La réponse home/summary a tous les champs attendus."""
        tokens = await register_and_login(client, "home_user2")
        resp = await client.get(
            "/api/v1/home/summary",
            headers=auth_headers(tokens["access_token"]),
        )
        data = resp.json()

        # Champs obligatoires
        assert "summary_date" in data
        assert "generated_at" in data
        assert "unread_insights" in data
        assert "unread_insights_count" in data
        assert "has_active_plan" in data
        # Champs optionnels (peuvent être null)
        assert "metrics" in data
        assert "readiness" in data
        assert "plan" in data
        assert "longevity" in data

    async def test_home_summary_requires_auth(self, client):
        """Sans token, 401 retourné."""
        resp = await client.get("/api/v1/home/summary")
        assert resp.status_code == 401

    async def test_home_summary_unread_count_is_int(self, client):
        """unread_insights_count est un entier >= 0."""
        tokens = await register_and_login(client, "home_user3")
        resp = await client.get(
            "/api/v1/home/summary",
            headers=auth_headers(tokens["access_token"]),
        )
        data = resp.json()
        assert isinstance(data["unread_insights_count"], int)
        assert data["unread_insights_count"] >= 0

    async def test_home_summary_metrics_created_lazily(self, client):
        """home/summary déclenche le lazy compute des métriques du jour."""
        tokens = await _register_with_profile(client, "home_user4")
        resp = await client.get(
            "/api/v1/home/summary",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        # Les métriques doivent être présentes (lazy compute déclenché)
        assert data.get("metrics") is not None


class TestDailyMetricsEndpoint:
    """Vérifie GET /metrics/daily avec une vraie DB."""

    async def test_metrics_daily_returns_200(self, client):
        """GET /metrics/daily retourne 200."""
        tokens = await register_and_login(client, "metrics_user1")
        resp = await client.get(
            "/api/v1/metrics/daily",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200

    async def test_metrics_daily_has_algorithm_version(self, client):
        """La réponse inclut algorithm_version."""
        tokens = await register_and_login(client, "metrics_user2")
        resp = await client.get(
            "/api/v1/metrics/daily",
            headers=auth_headers(tokens["access_token"]),
        )
        data = resp.json()
        assert "algorithm_version" in data
        assert data["algorithm_version"] == "v1.0"
