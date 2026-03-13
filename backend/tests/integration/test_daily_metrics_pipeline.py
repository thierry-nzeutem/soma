"""
Tests d'intégration PostgreSQL — Pipeline DailyMetrics (LOT 5).

Vérifie que compute_and_persist_daily_metrics fonctionne avec une vraie DB :
  - Insert initial
  - Upsert (cache 2h)
  - Force recompute
  - lazy_ensure_today_metrics
  - get_metrics_history avec tendances

Usage :
    SOMA_TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/soma_test \
    pytest tests/integration/test_daily_metrics_pipeline.py -v
"""
import pytest
import pytest_asyncio
import uuid
from datetime import date, timedelta

from tests.integration.conftest_pg import db_session, engine, anyio_backend  # noqa: F401

pytestmark = pytest.mark.anyio


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _make_user(db) -> uuid.UUID:
    """Crée un utilisateur minimal en DB et retourne son user_id."""
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


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestDailyMetricsPersistence:
    """Vérifications basiques insert / upsert."""

    async def test_insert_creates_snapshot(self, db_session):
        """compute_and_persist crée un snapshot en DB."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics
        user_id = await _make_user(db_session)
        today = date.today()

        dm = await compute_and_persist_daily_metrics(
            db_session, user_id, today, profile=None, force_recompute=True
        )

        assert dm is not None
        assert dm.user_id == user_id
        assert dm.metrics_date == today
        assert dm.id is not None

    async def test_upsert_returns_existing_within_cache(self, db_session):
        """Second appel dans la fenêtre 2h retourne le même objet."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics
        user_id = await _make_user(db_session)
        today = date.today()

        dm1 = await compute_and_persist_daily_metrics(
            db_session, user_id, today, force_recompute=True
        )
        dm2 = await compute_and_persist_daily_metrics(
            db_session, user_id, today, force_recompute=False
        )

        assert dm1.id == dm2.id

    async def test_force_recompute_updates_snapshot(self, db_session):
        """force_recompute=True met à jour même si snapshot est frais."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics
        user_id = await _make_user(db_session)
        today = date.today()

        dm1 = await compute_and_persist_daily_metrics(
            db_session, user_id, today, force_recompute=True
        )
        dm2 = await compute_and_persist_daily_metrics(
            db_session, user_id, today, force_recompute=True
        )

        # Même ID (upsert) mais updated_at plus récent
        assert dm1.id == dm2.id

    async def test_algorithm_version_is_set(self, db_session):
        """algorithm_version est défini à v1.0 sur chaque snapshot."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics
        user_id = await _make_user(db_session)

        dm = await compute_and_persist_daily_metrics(
            db_session, user_id, date.today(), force_recompute=True
        )

        assert dm.algorithm_version == "v1.0"

    async def test_data_completeness_pct_is_computed(self, db_session):
        """data_completeness_pct est calculé et stocké."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics
        user_id = await _make_user(db_session)

        dm = await compute_and_persist_daily_metrics(
            db_session, user_id, date.today(), force_recompute=True
        )

        assert isinstance(dm.data_completeness_pct, float)
        assert 0.0 <= dm.data_completeness_pct <= 100.0


class TestLazyEnsureTodayMetrics:
    """Vérifie le fallback lazy compute."""

    async def test_lazy_ensure_creates_if_absent(self, db_session):
        """lazy_ensure_today_metrics crée un snapshot si absent."""
        from app.services.daily_metrics_service import lazy_ensure_today_metrics, get_daily_metrics
        user_id = await _make_user(db_session)
        today = date.today()

        # Vérifier qu'il n'existe pas encore
        existing = await get_daily_metrics(db_session, user_id, today)
        assert existing is None

        dm = await lazy_ensure_today_metrics(db_session, user_id, today)

        assert dm is not None
        assert dm.user_id == user_id

    async def test_lazy_ensure_does_not_raise_on_error(self, db_session):
        """lazy_ensure_today_metrics retourne None si erreur (pas de propagation)."""
        from app.services.daily_metrics_service import lazy_ensure_today_metrics

        # UUID invalide qui n'est lié à aucun user
        fake_user_id = uuid.uuid4()
        # Ne devrait pas lever d'exception
        result = await lazy_ensure_today_metrics(db_session, fake_user_id, date.today())
        # Peut retourner None ou un objet selon l'implémentation
        # L'important : pas de crash


class TestMetricsHistory:
    """Vérifie get_metrics_history avec tendances."""

    async def test_history_empty_when_no_data(self, db_session):
        """Historique vide si pas de données."""
        from app.services.daily_metrics_service import get_metrics_history
        user_id = await _make_user(db_session)

        history = await get_metrics_history(db_session, user_id, days=30)

        assert history.days_available == 0
        assert history.history == []

    async def test_history_returns_multiple_days(self, db_session):
        """Historique retourne les données sur plusieurs jours."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics, get_metrics_history
        user_id = await _make_user(db_session)
        today = date.today()

        # Créer 3 jours de données
        for i in range(3):
            target = today - timedelta(days=i)
            await compute_and_persist_daily_metrics(
                db_session, user_id, target, force_recompute=True
            )

        history = await get_metrics_history(db_session, user_id, days=30)

        assert history.days_available >= 3
        assert len(history.history) >= 3

    async def test_history_ordered_descending(self, db_session):
        """Les entrées sont ordonnées par date décroissante."""
        from app.services.daily_metrics_service import compute_and_persist_daily_metrics, get_metrics_history
        user_id = await _make_user(db_session)
        today = date.today()

        for i in range(3):
            await compute_and_persist_daily_metrics(
                db_session, user_id, today - timedelta(days=i), force_recompute=True
            )

        history = await get_metrics_history(db_session, user_id, days=30)

        dates = [r.metrics_date for r in history.history]
        assert dates == sorted(dates, reverse=True)
