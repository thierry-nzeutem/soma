"""
Tests pour Adaptive Nutrition Engine — LOT 11.
~50 tests purs (aucun accès DB).
"""
import pytest
from datetime import date

from app.domains.adaptive_nutrition.service import (
    DayType,
    NutritionTarget,
    AdaptiveNutritionPlan,
    _determine_day_type,
    _compute_calorie_target,
    _compute_protein_target,
    _compute_carb_target,
    _compute_fat_target,
    _compute_hydration_target,
    _fasting_compatible,
    compute_adaptive_plan,
    build_adaptive_nutrition_summary,
    DAY_TYPE_LABELS,
)


# ── _determine_day_type ───────────────────────────────────────────────────────

class TestDetermineDayType:
    def test_default_is_rest(self):
        day_type = _determine_day_type(None, None, None, None)
        assert day_type == DayType.REST

    def test_recovery_beats_training(self):
        # Even with high load, low readiness → RECOVERY
        day_type = _determine_day_type(
            training_load_today=200, readiness_score=30,
            fatigue_score=None, acwr=None
        )
        assert day_type == DayType.RECOVERY

    def test_high_fatigue_triggers_recovery(self):
        day_type = _determine_day_type(
            training_load_today=80, readiness_score=60,
            fatigue_score=80, acwr=None
        )
        assert day_type == DayType.RECOVERY

    def test_deload_from_high_acwr(self):
        day_type = _determine_day_type(
            training_load_today=60, readiness_score=75,
            fatigue_score=30, acwr=1.6
        )
        assert day_type == DayType.DELOAD

    def test_intense_training_condition(self):
        day_type = _determine_day_type(
            training_load_today=120, readiness_score=80,
            fatigue_score=20, acwr=1.1
        )
        assert day_type == DayType.INTENSE_TRAINING

    def test_training_moderate_load(self):
        day_type = _determine_day_type(
            training_load_today=70, readiness_score=75,
            fatigue_score=30, acwr=None
        )
        assert day_type == DayType.TRAINING

    def test_day_type_hint_overrides(self):
        day_type = _determine_day_type(None, None, None, None, day_type_hint="intense_training")
        assert day_type == DayType.INTENSE_TRAINING

    def test_invalid_hint_falls_back_to_computed(self):
        day_type = _determine_day_type(None, None, None, None, day_type_hint="invalid_value")
        assert day_type == DayType.REST


# ── _compute_calorie_target ───────────────────────────────────────────────────

class TestComputeCalorieTarget:
    def test_weight_loss_creates_deficit(self):
        target = _compute_calorie_target(
            tdee=2000, goal="weight_loss", day_type=DayType.REST,
            fatigue_score=20, plateau_risk=False, weight_kg=70
        )
        assert target.value == pytest.approx(1700.0)  # 2000 - 300

    def test_muscle_gain_creates_surplus(self):
        target = _compute_calorie_target(
            tdee=2000, goal="muscle_gain", day_type=DayType.REST,
            fatigue_score=20, plateau_risk=False, weight_kg=70
        )
        assert target.value == pytest.approx(2300.0)  # 2000 + 300

    def test_intense_training_adds_300(self):
        target = _compute_calorie_target(
            tdee=2000, goal="maintenance", day_type=DayType.INTENSE_TRAINING,
            fatigue_score=20, plateau_risk=False, weight_kg=70
        )
        assert target.value == pytest.approx(2300.0)  # 2000 + 300

    def test_recovery_reduces_150(self):
        target = _compute_calorie_target(
            tdee=2000, goal="maintenance", day_type=DayType.RECOVERY,
            fatigue_score=20, plateau_risk=False, weight_kg=70
        )
        assert target.value == pytest.approx(1850.0)  # 2000 - 150

    def test_plateau_switches_to_maintenance(self):
        target = _compute_calorie_target(
            tdee=2000, goal="weight_loss", day_type=DayType.REST,
            fatigue_score=20, plateau_risk=True, weight_kg=70
        )
        assert target.value == pytest.approx(2000.0)  # maintenance, ignores goal

    def test_fatigue_reduces_deficit(self):
        # Weight loss deficit -300, fatigue > 75 → reduces by 150 → net -150
        target = _compute_calorie_target(
            tdee=2000, goal="weight_loss", day_type=DayType.REST,
            fatigue_score=80, plateau_risk=False, weight_kg=70
        )
        assert target.value == pytest.approx(1850.0)  # 2000 - 300 + 150

    def test_minimum_calories_1200(self):
        # Even extreme deficit, min 1200
        target = _compute_calorie_target(
            tdee=500, goal="weight_loss", day_type=DayType.REST,
            fatigue_score=20, plateau_risk=False, weight_kg=70
        )
        assert target.value >= 1200.0

    def test_no_tdee_uses_weight_estimate(self):
        target = _compute_calorie_target(
            tdee=None, goal="maintenance", day_type=DayType.REST,
            fatigue_score=20, plateau_risk=False, weight_kg=70
        )
        assert target.value > 0


