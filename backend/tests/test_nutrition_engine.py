"""
Tests unitaires — Nutrition Engine (LOT 3).

Couvre :
  - compute_workout_calorie_bonus (5 tests)
  - compute_fat_target_g (5 tests)
  - compute_carbs_target_g (5 tests)
  - compute_fiber_target_g (3 tests)
  - compute_macro_percentages (4 tests)
  - compute_fasting_window (5 tests)
  - compute_nutrition_targets — intégration (8 tests)
"""
import pytest
from app.services.nutrition_engine import (
    compute_workout_calorie_bonus,
    compute_fat_target_g,
    compute_carbs_target_g,
    compute_fiber_target_g,
    compute_macro_percentages,
    compute_fasting_window,
    compute_nutrition_targets,
    WORKOUT_CALORIE_BONUS,
    FAT_RATIO_BY_GOAL,
    KCAL_PER_G,
)


# ── compute_workout_calorie_bonus ──────────────────────────────────────────────

class TestComputeWorkoutCalorieBonus:

    def test_no_duration_returns_zero(self):
        assert compute_workout_calorie_bonus("strength", None, None) == 0.0

    def test_zero_duration_returns_zero(self):
        assert compute_workout_calorie_bonus("cardio", 0, None) == 0.0

    def test_strength_60min_no_rpe(self):
        bonus = compute_workout_calorie_bonus("strength", 60, None)
        assert bonus == 250.0  # 250 kcal/h × 1h × 1.0 (rpe=1.0 par défaut)

    def test_hiit_30min_rpe10(self):
        bonus = compute_workout_calorie_bonus("hiit", 30, 10)
        # 450 kcal/h × 0.5h × 1.5 (rpe_factor max)
        expected = round(450 * 0.5 * 1.5, 0)
        assert bonus == expected

    def test_unknown_type_uses_default(self):
        bonus = compute_workout_calorie_bonus("unknown_type", 60, None)
        assert bonus == float(WORKOUT_CALORIE_BONUS["default"])

    def test_mobility_45min(self):
        bonus = compute_workout_calorie_bonus("mobility", 45, None)
        assert bonus == round(100 * 0.75, 0)  # 75 kcal

    def test_rpe_5_gives_factor_1(self):
        # RPE 5 → factor = 0.7 + (5/10) * 0.8 = 1.1
        bonus = compute_workout_calorie_bonus("cardio", 60, 5)
        expected = round(400 * 1.0 * (0.7 + 0.5 * 0.8), 0)
        assert bonus == expected


# ── compute_fat_target_g ───────────────────────────────────────────────────────

class TestComputeFatTargetG:

    def test_weight_loss_goal(self):
        fat = compute_fat_target_g(2000, "weight_loss")
        # 2000 × 0.30 / 9
        expected = round(2000 * 0.30 / 9, 1)
        assert fat == expected

    def test_muscle_gain_goal(self):
        fat = compute_fat_target_g(2500, "muscle_gain")
        expected = round(2500 * 0.25 / 9, 1)
        assert fat == expected

    def test_longevity_goal_highest_fat(self):
        fat = compute_fat_target_g(2000, "longevity")
        expected = round(2000 * 0.35 / 9, 1)
        assert fat == expected

    def test_unknown_goal_uses_maintenance(self):
        fat_unknown = compute_fat_target_g(2000, "unknown")
        fat_maint = compute_fat_target_g(2000, "maintenance")
        assert fat_unknown == fat_maint

    def test_none_goal_uses_maintenance(self):
        fat_none = compute_fat_target_g(2000, None)
        fat_maint = compute_fat_target_g(2000, "maintenance")
        assert fat_none == fat_maint


# ── compute_carbs_target_g ────────────────────────────────────────────────────

class TestComputeCarbsTargetG:

    def test_basic_residual(self):
        # 2000 kcal, 150g prot (600 kcal), 55g fat (495 kcal) → 905 kcal / 4 = 226.25g
        carbs = compute_carbs_target_g(2000, 150, 55)
        assert carbs == round((2000 - 150 * 4 - 55 * 9) / 4, 1)

    def test_zero_floor(self):
        # Protéines + lipides dépassent les calories → 0
        carbs = compute_carbs_target_g(1000, 200, 60)
        assert carbs >= 0

    def test_high_protein_leaves_less_carbs(self):
        carbs_hp = compute_carbs_target_g(2000, 250, 50)
        carbs_lp = compute_carbs_target_g(2000, 100, 50)
        assert carbs_hp < carbs_lp

    def test_symmetry(self):
        cal = 2500.0
        prot = 180.0
        fat = 70.0
        carbs = compute_carbs_target_g(cal, prot, fat)
        # Vérification : prot_kcal + fat_kcal + carbs_kcal ≈ cal
        total = prot * 4 + fat * 9 + carbs * 4
        assert abs(total - cal) < 1.0

    def test_no_energy_means_zero_carbs(self):
        carbs = compute_carbs_target_g(0, 0, 0)
        assert carbs == 0.0


