"""
Tests unitaires — dashboard_service.py

Stratégie : mocks complets (pas de DB) — teste la logique métier pure.
  - compute_recovery_score_v1 : calculs pondérés, cas limites
  - generate_alerts           : déclenchement des alertes
  - generate_recommendations  : génération des recommandations
  - build_weight_summary      : calcul BMI, delta, direction
  - _day_bounds               : bornes UTC
"""
import pytest
from datetime import datetime, date, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from app.schemas.dashboard import (
    HydrationSummary, SleepSummary, NutritionSummary,
    ActivitySummary, RecoverySummary,
)
from app.services.dashboard_service import (
    compute_recovery_score_v1,
    generate_alerts,
    generate_recommendations,
    _day_bounds,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_sleep(
    duration_minutes: int = 480,
    perceived_quality: int = None,
    quality_label: str = "good",
    debt_minutes: int = 0,
) -> SleepSummary:
    duration_hours = round(duration_minutes / 60, 2) if duration_minutes is not None else None
    return SleepSummary(
        duration_minutes=duration_minutes,
        duration_hours=duration_hours,
        sleep_score=None,
        perceived_quality=perceived_quality,
        deep_sleep_minutes=None,
        rem_sleep_minutes=None,
        avg_hrv_ms=None,
        debt_minutes=debt_minutes,
        quality_label=quality_label,
    )


def make_hydration(total_ml: int = 2000, target_ml: int = 2500) -> HydrationSummary:
    pct = round((total_ml / target_ml) * 100, 1)
    status = "optimal" if pct >= 100 else ("adequate" if pct >= 70 else "insufficient")
    return HydrationSummary(
        total_ml=total_ml,
        target_ml=target_ml,
        pct=pct,
        status=status,
        entries_count=4,
    )


def make_nutrition(
    calories_consumed: float = 2000.0,
    calories_target: float = 2200.0,
    protein_g: float = 150.0,
    protein_target_g: float = 180.0,
    fasting_active: bool = False,
) -> NutritionSummary:
    return NutritionSummary(
        calories_consumed=calories_consumed,
        calories_target=calories_target,
        protein_g=protein_g,
        protein_target_g=protein_target_g,
        carbs_g=200.0,
        fat_g=80.0,
        fiber_g=25.0,
        meal_count=3,
        fasting_active=fasting_active,
        fasting_hours_elapsed=None,
        energy_balance_kcal=None,
    )


def make_activity(
    steps: float = 6000.0,
    steps_pct: float = 75.0,
    today_workout: dict = None,
) -> ActivitySummary:
    return ActivitySummary(
        steps=steps,
        steps_goal=8000,
        steps_pct=steps_pct,
        active_calories_kcal=300.0,
        distance_km=4.5,
        stand_hours=8.0,
        resting_heart_rate_bpm=55.0,
        hrv_ms=55.0,
        vo2_max=None,
        today_workout=today_workout,
    )


# ── Tests _day_bounds ──────────────────────────────────────────────────────────

class TestDayBounds:
    def test_returns_utc_start_of_day(self):
        d = date(2026, 3, 15)
        start, end = _day_bounds(d)
        assert start == datetime(2026, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 3, 16, 0, 0, 0, tzinfo=timezone.utc)

    def test_exactly_24h_span(self):
        d = date(2026, 1, 1)
        start, end = _day_bounds(d)
        delta = end - start
        assert delta.total_seconds() == 86400

    def test_last_day_of_month(self):
        d = date(2026, 3, 31)
        start, end = _day_bounds(d)
        assert end.day == 1
        assert end.month == 4

    def test_leap_year(self):
        d = date(2024, 2, 29)  # Année bissextile
        start, end = _day_bounds(d)
        assert start.day == 29
        assert start.month == 2
        assert end.day == 1
        assert end.month == 3


# ── Tests compute_recovery_score_v1 ────────────────────────────────────────────

class TestComputeRecoveryScore:

    def test_no_data_returns_unknown_with_zero_confidence(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.quality_label = "unknown"
        result = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=None)
        assert result.readiness_score is None
        assert result.confidence == 0.0
        assert result.recommended_intensity == "moderate"

    def test_perfect_sleep_gives_high_score(self):
        sleep = make_sleep(duration_minutes=480, perceived_quality=5, quality_label="excellent")
        result = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=None)
        assert result.readiness_score is not None
        assert result.readiness_score >= 80  # 480min = 100 + quality_bonus 20 → capped 100 × 0.4 = 40 / 0.4 = 100
        assert result.confidence == pytest.approx(0.40)

    def test_poor_sleep_gives_low_score(self):
        sleep = make_sleep(duration_minutes=300, perceived_quality=1, quality_label="poor")
        result = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=None)
        # 300 min = score 0, quality_bonus = (1-3)*10 = -20 → max(0, 0-20) = 0
        assert result.readiness_score == pytest.approx(0.0)
        assert result.recommended_intensity == "rest"

    def test_all_data_confidence_is_1(self):
        sleep = make_sleep(duration_minutes=450)
        result = compute_recovery_score_v1(
            sleep, hrv_ms=60, resting_hr=55, last_workout_load=250
        )
        assert result.confidence == pytest.approx(1.0)
        assert result.readiness_score is not None

    def test_hrv_contribution_only(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.quality_label = "unknown"
        result = compute_recovery_score_v1(sleep, hrv_ms=60.0, resting_hr=None, last_workout_load=None)
        assert result.readiness_score is not None
        assert result.confidence == pytest.approx(0.20)

    def test_high_hrv_gives_high_score(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.quality_label = "unknown"
        result = compute_recovery_score_v1(sleep, hrv_ms=80.0, resting_hr=None, last_workout_load=None)
        # HRV 80ms → score = max(0, min(100, (80-20)/(60-20)*100)) = 150 → capped 100
        assert result.hrv_contribution == pytest.approx(100.0)

    def test_low_hrv_gives_low_score(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.quality_label = "unknown"
        result = compute_recovery_score_v1(sleep, hrv_ms=10.0, resting_hr=None, last_workout_load=None)
        assert result.hrv_contribution == pytest.approx(0.0)  # (10-20)/(40)*100 < 0 → 0

    def test_low_resting_hr_gives_high_score(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.quality_label = "unknown"
        result = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=45.0, last_workout_load=None)
        # (80-45)/(80-45)*100 = 100
        assert result.readiness_score == pytest.approx(100.0)

    def test_training_load_thresholds(self):
        sleep = make_sleep(duration_minutes=None)
        sleep.duration_minutes = None
        sleep.quality_label = "unknown"

        # Faible charge → score 90
        r1 = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=100)
        assert r1.training_load_contribution == 90

        # Charge élevée → score plus bas
        r2 = compute_recovery_score_v1(sleep, hrv_ms=None, resting_hr=None, last_workout_load=700)
        assert r2.training_load_contribution == 35

    def test_recommended_intensity_push(self):
        sleep = make_sleep(480, perceived_quality=5, quality_label="excellent")
        result = compute_recovery_score_v1(sleep, hrv_ms=80, resting_hr=45, last_workout_load=50)
        assert result.recommended_intensity == "push"
        assert result.readiness_score >= 80

    def test_recommended_intensity_rest(self):
        sleep = make_sleep(300, perceived_quality=1, quality_label="poor")
        result = compute_recovery_score_v1(sleep, hrv_ms=15, resting_hr=90, last_workout_load=800)
        assert result.recommended_intensity == "rest"


# ── Tests generate_alerts ──────────────────────────────────────────────────────

class TestGenerateAlerts:

    def _make_recovery(self, score: float = 75.0) -> RecoverySummary:
        return RecoverySummary(
            readiness_score=score,
            recovery_score=score,
            sleep_contribution=score,
            hrv_contribution=None,
            training_load_contribution=None,
            recommended_intensity="normal",
            confidence=0.6,
            reasoning="Test",
        )

    def test_no_alerts_when_everything_ok(self):
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="excellent"),
            nutrition=make_nutrition(2000, 2000),
            activity=make_activity(8000),
            recovery=self._make_recovery(80),
        )
        assert len(alerts) == 0

    def test_hydration_warning_below_50pct(self):
        alerts = generate_alerts(
            hydration=make_hydration(1200, 2500),  # 48%
            sleep=make_sleep(480, quality_label="excellent"),
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        hydration_alerts = [a for a in alerts if a.type == "hydration"]
        assert len(hydration_alerts) == 1
        assert hydration_alerts[0].severity == "warning"

    def test_hydration_info_between_50_and_70pct(self):
        alerts = generate_alerts(
            hydration=make_hydration(1600, 2500),  # 64%
            sleep=make_sleep(480, quality_label="excellent"),
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        hydration_alerts = [a for a in alerts if a.type == "hydration"]
        assert len(hydration_alerts) == 1
        assert hydration_alerts[0].severity == "info"

    def test_no_hydration_alert_above_70pct(self):
        alerts = generate_alerts(
            hydration=make_hydration(1800, 2500),  # 72%
            sleep=make_sleep(480, quality_label="excellent"),
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        hydration_alerts = [a for a in alerts if a.type == "hydration"]
        assert len(hydration_alerts) == 0

    def test_sleep_warning_when_poor(self):
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(300, quality_label="poor"),
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        sleep_alerts = [a for a in alerts if a.type == "sleep"]
        assert any(a.severity == "warning" for a in sleep_alerts)

    def test_sleep_debt_alert(self):
        sleep = make_sleep(360, quality_label="fair", debt_minutes=120)
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=sleep,
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        debt_alerts = [a for a in alerts if a.type == "sleep" and "dette" in a.message.lower()]
        assert len(debt_alerts) == 1

    def test_recovery_warning_when_low(self):
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(30),
        )
        recovery_alerts = [a for a in alerts if a.type == "recovery"]
        assert len(recovery_alerts) == 1
        assert recovery_alerts[0].severity == "warning"

    def test_no_recovery_alert_when_above_40(self):
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            nutrition=make_nutrition(),
            activity=make_activity(),
            recovery=self._make_recovery(45),
        )
        recovery_alerts = [a for a in alerts if a.type == "recovery"]
        assert len(recovery_alerts) == 0

    def test_nutrition_alert_very_low_calories(self):
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            nutrition=make_nutrition(calories_consumed=800.0, calories_target=2200.0, fasting_active=False),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        nutrition_alerts = [a for a in alerts if a.type == "nutrition"]
        assert len(nutrition_alerts) == 1

    def test_no_nutrition_alert_when_fasting(self):
        """Pas d'alerte calorique si l'utilisateur est en jeûne."""
        alerts = generate_alerts(
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            nutrition=make_nutrition(calories_consumed=400.0, calories_target=2200.0, fasting_active=True),
            activity=make_activity(),
            recovery=self._make_recovery(75),
        )
        nutrition_alerts = [a for a in alerts if a.type == "nutrition"]
        assert len(nutrition_alerts) == 0


# ── Tests generate_recommendations ─────────────────────────────────────────────

class TestGenerateRecommendations:

    def _make_profile(self, primary_goal: str = "muscle_gain") -> MagicMock:
        profile = MagicMock()
        profile.primary_goal = primary_goal
        return profile

    def _make_recovery(self, intensity: str = "normal") -> RecoverySummary:
        return RecoverySummary(
            readiness_score=70,
            recovery_score=70,
            sleep_contribution=70,
            hrv_contribution=None,
            training_load_contribution=None,
            recommended_intensity=intensity,
            confidence=0.6,
            reasoning="Test",
        )

    def test_workout_recommendation_when_no_workout_and_good_recovery(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            activity=make_activity(today_workout=None),
            recovery=self._make_recovery("normal"),
            nutrition=make_nutrition(),
        )
        workout_recs = [r for r in recs if r.category == "workout"]
        assert len(workout_recs) >= 1

    def test_rest_recommendation_when_poor_recovery(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(300, quality_label="poor"),
            activity=make_activity(today_workout=None),
            recovery=self._make_recovery("rest"),
            nutrition=make_nutrition(),
        )
        recovery_recs = [r for r in recs if r.category == "recovery"]
        assert len(recovery_recs) >= 1

    def test_no_workout_recommendation_when_already_trained(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            activity=make_activity(today_workout={"id": "abc", "status": "completed"}),
            recovery=self._make_recovery("normal"),
            nutrition=make_nutrition(),
        )
        workout_recs = [r for r in recs if r.category == "workout"]
        assert len(workout_recs) == 0

    def test_protein_recommendation_when_deficit(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            activity=make_activity(today_workout={"id": "abc"}),
            recovery=self._make_recovery("normal"),
            nutrition=make_nutrition(protein_g=50.0, protein_target_g=180.0),
        )
        protein_recs = [r for r in recs if r.category == "nutrition"]
        assert len(protein_recs) >= 1

    def test_hydration_recommendation_when_below_70pct(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(1500, 2500),  # 60%
            sleep=make_sleep(480, quality_label="good"),
            activity=make_activity(today_workout={"id": "abc"}),
            recovery=self._make_recovery("normal"),
            nutrition=make_nutrition(),
        )
        hydration_recs = [r for r in recs if r.category == "hydration"]
        assert len(hydration_recs) >= 1

    def test_recommendations_sorted_by_priority(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(1200, 2500),
            sleep=make_sleep(480, quality_label="good"),
            activity=make_activity(today_workout=None),
            recovery=self._make_recovery("normal"),
            nutrition=make_nutrition(protein_g=50.0, protein_target_g=180.0),
        )
        priorities = [r.priority for r in recs]
        assert priorities == sorted(priorities)

    def test_steps_recommendation_when_low(self):
        recs = generate_recommendations(
            profile=self._make_profile(),
            hydration=make_hydration(2500, 2500),
            sleep=make_sleep(480, quality_label="good"),
            activity=make_activity(steps=2000, steps_pct=25.0, today_workout={"id": "abc"}),
            recovery=self._make_recovery("normal"),
            nutrition=make_nutrition(),
        )
        steps_recs = [r for r in recs if r.category == "workout" and "pas" in r.text.lower()]
        assert len(steps_recs) >= 1


# ── Tests schemas dashboard ────────────────────────────────────────────────────

class TestDashboardSchemas:

    def test_sleep_summary_no_data(self):
        s = SleepSummary(
            duration_minutes=None, duration_hours=None,
            sleep_score=None, perceived_quality=None,
            deep_sleep_minutes=None, rem_sleep_minutes=None,
            avg_hrv_ms=None, debt_minutes=None,
            quality_label="unknown",
        )
        assert s.quality_label == "unknown"
        assert s.duration_minutes is None

    def test_hydration_summary_pct_calculation(self):
        h = make_hydration(2000, 2500)
        assert h.pct == pytest.approx(80.0)
        assert h.status == "adequate"

    def test_hydration_summary_optimal(self):
        h = make_hydration(2600, 2500)
        assert h.pct > 100
        assert h.status == "optimal"
