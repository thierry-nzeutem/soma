"""
Tests unitaires — Health Plan Service (LOT 3).

Couvre :
  - _readiness_level (5 tests)
  - _build_workout_recommendation (7 tests)
  - _build_daily_tips (6 tests)
  - _build_eating_window (4 tests)
  - _choose_nutrition_focus (4 tests)
  - generate_daily_health_plan — intégration (7 tests)
"""
import pytest
from datetime import datetime
from app.services.health_plan_service import (
    _readiness_level,
    _build_workout_recommendation,
    _build_daily_tips,
    _build_eating_window,
    _choose_nutrition_focus,
    generate_daily_health_plan,
    SLEEP_TARGET_HOURS,
    STEPS_DAILY_GOAL,
)
from app.services.nutrition_engine import compute_nutrition_targets, NutritionTargets


# ── Helpers ───────────────────────────────────────────────────────────────────

def _default_targets() -> NutritionTargets:
    return compute_nutrition_targets(
        age=30, sex="male", height_cm=180, weight_kg=80,
        body_fat_pct=None, activity_level="moderate",
        fitness_level="intermediate", primary_goal="maintenance",
    )


# ── _readiness_level ──────────────────────────────────────────────────────────

class TestReadinessLevel:

    def test_none_returns_unknown(self):
        assert _readiness_level(None) == "unknown"

    def test_above_80_excellent(self):
        assert _readiness_level(85) == "excellent"
        assert _readiness_level(100) == "excellent"

    def test_65_to_80_good(self):
        assert _readiness_level(70) == "good"
        assert _readiness_level(65) == "good"

    def test_50_to_65_fair(self):
        assert _readiness_level(55) == "fair"
        assert _readiness_level(50) == "fair"

    def test_below_50_poor(self):
        assert _readiness_level(40) == "poor"
        assert _readiness_level(0) == "poor"


# ── _build_workout_recommendation ─────────────────────────────────────────────

class TestBuildWorkoutRecommendation:

    def test_already_done_returns_special(self):
        rec = _build_workout_recommendation(
            "push", has_workout_today=True,
            primary_goal="muscle_gain", fitness_level="intermediate",
            home_equipment=None, gym_access=False,
        )
        assert rec["type"] == "already_done"
        assert rec["duration_minutes"] == 0

    def test_push_intensity_gives_60min(self):
        rec = _build_workout_recommendation(
            "push", has_workout_today=False,
            primary_goal="muscle_gain", fitness_level="intermediate",
            home_equipment=None, gym_access=True,
        )
        assert rec["duration_minutes"] == 60
        assert rec["intensity"] == "push"

    def test_rest_intensity(self):
        rec = _build_workout_recommendation(
            "rest", has_workout_today=False,
            primary_goal="maintenance", fitness_level="beginner",
            home_equipment=None, gym_access=False,
        )
        assert rec["type"] == "rest"
        assert rec["duration_minutes"] == 0

    def test_moderate_intensity_30min(self):
        rec = _build_workout_recommendation(
            "moderate", has_workout_today=False,
            primary_goal="weight_loss", fitness_level="intermediate",
            home_equipment=["dumbbells"], gym_access=False,
        )
        assert rec["duration_minutes"] == 30

    def test_light_intensity_gives_mobility(self):
        rec = _build_workout_recommendation(
            "light", has_workout_today=False,
            primary_goal="maintenance", fitness_level="beginner",
            home_equipment=None, gym_access=False,
        )
        assert rec["type"] == "mobility"
        assert rec["duration_minutes"] == 20

    def test_gym_access_sets_location_gym(self):
        rec = _build_workout_recommendation(
            "normal", has_workout_today=False,
            primary_goal="muscle_gain", fitness_level="advanced",
            home_equipment=None, gym_access=True,
        )
        assert rec["location"] == "gym"

    def test_no_equipment_sets_outdoor(self):
        rec = _build_workout_recommendation(
            "normal", has_workout_today=False,
            primary_goal="maintenance", fitness_level="beginner",
            home_equipment=None, gym_access=False,
        )
        assert rec["location"] == "outdoor"


# ── _build_daily_tips ─────────────────────────────────────────────────────────

class TestBuildDailyTips:

    def test_returns_list(self):
        tips = _build_daily_tips(
            readiness_level="good",
            hydration_pct=0.80, sleep_quality_label="good",
            protein_pct=0.90, calorie_pct=0.90,
        )
        assert isinstance(tips, list)

    def test_max_4_tips(self):
        tips = _build_daily_tips(
            readiness_level="poor",
            hydration_pct=0.30, sleep_quality_label="poor",
            protein_pct=0.40, calorie_pct=0.50,
        )
        assert len(tips) <= 4

    def test_poor_readiness_adds_tip(self):
        tips = _build_daily_tips("poor", None, None, None, None)
        assert any("coucher" in t.lower() or "récupération" in t.lower() for t in tips)

    def test_dehydration_adds_tip(self):
        tips = _build_daily_tips("good", 0.30, None, None, None)
        assert any("eau" in t.lower() or "hydrat" in t.lower() for t in tips)

    def test_low_protein_adds_tip(self):
        tips = _build_daily_tips("good", 1.0, None, 0.40, None)
        assert any("protéine" in t.lower() for t in tips)

    def test_fasting_adds_tip(self):
        tips = _build_daily_tips(
            "good", 1.0, None, 1.0, 1.0,
            intermittent_fasting=True, fasting_protocol="16:8",
        )
        assert any("jeûne" in t.lower() or "16:8" in t for t in tips)


