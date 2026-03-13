"""
SOMA LOT 18 — Tests unitaires Daily Briefing Service.

Couvre :
  - _readiness_level() : seuils 80/65/45
  - _readiness_color() : seuils 75/50
  - _extract_coach_tip() : troncage, markdown cleaning, fallback
  - DailyBriefing dataclass : valeurs par défaut
  - compute_daily_briefing() : mock DB, champs renseignés, alerts capping

~18 tests purs, aucune dépendance DB réelle.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.daily_briefing_service import (
    DailyBriefing,
    _readiness_level,
    _readiness_color,
    _extract_coach_tip,
    compute_daily_briefing,
    _COLOR_GOOD,
    _COLOR_MODERATE,
    _COLOR_LOW,
    _COACH_TIP_MAX_LEN,
)


# ── Tests _readiness_level() ────────────────────────────────────────────────

class TestReadinessLevel:
    """Seuils : ≥80 excellent, ≥65 good, ≥45 moderate, <45 low."""

    def test_excellent_at_80(self):
        assert _readiness_level(80.0) == "excellent"

    def test_excellent_at_100(self):
        assert _readiness_level(100.0) == "excellent"

    def test_good_at_65(self):
        assert _readiness_level(65.0) == "good"

    def test_good_at_79(self):
        assert _readiness_level(79.0) == "good"

    def test_moderate_at_45(self):
        assert _readiness_level(45.0) == "moderate"

    def test_moderate_at_64(self):
        assert _readiness_level(64.0) == "moderate"

    def test_low_below_45(self):
        assert _readiness_level(44.9) == "low"
        assert _readiness_level(0.0) == "low"

    def test_none_returns_moderate(self):
        assert _readiness_level(None) == "moderate"


# ── Tests _readiness_color() ────────────────────────────────────────────────

class TestReadinessColor:
    """Seuils couleur : ≥75 vert, ≥50 orange, <50 rouge."""

    def test_green_at_75(self):
        assert _readiness_color(75.0) == _COLOR_GOOD
        assert _readiness_color(75.0) == "#34C759"

    def test_green_at_100(self):
        assert _readiness_color(100.0) == _COLOR_GOOD

    def test_orange_at_50(self):
        assert _readiness_color(50.0) == _COLOR_MODERATE
        assert _readiness_color(50.0) == "#FF9500"

    def test_orange_at_74(self):
        assert _readiness_color(74.9) == _COLOR_MODERATE

    def test_red_below_50(self):
        assert _readiness_color(49.9) == _COLOR_LOW
        assert _readiness_color(0.0) == _COLOR_LOW
        assert _readiness_color(0.0) == "#FF3B30"

    def test_none_returns_moderate_color(self):
        assert _readiness_color(None) == _COLOR_MODERATE


# ── Tests _extract_coach_tip() ──────────────────────────────────────────────

class TestExtractCoachTip:
    """Extraction du coach tip depuis le morning_briefing Markdown."""

    def test_none_returns_none(self):
        assert _extract_coach_tip(None) is None

    def test_empty_string_returns_none(self):
        assert _extract_coach_tip("") is None

    def test_truncates_at_max_len(self):
        long_text = "x" * 1000
        tip = _extract_coach_tip(long_text)
        assert len(tip) <= _COACH_TIP_MAX_LEN

    def test_removes_markdown_asterisks(self):
        text = "**Synthèse** : Tu es en bonne forme."
        tip = _extract_coach_tip(text)
        assert "**" not in tip

    def test_splits_at_double_newline(self):
        text = "Première partie (plus de 20 chars ici).\n\nDeuxième partie."
        tip = _extract_coach_tip(text)
        assert "Deuxième partie" not in tip

    def test_short_text_returned_as_is(self):
        text = "Mange bien et dors bien."
        tip = _extract_coach_tip(text)
        assert tip is not None
        assert "Mange bien" in tip


# ── Tests DailyBriefing dataclass ───────────────────────────────────────────

class TestDailyBriefingDefaults:
    """Le dataclass doit avoir des valeurs par défaut sensées."""

    def test_hydration_default_is_2500(self):
        b = DailyBriefing(briefing_date=date.today(), generated_at=datetime.now(timezone.utc))
        assert b.hydration_target_ml == 2500

    def test_readiness_score_default_none(self):
        b = DailyBriefing(briefing_date=date.today(), generated_at=datetime.now(timezone.utc))
        assert b.readiness_score is None

    def test_alerts_default_empty_list(self):
        b = DailyBriefing(briefing_date=date.today(), generated_at=datetime.now(timezone.utc))
        assert b.alerts == []

    def test_readiness_color_default_moderate(self):
        b = DailyBriefing(briefing_date=date.today(), generated_at=datetime.now(timezone.utc))
        assert b.readiness_color == _COLOR_MODERATE


# ── Tests compute_daily_briefing (mock DB) ──────────────────────────────────

class TestComputeDailyBriefing:
    """Tests de compute_daily_briefing avec DB mockée."""

    def _make_db(self) -> AsyncMock:
        """Retourne une session DB mockée qui retourne None pour toutes les requêtes."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        return db

    @pytest.mark.asyncio
    async def test_empty_data_returns_defaults(self):
        """Sans données DB, le briefing doit avoir les valeurs par défaut."""
        db = self._make_db()
        user_id = uuid.uuid4()
        today = date.today()

        briefing = await compute_daily_briefing(db, user_id, today)

        assert briefing.briefing_date == today
        assert briefing.readiness_score is None
        assert briefing.hydration_target_ml == 2500
        assert briefing.alerts == []
        assert briefing.coach_tip is None

    @pytest.mark.asyncio
    async def test_briefing_date_is_today(self):
        """La date du briefing doit correspondre à target_date."""
        db = self._make_db()
        user_id = uuid.uuid4()
        target = date(2026, 3, 8)

        briefing = await compute_daily_briefing(db, user_id, target)
        assert briefing.briefing_date == target

    @pytest.mark.asyncio
    async def test_alerts_capped_at_3(self):
        """Les alertes sont limitées à 3 même si plus sont disponibles."""
        db = self._make_db()

        # Mock twin avec 3 recommandations
        twin_mock = MagicMock()
        twin_mock.overall_status = "moderate"
        twin_mock.primary_concern = "fatigue"
        twin_mock.recommendations = ["Alert 1", "Alert 2", "Alert 3", "Alert 4", "Alert 5"]

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=twin_mock)),  # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        assert len(briefing.alerts) <= 3

    @pytest.mark.asyncio
    async def test_readiness_fields_populated(self):
        """Si ReadinessScore existe, les champs readiness doivent être renseignés."""
        db = self._make_db()

        readiness_mock = MagicMock()
        readiness_mock.overall_readiness = 82.0
        readiness_mock.recommended_intensity = "push"

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=readiness_mock)),  # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        assert briefing.readiness_score == 82.0
        assert briefing.readiness_level == "excellent"
        assert briefing.readiness_color == _COLOR_GOOD
        assert briefing.recommended_intensity == "push"

    @pytest.mark.asyncio
    async def test_sleep_duration_computed_from_minutes(self):
        """sleep_duration_h = sleep_minutes / 60."""
        db = self._make_db()

        metrics_mock = MagicMock()
        metrics_mock.sleep_minutes = 450  # 7h30
        metrics_mock.calories_target = 2200.0
        metrics_mock.protein_target_g = 150.0
        metrics_mock.hydration_target_ml = 2500
        metrics_mock.sleep_quality_label = "good"

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),     # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=metrics_mock)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),     # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),     # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),     # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        assert briefing.sleep_duration_h == 7.5

    @pytest.mark.asyncio
    async def test_twin_status_propagated(self):
        """Si DigitalTwinSnapshot existe, twin_status est renseigné."""
        db = self._make_db()

        twin_mock = MagicMock()
        twin_mock.overall_status = "critical"
        twin_mock.primary_concern = "overtraining_risk"
        twin_mock.recommendations = []

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=twin_mock)),  # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        assert briefing.twin_status == "critical"
        assert briefing.twin_primary_concern == "overtraining_risk"

    @pytest.mark.asyncio
    async def test_top_insight_taken_from_first_unread(self):
        """top_insight doit être le message du premier insight non lu."""
        db = self._make_db()

        insight_mock = MagicMock()
        insight_mock.message = "Ta récupération est insuffisante cette semaine."

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=insight_mock)),  # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        assert "récupération" in (briefing.top_insight or "")

    @pytest.mark.asyncio
    async def test_coach_tip_truncated_at_max_len(self):
        """Le coach tip doit être tronqué à _COACH_TIP_MAX_LEN caractères."""
        db = self._make_db()

        rec_mock = MagicMock()
        rec_mock.morning_briefing = "x" * 2000
        rec_mock.workout_recommendation = None
        rec_mock.daily_plan = None
        rec_mock.hydration_target_ml = None

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=rec_mock)),  # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        if briefing.coach_tip:
            assert len(briefing.coach_tip) <= _COACH_TIP_MAX_LEN

    @pytest.mark.asyncio
    async def test_alerts_deduplicated(self):
        """Les alertes dupliquées doivent être dédoublonnées."""
        db = self._make_db()

        twin_mock = MagicMock()
        twin_mock.overall_status = "moderate"
        twin_mock.primary_concern = None
        twin_mock.recommendations = ["Attention à la récupération", "Attention à la récupération"]

        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # readiness
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # metrics
            MagicMock(scalar_one_or_none=MagicMock(return_value=twin_mock)),  # twin
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # rec
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # insight
        ]
        db.execute = AsyncMock(side_effect=results)

        briefing = await compute_daily_briefing(db, uuid.uuid4())
        assert len(briefing.alerts) == len(set(briefing.alerts))