# ── compute_fiber_target_g ────────────────────────────────────────────────────

class TestComputeFiberTargetG:

    def test_2000_kcal(self):
        assert compute_fiber_target_g(2000) == 28.0  # 14 * 2

    def test_1000_kcal(self):
        assert compute_fiber_target_g(1000) == 14.0

    def test_proportional(self):
        assert compute_fiber_target_g(3000) == pytest.approx(42.0, abs=0.1)


# ── compute_macro_percentages ─────────────────────────────────────────────────

class TestComputeMacroPercentages:

    def test_typical_values(self):
        prot_pct, carbs_pct, fat_pct = compute_macro_percentages(2000, 150, 200, 67)
        # Protéines : 150*4=600 / 2000 = 30%
        assert prot_pct == pytest.approx(30.0, abs=0.5)
        # Total ≈ 100%
        assert prot_pct + carbs_pct + fat_pct == pytest.approx(100.0, abs=0.5)

    def test_zero_calories_returns_zeros(self):
        assert compute_macro_percentages(0, 100, 100, 50) == (0.0, 0.0, 0.0)

    def test_sum_is_100(self):
        prot_pct, carbs_pct, fat_pct = compute_macro_percentages(2500, 200, 250, 70)
        assert prot_pct + carbs_pct + fat_pct == pytest.approx(100.0, abs=1.0)

    def test_high_protein_diet(self):
        # 200g prot (800 kcal) sur 2000 = 40%
        prot_pct, _, _ = compute_macro_percentages(2000, 200, 100, 55)
        assert prot_pct == pytest.approx(40.0, abs=1.0)


# ── compute_fasting_window ────────────────────────────────────────────────────

class TestComputeFastingWindow:

    def test_no_protocol_returns_none(self):
        window, start = compute_fasting_window(None)
        assert window is None
        assert start is None

    def test_16_8_protocol(self):
        window, _ = compute_fasting_window("16:8")
        assert window == 8.0

    def test_18_6_protocol(self):
        window, _ = compute_fasting_window("18:6")
        assert window == 6.0

    def test_omad_protocol(self):
        window, _ = compute_fasting_window("OMAD")
        assert window == 1.0

    def test_wake_time_computes_fasting_start(self):
        window, fasting_start = compute_fasting_window("16:8", "07:00")
        assert window == 8.0
        # Réveil 7h + fenêtre 8h = jeûne commence à 15h
        assert fasting_start == "15:00"

    def test_unknown_protocol_returns_none(self):
        window, start = compute_fasting_window("random_protocol")
        assert window is None
        assert start is None


# ── compute_nutrition_targets — intégration ───────────────────────────────────

class TestComputeNutritionTargets:

    def _default_params(self, **overrides):
        params = dict(
            age=30, sex="male", height_cm=180, weight_kg=80,
            body_fat_pct=None, activity_level="moderate",
            fitness_level="intermediate", primary_goal="maintenance",
        )
        params.update(overrides)
        return params

    def test_returns_positive_calories(self):
        result = compute_nutrition_targets(**self._default_params())
        assert result.calories_target > 0

    def test_muscle_gain_has_surplus(self):
        result = compute_nutrition_targets(**self._default_params(primary_goal="muscle_gain"))
        assert result.goal_adjustment_kcal > 0

    def test_weight_loss_has_deficit(self):
        result = compute_nutrition_targets(**self._default_params(primary_goal="weight_loss"))
        assert result.goal_adjustment_kcal < 0

    def test_training_day_has_bonus(self):
        result = compute_nutrition_targets(
            **self._default_params(),
            workout_type="strength", workout_duration_minutes=60,
        )
        assert result.workout_bonus_kcal > 0
        assert result.target_mode == "training_day"

    def test_no_training_standard_mode(self):
        result = compute_nutrition_targets(**self._default_params())
        assert result.workout_bonus_kcal == 0
        assert result.target_mode == "standard"

    def test_fasting_mode(self):
        result = compute_nutrition_targets(
            **self._default_params(),
            intermittent_fasting=True, fasting_protocol="16:8",
        )
        assert result.target_mode == "fasting"
        assert result.eating_window_hours == 8.0

    def test_macro_percentages_sum_100(self):
        result = compute_nutrition_targets(**self._default_params())
        total = result.protein_pct + result.carbs_pct + result.fat_pct
        assert total == pytest.approx(100.0, abs=2.0)

    def test_protein_positive(self):
        result = compute_nutrition_targets(**self._default_params())
        assert result.protein_target_g > 0

    def test_hydration_positive(self):
        result = compute_nutrition_targets(**self._default_params())
        assert result.hydration_target_ml > 0

    def test_female_has_reasoning(self):
        result = compute_nutrition_targets(
            **self._default_params(sex="female", weight_kg=60, height_cm=165)
        )
        assert len(result.reasoning) > 10
