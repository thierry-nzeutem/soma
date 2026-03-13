"""
Tests unitaires — readiness_service.py (logique pure, sans DB).

Stratégie :
  - Tests sur le mappage ReadinessScore → RecoverySummary (via compute_recovery_score_v1)
  - Tests sur les schémas Pydantic ReadinessScoreResponse
  - Tests sur la logique de freshness (MIN_RECOMPUTE_INTERVAL_H)
  - Pas de DB requise (mocks pour les fonctions async)
"""
import pytest
from datetime import date, datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import uuid

from app.services.readiness_service import MIN_RECOMPUTE_INTERVAL_H
from app.services.dashboard_service import compute_recovery_score_v1
from app.schemas.scores import ReadinessScoreResponse, ReadinessScoreHistoryResponse
from app.schemas.dashboard import SleepSummary, RecoverySummary


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_sleep(
    duration_minutes: int = 480,
    perceived_quality: int = None,
    avg_hrv_ms: float = None,
) -> SleepSummary:
    duration_hours = round(duration_minutes / 60, 2) if duration_minutes is not None else None
    return SleepSummary(
        duration_minutes=duration_minutes,
        duration_hours=duration_hours,
        sleep_score=None,
        perceived_quality=perceived_quality,
        deep_sleep_minutes=None,
        rem_sleep_minutes=None,
        avg_hrv_ms=avg_hrv_ms,
        debt_minutes=None,
        quality_label="good" if duration_minutes and duration_minutes >= 420 else "poor",
    )


def make_mock_readiness_score(
    overall_readiness: float = 75.0,
    sleep_score: float = 80.0,
    hrv_score: float = 60.0,
    training_load_score: float = 70.0,
    recovery_score: float = 80.0,
    recommended_intensity: str = "normal",
    reasoning: str = "Bonne récupération.",
    confidence_score: float = 0.8,
    variables_used: dict = None,
    score_date: date = None,
    created_at: datetime = None,
    updated_at: datetime = None,
) -> MagicMock:
    now = datetime.now(timezone.utc)
    score = MagicMock()
    score.id = uuid.uuid4()
    score.user_id = uuid.uuid4()
    score.score_date = score_date or date.today()
    score.overall_readiness = overall_readiness
    score.sleep_score = sleep_score
    score.hrv_score = hrv_score
    score.training_load_score = training_load_score
    score.recovery_score = recovery_score
    score.recommended_intensity = recommended_intensity
    score.reasoning = reasoning
    score.confidence_score = confidence_score
    score.variables_used = variables_used or {}
    score.created_at = created_at or now
    score.updated_at = updated_at or now
    return score


# ── Tests freshness logic ──────────────────────────────────────────────────────

class TestReadinessFreshnessConfig:

    def test_recompute_interval_is_positive(self):
        assert MIN_RECOMPUTE_INTERVAL_H > 0

    def test_recompute_interval_reasonable(self):
        # Doit être entre 30min et 24h
        assert 0.5 <= MIN_RECOMPUTE_INTERVAL_H <= 24

    def test_fresh_score_within_interval(self):
        """Un score créé il y a moins de MIN_RECOMPUTE_INTERVAL_H est frais."""
        now = datetime.now(timezone.utc)
        half_interval = timedelta(hours=MIN_RECOMPUTE_INTERVAL_H / 2)
        score_created = now - half_interval
        freshness = now - score_created.replace(tzinfo=timezone.utc)
        assert freshness < timedelta(hours=MIN_RECOMPUTE_INTERVAL_H)

    def test_stale_score_beyond_interval(self):
        """Un score créé il y a plus de MIN_RECOMPUTE_INTERVAL_H est périmé."""
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(hours=MIN_RECOMPUTE_INTERVAL_H + 1)
        freshness = now - old_time.replace(tzinfo=timezone.utc)
        assert freshness >= timedelta(hours=MIN_RECOMPUTE_INTERVAL_H)


# ── Tests compute_recovery_score_v1 (déjà testé dans test_dashboard) ─────────

class TestRecoveryScoreComputation:
    """Vérifie que les champs de RecoverySummary correspondent bien aux champs de ReadinessScore."""

    def test_full_data_gives_score(self):
        sleep = make_sleep(duration_minutes=480, perceived_quality=4)
        result = compute_recovery_score_v1(sleep, hrv_ms=55.0, resting_hr=52.0, last_workout_load=200.0)
        assert result.readiness_score is not None
        assert 0 <= result.readiness_score <= 100
        assert result.sleep_contribution is not None
        assert result.hrv_contribution is not None
        assert result.training_load_contribution is not None
        assert result.confidence == pytest.approx(1.0)

    def test_no_data_gives_no_score(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.duration_hours = None
        result = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=None)
        assert result.readiness_score is None
        assert result.confidence == pytest.approx(0.0)

    def test_sleep_only_gives_partial_score(self):
        sleep = make_sleep(duration_minutes=420)
        result = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=None)
        assert result.readiness_score is not None
        assert result.confidence < 1.0  # Données partielles → confidence < 100%
        assert result.hrv_contribution is None
        assert result.training_load_contribution is None

    def test_recommended_intensity_levels(self):
        """Vérifie les seuils d'intensité recommandée."""
        # Excellent (>= 80)
        sleep = make_sleep(480, perceived_quality=5)
        result = compute_recovery_score_v1(sleep, hrv_ms=70.0, resting_hr=45.0, last_workout_load=0.0)
        assert result.recommended_intensity == "push"

        # Mauvais (< 35)
        sleep_bad = make_sleep(300, perceived_quality=1)
        result_bad = compute_recovery_score_v1(sleep_bad, hrv_ms=15.0, resting_hr=85.0, last_workout_load=700.0)
        assert result_bad.recommended_intensity == "rest"

    def test_confidence_proportional_to_data(self):
        """Plus on a de données, plus la confiance est haute."""
        sleep = make_sleep(480)
        r1 = compute_recovery_score_v1(sleep, None, None, None)          # 1 composant
        r2 = compute_recovery_score_v1(sleep, 50.0, None, None)          # 2 composants
        r3 = compute_recovery_score_v1(sleep, 50.0, 60.0, None)          # 3 composants
        r4 = compute_recovery_score_v1(sleep, 50.0, 60.0, 200.0)        # 4 composants
        assert r1.confidence <= r2.confidence <= r3.confidence <= r4.confidence
        assert r4.confidence == pytest.approx(1.0)