# ── _build_eating_window ──────────────────────────────────────────────────────

class TestBuildEatingWindow:

    def test_no_fasting_returns_none(self):
        result = _build_eating_window(
            intermittent_fasting=False,
            fasting_protocol=None,
            eating_window_hours=None,
            fasting_start_at=None,
            usual_wake_time=None,
        )
        assert result is None

    def test_fasting_with_protocol_returns_dict(self):
        result = _build_eating_window(
            intermittent_fasting=True,
            fasting_protocol="16:8",
            eating_window_hours=8.0,
            fasting_start_at="15:00",
            usual_wake_time="07:00",
        )
        assert result is not None
        assert result["protocol"] == "16:8"
        assert result["window_hours"] == 8.0

    def test_eating_start_from_wake_time(self):
        result = _build_eating_window(
            intermittent_fasting=True,
            fasting_protocol="16:8",
            eating_window_hours=8.0,
            fasting_start_at="15:00",
            usual_wake_time="07:00",
        )
        assert result["eating_start"] == "07:00"

    def test_no_protocol_returns_none_even_with_fasting(self):
        result = _build_eating_window(
            intermittent_fasting=True,
            fasting_protocol=None,
            eating_window_hours=None,
            fasting_start_at=None,
            usual_wake_time="07:00",
        )
        assert result is None


# ── _choose_nutrition_focus ───────────────────────────────────────────────────

class TestChooseNutritionFocus:

    def test_low_protein_pct_prioritizes_protein(self):
        focus = _choose_nutrition_focus(avg_protein_pct=0.50, micro_score=None, top_deficiencies=[])
        assert focus is not None
        assert "rotéine" in focus

    def test_deficiency_mentions_nutriment(self):
        focus = _choose_nutrition_focus(
            avg_protein_pct=0.90,
            micro_score=40.0,
            top_deficiencies=["Vitamine D"],
        )
        assert focus is not None
        assert "Vitamine D" in focus

    def test_low_micro_score_general_variety(self):
        focus = _choose_nutrition_focus(
            avg_protein_pct=0.90, micro_score=30.0, top_deficiencies=[],
        )
        assert focus is not None
        assert "variété" in focus.lower() or "divers" in focus.lower()

    def test_no_issues_returns_none(self):
        focus = _choose_nutrition_focus(
            avg_protein_pct=0.95, micro_score=80.0, top_deficiencies=[],
        )
        assert focus is None


# ── generate_daily_health_plan — intégration ─────────────────────────────────

class TestGenerateDailyHealthPlan:

    def test_returns_complete_plan(self):
        targets = _default_targets()
        plan = generate_daily_health_plan(
            target_date_str="2026-03-07",
            readiness_score=75.0,
            recommended_intensity="normal",
            nutrition_targets=targets,
        )
        assert plan.date == "2026-03-07"
        assert plan.protein_target_g > 0
        assert plan.calorie_target > 0
        assert plan.steps_goal == STEPS_DAILY_GOAL
        assert plan.sleep_target_hours == SLEEP_TARGET_HOURS

    def test_readiness_level_computed(self):
        targets = _default_targets()
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=85.0,
            recommended_intensity="push",
            nutrition_targets=targets,
        )
        assert plan.readiness_level == "excellent"

    def test_unknown_readiness_if_none(self):
        targets = _default_targets()
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=None,
            recommended_intensity="moderate",
            nutrition_targets=targets,
        )
        assert plan.readiness_level == "unknown"

    def test_already_done_workout_returns_rest_rec(self):
        targets = _default_targets()
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=80.0,
            recommended_intensity="push",
            nutrition_targets=targets,
            has_workout_today=True,
        )
        assert plan.workout_recommendation["type"] == "already_done"

    def test_generated_at_is_recent(self):
        targets = _default_targets()
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=70.0,
            recommended_intensity="normal",
            nutrition_targets=targets,
        )
        assert plan.generated_at is not None
        assert isinstance(plan.generated_at, datetime)

    def test_eating_window_with_fasting(self):
        from app.services.nutrition_engine import compute_nutrition_targets
        targets = compute_nutrition_targets(
            age=30, sex="male", height_cm=180, weight_kg=80,
            body_fat_pct=None, activity_level="moderate",
            fitness_level="intermediate", primary_goal="maintenance",
            intermittent_fasting=True, fasting_protocol="16:8",
            usual_wake_time="07:00",
        )
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=70.0,
            recommended_intensity="normal",
            nutrition_targets=targets,
            intermittent_fasting=True,
            fasting_protocol="16:8",
        )
        assert plan.eating_window is not None
        assert plan.eating_window["protocol"] == "16:8"

    def test_alerts_limited_to_3(self):
        targets = _default_targets()
        raw_alerts = [{"title": f"Alert {i}"} for i in range(10)]
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=70.0,
            recommended_intensity="moderate",
            nutrition_targets=targets,
            raw_alerts=raw_alerts,
        )
        assert len(plan.alerts) <= 3

    def test_tips_not_empty(self):
        targets = _default_targets()
        plan = generate_daily_health_plan(
            "2026-03-07",
            readiness_score=70.0,
            recommended_intensity="normal",
            nutrition_targets=targets,
        )
        assert len(plan.daily_tips) >= 1