# ── _compute_protein_target ───────────────────────────────────────────────────

class TestComputeProteinTarget:
    def test_rest_day_1_6_g_per_kg(self):
        target = _compute_protein_target(weight_kg=75, day_type=DayType.REST)
        assert target.value == pytest.approx(120.0)  # 75 × 1.6

    def test_training_day_1_8_g_per_kg(self):
        target = _compute_protein_target(weight_kg=75, day_type=DayType.TRAINING)
        assert target.value == pytest.approx(135.0)  # 75 × 1.8

    def test_intense_training_2_0_g_per_kg(self):
        target = _compute_protein_target(weight_kg=80, day_type=DayType.INTENSE_TRAINING)
        assert target.value == pytest.approx(160.0)  # 80 × 2.0

    def test_recovery_2_2_g_per_kg(self):
        target = _compute_protein_target(weight_kg=80, day_type=DayType.RECOVERY)
        assert target.value == pytest.approx(176.0)  # 80 × 2.2

    def test_recovery_priority_critical(self):
        target = _compute_protein_target(weight_kg=70, day_type=DayType.RECOVERY)
        assert target.priority == "critical"

    def test_default_weight_when_none(self):
        target = _compute_protein_target(weight_kg=None, day_type=DayType.REST)
        assert target.value == pytest.approx(70 * 1.6)  # default 70 kg


# ── _compute_carb_target ──────────────────────────────────────────────────────

class TestComputeCarbTarget:
    def test_rest_2_5_g_per_kg(self):
        target = _compute_carb_target(weight_kg=80, day_type=DayType.REST, glycogen_status="normal")
        assert target.value == pytest.approx(200.0)  # 80 × 2.5

    def test_intense_5_5_g_per_kg(self):
        target = _compute_carb_target(weight_kg=80, day_type=DayType.INTENSE_TRAINING, glycogen_status="normal")
        assert target.value == pytest.approx(440.0)  # 80 × 5.5

    def test_depleted_glycogen_adds_bonus(self):
        target_normal = _compute_carb_target(80, DayType.TRAINING, "normal")
        target_depleted = _compute_carb_target(80, DayType.TRAINING, "depleted")
        assert target_depleted.value == target_normal.value + 40  # +0.5 × 80

    def test_intense_training_carbs_for_80kg(self):
        target = _compute_carb_target(weight_kg=80, day_type=DayType.INTENSE_TRAINING, glycogen_status="normal")
        assert target.value >= 400  # must be ≥ 5g/kg × 80kg


# ── _compute_fat_target ───────────────────────────────────────────────────────

class TestComputeFatTarget:
    def test_fat_from_remaining_calories(self):
        # 2000 kcal, 150g protein (600), 200g carbs (800) → remaining 600 / 9 ≈ 67
        target = _compute_fat_target(
            calorie_target=2000, protein_g=150, carb_g=200, weight_kg=70
        )
        expected_from_remaining = (2000 - 150*4 - 200*4) / 9
        expected = max(70*0.7, min(70*1.5, expected_from_remaining))
        assert target.value == pytest.approx(expected, abs=2)

    def test_fat_min_0_7_per_kg(self):
        # Very high protein + carbs → fat from remaining may be negative, clamped
        target = _compute_fat_target(2000, protein_g=300, carb_g=400, weight_kg=70)
        assert target.value >= 70 * 0.7

    def test_fat_max_1_5_per_kg(self):
        # Very low other macros → fat from remaining could be too high
        target = _compute_fat_target(5000, protein_g=50, carb_g=50, weight_kg=70)
        assert target.value <= 70 * 1.5


# ── _compute_hydration_target ─────────────────────────────────────────────────

class TestComputeHydrationTarget:
    def test_rest_day_35ml_per_kg(self):
        target = _compute_hydration_target(weight_kg=70, day_type=DayType.REST)
        assert target.value == pytest.approx(70 * 35)

    def test_training_adds_500ml(self):
        target = _compute_hydration_target(weight_kg=70, day_type=DayType.TRAINING)
        assert target.value == pytest.approx(70 * 35 + 500)

    def test_intense_adds_1000ml(self):
        target = _compute_hydration_target(weight_kg=70, day_type=DayType.INTENSE_TRAINING)
        assert target.value == pytest.approx(70 * 35 + 1000)


# ── _fasting_compatible ───────────────────────────────────────────────────────