# ── Tests ReadinessScoreResponse schema ───────────────────────────────────────

class TestReadinessScoreResponseSchema:

    def _make_score_dict(self, **overrides):
        now = datetime.now(timezone.utc)
        base = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "score_date": date.today(),
            "overall_readiness": 75.0,
            "sleep_score": 80.0,
            "hrv_score": 60.0,
            "training_load_score": 70.0,
            "recovery_score": 80.0,
            "recommended_intensity": "normal",
            "reasoning": "Bonne récupération.",
            "confidence_score": 0.8,
            "variables_used": {"sleep_available": True},
            "created_at": now,
            "updated_at": now,
        }
        base.update(overrides)
        return base

    def test_basic_response(self):
        data = self._make_score_dict()
        resp = ReadinessScoreResponse(**data)
        assert resp.overall_readiness == 75.0
        assert resp.confidence_score == pytest.approx(0.8)
        assert resp.score_date == date.today()

    def test_optional_fields_none(self):
        data = self._make_score_dict(
            hrv_score=None, training_load_score=None, variables_used=None,
        )
        resp = ReadinessScoreResponse(**data)
        assert resp.hrv_score is None
        assert resp.training_load_score is None

    def test_all_intensity_levels_valid(self):
        for intensity in ("rest", "light", "moderate", "normal", "push"):
            data = self._make_score_dict(recommended_intensity=intensity)
            resp = ReadinessScoreResponse(**data)
            assert resp.recommended_intensity == intensity

    def test_history_response(self):
        now = datetime.now(timezone.utc)
        scores = [
            ReadinessScoreResponse(**self._make_score_dict(score_date=date.today())),
            ReadinessScoreResponse(**self._make_score_dict(score_date=date(2026, 3, 6))),
        ]
        history = ReadinessScoreHistoryResponse(
            history=scores,
            days_requested=30,
            days_available=2,
            date_from=date(2026, 3, 6),
            date_to=date.today(),
        )
        assert len(history.history) == 2
        assert history.days_available == 2
        assert history.days_requested == 30


# ── Tests score → recovery mapping ────────────────────────────────────────────

class TestReadinessToRecoverySummaryMapping:
    """
    Vérifie que les champs ReadinessScore correspondent correctement
    aux champs RecoverySummary utilisés dans le dashboard.
    """

    def test_mapping_fields(self):
        """Les noms de champs doivent être cohérents entre ReadinessScore et RecoverySummary."""
        mock_score = make_mock_readiness_score(
            overall_readiness=72.5,
            sleep_score=80.0,
            hrv_score=65.0,
            training_load_score=60.0,
            recovery_score=80.0,
            recommended_intensity="normal",
            reasoning="Bon score.",
            confidence_score=0.8,
        )

        # Simulation de la conversion faite dans dashboard_service.build_dashboard
        recovery = RecoverySummary(
            readiness_score=mock_score.overall_readiness,
            recovery_score=mock_score.recovery_score,
            sleep_contribution=mock_score.sleep_score,
            hrv_contribution=mock_score.hrv_score,
            training_load_contribution=mock_score.training_load_score,
            recommended_intensity=mock_score.recommended_intensity,
            confidence=mock_score.confidence_score,
            reasoning=mock_score.reasoning,
        )

        assert recovery.readiness_score == pytest.approx(72.5)
        assert recovery.sleep_contribution == pytest.approx(80.0)
        assert recovery.hrv_contribution == pytest.approx(65.0)
        assert recovery.training_load_contribution == pytest.approx(60.0)
        assert recovery.recommended_intensity == "normal"
        assert recovery.confidence == pytest.approx(0.8)

    def test_null_score_mapping(self):
        """Un ReadinessScore avec des None se mappe correctement."""
        mock_score = make_mock_readiness_score(
            overall_readiness=None,
            hrv_score=None,
            training_load_score=None,
            confidence_score=0.4,
            recommended_intensity="moderate",
        )

        recovery = RecoverySummary(
            readiness_score=mock_score.overall_readiness,
            recovery_score=mock_score.recovery_score,
            sleep_contribution=mock_score.sleep_score,
            hrv_contribution=mock_score.hrv_score,
            training_load_contribution=mock_score.training_load_score,
            recommended_intensity=mock_score.recommended_intensity or "moderate",
            confidence=mock_score.confidence_score or 0.0,
            reasoning=mock_score.reasoning or "",
        )

        assert recovery.readiness_score is None
        assert recovery.hrv_contribution is None
        assert recovery.recommended_intensity == "moderate"
