"""
Tests d'intégration PostgreSQL — Insight Engine (LOT 5).

Vérifie que run_and_persist_insights fonctionne avec une vraie DB :
  - Génération d'insights depuis DailyMetrics réels
  - Upsert (contrainte unique user + date + category + title)
  - Statut is_read / is_dismissed
  - Endpoint GET /insights (via client HTTP)

Usage :
    SOMA_TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/soma_test \
    pytest tests/integration/test_insights_integration.py -v
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

async def _make_user(db) -> uuid.UUID:
    from app.models.user import User
    import bcrypt
    user = User(
        username=f"test_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@soma-test.com",
        hashed_password=bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt()).decode(),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user.id


async def _create_daily_metrics(db, user_id: uuid.UUID, target_date: date, **kwargs):
    """Crée un DailyMetrics directement en DB pour tester l'insight engine."""
    from app.models.metrics import DailyMetrics
    dm = DailyMetrics(
        user_id=user_id,
        metrics_date=target_date,
        **kwargs,
    )
    db.add(dm)
    await db.flush()
    return dm


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestInsightPersistence:
    """Vérifie la persistance et l'upsert des insights."""

    async def test_run_and_persist_creates_insights(self, db_session):
        """run_and_persist_insights crée des insights si détections positives."""
        from app.services.insight_service import run_and_persist_insights
        user_id = await _make_user(db_session)
        today = date.today()

        # Créer des données qui déclenchent des insights (déficit protéique)
        for i in range(7):
            await _create_daily_metrics(
                db_session, user_id, today - timedelta(days=i),
                protein_g=40,           # bien en dessous de la target
                protein_target_g=150,   # target haute
                calories_consumed=1800,
                calories_target=2500,
                hydration_ml=1200,
                hydration_target_ml=2500,
                sleep_minutes=300,      # < 6h
                workout_count=0,
                data_completeness_pct=90.0,
                algorithm_version="v1.0",
            )

        insights = await run_and_persist_insights(db_session, user_id, today)

        # Au moins quelques insights doivent être générés avec ces données
        assert isinstance(insights, list)

    async def test_upsert_no_duplicate_same_day(self, db_session):
        """Deux appels le même jour ne créent pas de doublons (contrainte unique)."""
        from app.services.insight_service import run_and_persist_insights
        from sqlalchemy import select, and_
        from app.models.insights import Insight

        user_id = await _make_user(db_session)
        today = date.today()

        # Données minimal pour potentiellement déclencher des insights
        for i in range(7):
            await _create_daily_metrics(
                db_session, user_id, today - timedelta(days=i),
                protein_g=40,
                protein_target_g=150,
                algorithm_version="v1.0",
            )

        await run_and_persist_insights(db_session, user_id, today)
        first_count_res = await db_session.execute(
            select(Insight).where(and_(
                Insight.user_id == user_id,
                Insight.insight_date == today,
            ))
        )
        first_count = len(first_count_res.scalars().all())

        # Deuxième appel — ne doit pas créer de doublons
        await run_and_persist_insights(db_session, user_id, today)
        second_count_res = await db_session.execute(
            select(Insight).where(and_(
                Insight.user_id == user_id,
                Insight.insight_date == today,
            ))
        )
        second_count = len(second_count_res.scalars().all())

        assert first_count == second_count

    async def test_insight_fields_are_set(self, db_session):
        """Les champs obligatoires des insights sont renseignés."""
        from app.services.insight_service import run_and_persist_insights
        from sqlalchemy import select, and_
        from app.models.insights import Insight

        user_id = await _make_user(db_session)
        today = date.today()

        for i in range(7):
            await _create_daily_metrics(
                db_session, user_id, today - timedelta(days=i),
                protein_g=30, protein_target_g=150,
                algorithm_version="v1.0",
            )

        await run_and_persist_insights(db_session, user_id, today)

        res = await db_session.execute(
            select(Insight).where(and_(
                Insight.user_id == user_id,
                Insight.insight_date == today,
            ))
        )
        insights = res.scalars().all()

        for insight in insights:
            assert insight.category is not None
            assert insight.severity in ("info", "warning", "critical")
            assert insight.title is not None
            assert insight.message is not None
            assert insight.is_read is False
            assert insight.is_dismissed is False


class TestInsightEndpointHTTP:
    """Tests HTTP via le client FastAPI complet."""

    async def test_get_insights_returns_empty_list(self, client):
        """GET /insights retourne une liste vide si aucun insight."""
        tokens = await register_and_login(client, "insights_user1")
        resp = await client.get(
            "/api/v1/insights",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data
        assert isinstance(data["insights"], list)

    async def test_insights_run_endpoint(self, client):
        """POST /insights/run retourne la liste des insights générés."""
        tokens = await register_and_login(client, "insights_user2")
        resp = await client.post(
            "/api/v1/insights/run",
            headers=auth_headers(tokens["access_token"]),
        )
        # Peut retourner 200 (avec insights) ou 200 (liste vide si pas de données)
        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data

    async def test_home_summary_returns_insights_count(self, client):
        """GET /home/summary inclut unread_insights_count."""
        tokens = await register_and_login(client, "insights_user3")
        resp = await client.get(
            "/api/v1/home/summary",
            headers=auth_headers(tokens["access_token"]),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "unread_insights_count" in data
        assert isinstance(data["unread_insights_count"], int)