class TestFastingCompatible:
    def test_no_if_protocol_not_compatible(self):
        ok, _ = _fasting_compatible(DayType.REST, "normal", 20, has_if_protocol=False)
        assert ok is False

    def test_depleted_glycogen_training_not_compatible(self):
        ok, reason = _fasting_compatible(DayType.TRAINING, "depleted", 20, has_if_protocol=True)
        assert ok is False
        assert "glycogène" in reason.lower() or "depleted" in reason.lower() or "bas" in reason.lower()

    def test_high_fatigue_not_compatible(self):
        ok, reason = _fasting_compatible(DayType.REST, "normal", 75, has_if_protocol=True)
        assert ok is False
        assert "fatigue" in reason.lower()

    def test_intense_training_not_compatible(self):
        ok, _ = _fasting_compatible(DayType.INTENSE_TRAINING, "normal", 20, has_if_protocol=True)
        assert ok is False

    def test_rest_day_normal_compatible(self):
        ok, _ = _fasting_compatible(DayType.REST, "normal", 20, has_if_protocol=True)
        assert ok is True

    def test_recovery_day_compatible(self):
        ok, _ = _fasting_compatible(DayType.RECOVERY, "normal", 40, has_if_protocol=True)
        assert ok is True


# ── compute_adaptive_plan ─────────────────────────────────────────────────────

class TestComputeAdaptivePlan:
    def test_basic_plan_returns_all_fields(self):
        plan = compute_adaptive_plan(weight_kg=75, goal="maintenance", tdee=2000)
        assert isinstance(plan, AdaptiveNutritionPlan)
        assert plan.calorie_target.value > 0
        assert plan.protein_target.value > 0
        assert plan.carb_target.value > 0
        assert plan.fat_target.value > 0
        assert plan.hydration_target.value > 0

    def test_intense_training_carbs_elevated_for_80kg(self):
        plan = compute_adaptive_plan(
            day_type_hint="intense_training",
            weight_kg=80, goal="muscle_gain", tdee=2800,
        )
        assert plan.carb_target.value >= 400  # 5 g/kg × 80 kg

    def test_recovery_day_protein_highest(self):
        plan = compute_adaptive_plan(
            day_type_hint="recovery",
            weight_kg=70, goal="muscle_gain", tdee=2200,
        )
        # Recovery protein = 2.2 g/kg = 154 g
        assert plan.protein_target.value == pytest.approx(154.0)

    def test_confidence_low_without_data(self):
        plan = compute_adaptive_plan()
        assert plan.confidence < 0.5

    def test_confidence_high_with_full_data(self):
        plan = compute_adaptive_plan(
            tdee=2000, weight_kg=70,
            readiness_score=75, training_load_today=80,
        )
        assert plan.confidence == 1.0

    def test_plateau_switches_to_maintenance(self):
        plan_loss = compute_adaptive_plan(goal="weight_loss", tdee=2000, weight_kg=70, plateau_risk=False)
        plan_plateau = compute_adaptive_plan(goal="weight_loss", tdee=2000, weight_kg=70, plateau_risk=True)
        assert plan_loss.calorie_target.value < plan_plateau.calorie_target.value

    def test_day_type_hint_respected(self):
        plan = compute_adaptive_plan(day_type_hint="deload", weight_kg=70, tdee=2000)
        assert plan.day_type == DayType.DELOAD

    def test_pre_workout_guidance_for_training(self):
        plan = compute_adaptive_plan(day_type_hint="training", weight_kg=70, tdee=2000)
        assert plan.pre_workout_guidance is not None

    def test_no_pre_workout_for_rest(self):
        plan = compute_adaptive_plan(day_type_hint="rest", weight_kg=70, tdee=2000)
        assert plan.pre_workout_guidance is None

    def test_alerts_for_glycogen_depleted_training(self):
        plan = compute_adaptive_plan(
            day_type_hint="training", glycogen_status="depleted",
            weight_kg=70, tdee=2000
        )
        assert len(plan.alerts) > 0

    def test_supplementation_not_empty_for_intense(self):
        plan = compute_adaptive_plan(
            day_type_hint="intense_training", weight_kg=70, tdee=2500
        )
        assert len(plan.supplementation_focus) > 0

    def test_fasting_not_compatible_with_intense(self):
        plan = compute_adaptive_plan(
            day_type_hint="intense_training", weight_kg=70, tdee=2500,
            has_if_protocol=True
        )
        assert plan.fasting_compatible is False


# ── build_adaptive_nutrition_summary ─────────────────────────────────────────

class TestBuildAdaptiveNutritionSummary:
    def test_summary_is_string(self):
        plan = compute_adaptive_plan(weight_kg=70, tdee=2000)
        assert isinstance(build_adaptive_nutrition_summary(plan), str)

    def test_summary_contains_day_type(self):
        plan = compute_adaptive_plan(day_type_hint="training", weight_kg=70, tdee=2000)
        summary = build_adaptive_nutrition_summary(plan)
        assert "training" in summary.lower() or "entraînement" in summary.lower()

    def test_summary_compact(self):
        plan = compute_adaptive_plan(weight_kg=70, tdee=2000)
        assert len(build_adaptive_nutrition_summary(plan)) < 300
