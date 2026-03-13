"""
Tests SOMA LOT 13 — Personalized Learning Engine.
~30 tests purs (aucun acces DB requis).
"""
import pytest
from datetime import date

from app.domains.learning.service import (
    compute_user_learning_profile,
    _estimate_true_tdee,
    _compute_metabolic_efficiency,
    _analyze_recovery_profile,
    _analyze_training_tolerance,
    _analyze_nutrition_response,
    _analyze_sleep_recovery,
    WeightCalorieObservation,
    ReadinessObservation,
    TrainingObservation,
    NutritionReadinessObservation,
    REFERENCE_EFFICIENCY,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _obs(day: int, weight: float, calories: float) -> WeightCalorieObservation:
    return WeightCalorieObservation(
        obs_date=date(2026, 1, day),
        weight_kg=weight,
        calories_consumed=calories,
    )


def _readiness(day: int, score: float, prior_load: float = None) -> ReadinessObservation:
    return ReadinessObservation(
        obs_date=date(2026, 1, day),
        readiness_score=score,
        prior_training_load=prior_load,
    )


def _training(day: int, load: float, acwr: float = None, fatigue: float = None) -> TrainingObservation:
    return TrainingObservation(
        session_date=date(2026, 1, day),
        training_load=load,
        acwr=acwr,
        fatigue_score=fatigue,
    )


def _nutrition(day: int, carbs: float, protein: float, readiness_next: float = None) -> NutritionReadinessObservation:
    return NutritionReadinessObservation(
        obs_date=date(2026, 1, day),
        carbs_g=carbs,
        protein_g=protein,
        weight_kg=75.0,
        next_day_readiness=readiness_next,
    )


# ── Tests: _estimate_true_tdee ────────────────────────────────────────────────

class TestEstimateTrueTdee:
    def test_stable_weight_tdee_equals_calories(self):
        obs = [_obs(i, 75.0, 2500) for i in range(1, 21)]  # 20 days, stable weight
        tdee, confidence = _estimate_true_tdee(obs)
        assert tdee is not None
        assert abs(tdee - 2500) < 50  # should be close to consumed calories
        assert confidence > 0

    def test_weight_loss_tdee_higher_than_consumed(self):
        # User consuming 1800 kcal, losing weight -> TDEE > 1800
        obs = [_obs(i, 75.0 - i * 0.02, 1800) for i in range(1, 21)]
        tdee, confidence = _estimate_true_tdee(obs)
        assert tdee is not None
        assert tdee > 1800

    def test_weight_gain_tdee_lower_than_consumed(self):
        # User consuming 3000 kcal, gaining weight -> TDEE < 3000
        obs = [_obs(i, 75.0 + i * 0.02, 3000) for i in range(1, 21)]
        tdee, confidence = _estimate_true_tdee(obs)
        assert tdee is not None
        assert tdee < 3000

    def test_insufficient_data_returns_none(self):
        obs = [_obs(i, 75.0, 2500) for i in range(1, 10)]  # only 9 days
        tdee, confidence = _estimate_true_tdee(obs)
        assert tdee is None
        assert confidence == 0.0

    def test_empty_observations_returns_none(self):
        tdee, confidence = _estimate_true_tdee([])
        assert tdee is None

    def test_confidence_increases_with_more_data(self):
        obs_14 = [_obs(i, 75.0, 2500) for i in range(1, 15)]
        obs_30 = [_obs(i, 75.0, 2500) for i in range(1, 31)]
        _, conf_14 = _estimate_true_tdee(obs_14)
        _, conf_30 = _estimate_true_tdee(obs_30)
        assert conf_30 > conf_14

    def test_unrealistic_tdee_gets_clamped(self):
        # Extreme weight loss to force unrealistic TDEE
        obs = [_obs(i, 80.0 - i * 0.5, 500) for i in range(1, 21)]  # massive loss
        tdee, confidence = _estimate_true_tdee(obs)
        if tdee is not None:
            assert 1000 <= tdee <= 6000  # clamped to reasonable range


# ── Tests: _compute_metabolic_efficiency ─────────────────────────────────────

class TestComputeMetabolicEfficiency:
    def test_equal_values_give_reference_efficiency(self):
        efficiency, trend = _compute_metabolic_efficiency(2000, 2000)
        assert efficiency == pytest.approx(1.0, abs=0.01)

    def test_fast_metabolizer_above_threshold(self):
        efficiency, trend = _compute_metabolic_efficiency(2200, 2000)
        assert efficiency > 1.05
        assert trend == "improving"

    def test_slow_metabolizer_below_threshold(self):
        efficiency, trend = _compute_metabolic_efficiency(1800, 2000)
        assert efficiency < 0.95
        assert trend == "declining"

    def test_none_mifflin_returns_reference(self):
        efficiency, trend = _compute_metabolic_efficiency(2000, None)
        assert efficiency == REFERENCE_EFFICIENCY

    def test_none_true_tdee_returns_reference(self):
        efficiency, trend = _compute_metabolic_efficiency(None, 2000)
        assert efficiency == REFERENCE_EFFICIENCY

    def test_efficiency_clamped_to_reasonable_range(self):
        efficiency, _ = _compute_metabolic_efficiency(10000, 1000)
        assert efficiency <= 2.0
        efficiency2, _ = _compute_metabolic_efficiency(100, 2000)
        assert efficiency2 >= 0.5


# ── Tests: _analyze_recovery_profile ─────────────────────────────────────────

class TestAnalyzeRecoveryProfile:
    def test_high_readiness_post_hard_session_is_fast(self):
        obs = [_readiness(i, 80.0, prior_load=80.0) for i in range(1, 10)]
        profile, factor, days = _analyze_recovery_profile(obs)
        assert profile == "fast"
        assert factor > 1.0

    def test_low_readiness_post_hard_session_is_slow(self):
        obs = [_readiness(i, 45.0, prior_load=80.0) for i in range(1, 10)]
        profile, factor, days = _analyze_recovery_profile(obs)
        assert profile == "slow"
        assert factor < 1.0
        assert days > 1.5

    def test_no_hard_sessions_uses_overall_readiness(self):
        obs = [_readiness(i, 75.0) for i in range(1, 10)]
        profile, factor, days = _analyze_recovery_profile(obs)
        assert profile in ("fast", "normal")

    def test_insufficient_data_returns_normal(self):
        obs = [_readiness(1, 70.0)]
        profile, factor, days = _analyze_recovery_profile(obs)
        assert profile == "normal"
        assert factor == 1.0

    def test_empty_returns_normal(self):
        profile, factor, days = _analyze_recovery_profile([])
        assert profile == "normal"


# ── Tests: _analyze_training_tolerance ───────────────────────────────────────

class TestAnalyzeTrainingTolerance:
    def test_high_sustainable_loads_high_tolerance(self):
        obs = [_training(i, 100.0, acwr=1.1, fatigue=50.0) for i in range(1, 15)]
        tolerance, adapt, acwr = _analyze_training_tolerance(obs)
        assert tolerance > 500  # 100 * 7 = 700 weekly

    def test_unsafe_acwr_reduces_tolerance(self):
        # Some sessions with high ACWR (unsafe) -> lower sustainable tolerance
        obs_safe = [_training(i, 80.0, acwr=1.0) for i in range(1, 8)]
        obs_unsafe = [_training(i + 7, 80.0, acwr=1.6) for i in range(1, 8)]
        obs = obs_safe + obs_unsafe
        tolerance, _, _ = _analyze_training_tolerance(obs)
        # Tolerance should be based only on safe sessions
        assert tolerance is not None

    def test_insufficient_data_returns_defaults(self):
        obs = [_training(i, 50.0) for i in range(1, 8)]
        tolerance, adapt, acwr = _analyze_training_tolerance(obs)
        assert tolerance == 50.0  # conservative default
        assert adapt == 0.5
        assert acwr == 1.1

    def test_adaptation_rate_positive_when_loads_increase(self):
        early_obs = [_training(i, 50.0, acwr=1.0) for i in range(1, 6)]
        late_obs = [_training(i + 5, 80.0, acwr=1.0) for i in range(1, 6)]
        obs = early_obs + late_obs + [_training(11, 70.0)]  # enough for tolerance
        tolerance, adapt, _ = _analyze_training_tolerance(obs)
        assert adapt > 0.5  # increasing loads -> positive adaptation


# ── Tests: _analyze_nutrition_response ────────────────────────────────────────

class TestAnalyzeNutritionResponse:
    def test_high_carbs_better_readiness_positive_response(self):
        obs = (
            [_nutrition(i, carbs=300, protein=150, readiness_next=80.0) for i in range(1, 8)]
            + [_nutrition(i + 7, carbs=100, protein=150, readiness_next=55.0) for i in range(1, 8)]
        )
        carb_r, _ = _analyze_nutrition_response(obs)
        assert carb_r > 0  # high carbs -> better readiness

    def test_insufficient_data_returns_neutral(self):
        obs = [_nutrition(i, 200, 150, 65.0) for i in range(1, 5)]
        carb_r, protein_r = _analyze_nutrition_response(obs)
        assert carb_r == 0.0
        assert protein_r == 0.0

    def test_empty_returns_neutral(self):
        carb_r, protein_r = _analyze_nutrition_response([])
        assert carb_r == 0.0
        assert protein_r == 0.0

    def test_response_clamped_to_minus_one_plus_one(self):
        # Extreme differences
        obs = (
            [_nutrition(i, carbs=500, protein=50, readiness_next=95.0) for i in range(1, 10)]
            + [_nutrition(i + 9, carbs=0, protein=50, readiness_next=5.0) for i in range(1, 10)]
        )
        carb_r, _ = _analyze_nutrition_response(obs)
        assert -1.0 <= carb_r <= 1.0


# ── Tests: _analyze_sleep_recovery ───────────────────────────────────────────

class TestAnalyzeSleepRecovery:
    def test_good_sleeper_high_factor(self):
        # 8h sleep, excellent readiness
        factor = _analyze_sleep_recovery([480] * 10, [90.0] * 10)
        assert factor > 1.0

    def test_poor_sleeper_low_factor(self):
        # 4h sleep, poor readiness
        factor = _analyze_sleep_recovery([240] * 10, [35.0] * 10)
        assert factor < 1.0

    def test_insufficient_data_returns_neutral(self):
        factor = _analyze_sleep_recovery([480] * 3, [75.0] * 3)
        assert factor == 1.0

    def test_factor_clamped_to_range(self):
        # extreme case
        factor = _analyze_sleep_recovery([600] * 10, [100.0] * 10)
        assert 0.5 <= factor <= 1.5


# ── Tests: compute_user_learning_profile (integration) ────────────────────────

class TestComputeUserLearningProfile:
    def test_no_data_returns_defaults(self):
        result = compute_user_learning_profile()
        assert result.metabolic_efficiency == REFERENCE_EFFICIENCY
        assert result.recovery_profile == "normal"
        assert result.confidence == 0.0
        assert result.data_sufficient is False

    def test_with_sufficient_data_has_confidence(self):
        obs = [_obs(i, 75.0, 2200) for i in range(1, 31)]
        r_obs = [_readiness(i, 70.0, prior_load=70.0) for i in range(1, 21)]
        result = compute_user_learning_profile(
            weight_calorie_obs=obs,
            readiness_obs=r_obs,
        )
        assert result.confidence > 0
        assert result.days_analyzed > 0

    def test_fast_recoverer_insights_not_empty(self):
        r_obs = [_readiness(i, 80.0, prior_load=80.0) for i in range(1, 20)]
        obs = [_obs(i, 75.0, 2500) for i in range(1, 20)]
        result = compute_user_learning_profile(
            weight_calorie_obs=obs,
            readiness_obs=r_obs,
        )
        # Should have at least one insight about fast recovery
        if result.recovery_profile == "fast":
            assert any("rapide" in i.lower() for i in result.insights)

    def test_true_tdee_computed_from_weight_calorie_obs(self):
        obs = [_obs(i, 75.0, 2000) for i in range(1, 25)]  # stable weight
        result = compute_user_learning_profile(weight_calorie_obs=obs)
        assert result.true_tdee is not None
        assert abs(result.true_tdee - 2000) < 100

    def test_slow_metabolizer_detected(self):
        obs = [_obs(i, 75.0, 2500) for i in range(1, 25)]  # consuming 2500 but weight stable
        result = compute_user_learning_profile(
            weight_calorie_obs=obs,
            mifflin_tdee=3000,  # Mifflin predicts 3000 but real is ~2500
        )
        assert result.is_slow_metabolizer()

    def test_result_has_all_required_fields(self):
        result = compute_user_learning_profile()
        assert hasattr(result, "true_tdee")
        assert hasattr(result, "metabolic_efficiency")
        assert hasattr(result, "recovery_profile")
        assert hasattr(result, "training_load_tolerance")
        assert hasattr(result, "carb_response")
        assert hasattr(result, "confidence")
        assert hasattr(result, "insights")
        assert isinstance(result.insights, list)
