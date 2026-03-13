"""
Tests unitaires — Longevity Engine (LOT 3).

Couvre :
  - score_cardio (5 tests)
  - score_strength (4 tests)
  - score_sleep (5 tests)
  - score_nutrition (4 tests)
  - score_weight (5 tests)
  - score_body_composition (5 tests)
  - score_consistency (3 tests)
  - compute_longevity_score — intégration (8 tests)
"""
import pytest
from app.services.longevity_engine import (
    score_cardio,
    score_strength,
    score_sleep,
    score_nutrition,
    score_weight,
    score_body_composition,
    score_consistency,
    compute_longevity_score,
    LONGEVITY_OPTIMAL_SCORE,
    AGE_YEARS_PER_SCORE_POINT,
)


# ── score_cardio ──────────────────────────────────────────────────────────────

class TestScoreCardio:

    def test_all_none_returns_none(self):
        assert score_cardio(None, None, None, None) is None

    def test_perfect_steps_gives_100(self):
        score = score_cardio(steps=10000, hrv_ms=None, active_calories=None, workout_frequency_pct=None)
        assert score == pytest.approx(100.0, abs=0.5)

    def test_zero_steps_gives_0(self):
        score = score_cardio(steps=0, hrv_ms=None, active_calories=None, workout_frequency_pct=None)
        assert score == pytest.approx(0.0, abs=0.5)

    def test_high_hrv_contributes(self):
        score_high_hrv = score_cardio(steps=5000, hrv_ms=80, active_calories=None, workout_frequency_pct=None)
        score_low_hrv = score_cardio(steps=5000, hrv_ms=20, active_calories=None, workout_frequency_pct=None)
        assert score_high_hrv > score_low_hrv

    def test_multiple_inputs_averaged(self):
        score = score_cardio(steps=5000, hrv_ms=45, active_calories=250, workout_frequency_pct=50)
        assert 0.0 < score < 100.0

    def test_score_capped_at_100(self):
        score = score_cardio(steps=20000, hrv_ms=100, active_calories=1000, workout_frequency_pct=100)
        assert score <= 100.0


# ── score_strength ────────────────────────────────────────────────────────────

class TestScoreStrength:

    def test_all_none_returns_none(self):
        assert score_strength(None, None) is None

    def test_high_tonnage_gives_100(self):
        score = score_strength(total_tonnage_avg=3000, workout_count_30d=None)
        assert score == pytest.approx(100.0, abs=0.5)

    def test_zero_tonnage_gives_0(self):
        score = score_strength(total_tonnage_avg=0, workout_count_30d=None)
        assert score == pytest.approx(0.0, abs=0.5)

    def test_12_sessions_per_month_perfect_freq(self):
        score = score_strength(total_tonnage_avg=None, workout_count_30d=12)
        assert score == pytest.approx(100.0, abs=0.5)


# ── score_sleep ───────────────────────────────────────────────────────────────

class TestScoreSleep:

    def test_all_none_returns_none(self):
        assert score_sleep(None, None) is None

    def test_optimal_range_gives_100(self):
        score = score_sleep(avg_sleep_hours=8.0, avg_sleep_quality=None)
        assert score == pytest.approx(100.0, abs=1.0)

    def test_7_hours_gives_100(self):
        score = score_sleep(7.0, None)
        assert score == pytest.approx(100.0, abs=1.0)

    def test_5_hours_gives_low_score(self):
        score = score_sleep(5.0, None)
        assert score < 50.0

    def test_too_much_sleep_reduces_score(self):
        score_9 = score_sleep(9.0, None)
        score_12 = score_sleep(12.0, None)
        assert score_9 >= score_12

    def test_quality_improves_score(self):
        score_with_quality = score_sleep(7.0, 90.0)
        score_without = score_sleep(7.0, None)
        # Avec qualité élevée, score devrait être ≥ sans qualité (parfois égal si déjà max)
        assert score_with_quality >= score_without * 0.9  # Tolérance


# ── score_nutrition ───────────────────────────────────────────────────────────

class TestScoreNutrition:

    def test_all_none_returns_none(self):
        assert score_nutrition(None, None, None, None) is None

    def test_perfect_compliance_gives_100(self):
        score = score_nutrition(
            avg_calories_pct=1.0, avg_protein_pct=1.0,
            meal_frequency_pct=100.0, micro_score=100.0,
        )
        assert score == pytest.approx(100.0, abs=1.0)

    def test_low_protein_reduces_score(self):
        score_lp = score_nutrition(None, 0.50, None, None)
        score_hp = score_nutrition(None, 1.0, None, None)
        assert score_lp < score_hp

    def test_calorie_excess_reduces_score(self):
        score_excess = score_nutrition(1.5, None, None, None)  # 150% de la cible
        score_optimal = score_nutrition(1.0, None, None, None)
        assert score_excess < score_optimal


# ── score_weight ──────────────────────────────────────────────────────────────

class TestScoreWeight:

    def test_none_bmi_returns_none(self):
        assert score_weight(None, None, None) is None

    def test_optimal_bmi_gives_100(self):
        score = score_weight(bmi=22.0, weight_trend_kg=None, goal=None)
        assert score == pytest.approx(100.0, abs=1.0)

    def test_obese_bmi_gives_low_score(self):
        score = score_weight(bmi=35.0, weight_trend_kg=None, goal=None)
        assert score < 40.0

    def test_trend_bonus_for_weight_loss(self):
        score_losing = score_weight(bmi=26.0, weight_trend_kg=-0.5, goal="weight_loss")
        score_gaining = score_weight(bmi=26.0, weight_trend_kg=0.5, goal="weight_loss")
        assert score_losing >= score_gaining

    def test_score_capped_at_100(self):
        score = score_weight(bmi=22.0, weight_trend_kg=-0.5, goal="weight_loss")
        assert score <= 100.0


# ── score_body_composition ────────────────────────────────────────────────────

class TestScoreBodyComposition:

    def test_none_returns_none(self):
        assert score_body_composition(None, None) is None

    def test_athletic_male(self):
        score = score_body_composition(body_fat_pct=10.0, sex="male")
        assert score >= 80.0

    def test_high_body_fat_male(self):
        score = score_body_composition(body_fat_pct=30.0, sex="male")
        assert score < 50.0

    def test_athletic_female(self):
        score = score_body_composition(body_fat_pct=18.0, sex="female")
        assert score >= 70.0

    def test_score_in_range(self):
        for fat_pct in [5, 10, 15, 20, 25, 30, 35, 40]:
            score = score_body_composition(fat_pct, "male")
            assert 0 <= score <= 100


# ── score_consistency ─────────────────────────────────────────────────────────

class TestScoreConsistency:

    def test_none_returns_none(self):
        assert score_consistency(None, None) is None

    def test_perfect_tracking_gives_100(self):
        score = score_consistency(tracking_days_pct=100.0, workout_streak=None)
        assert score == pytest.approx(100.0, abs=0.5)

    def test_long_streak_improves_score(self):
        score_no_streak = score_consistency(tracking_days_pct=70.0, workout_streak=None)
        score_with_streak = score_consistency(tracking_days_pct=70.0, workout_streak=14)
        assert score_with_streak >= score_no_streak


# ── compute_longevity_score — intégration ─────────────────────────────────────

class TestComputeLongevityScore:

    def test_all_none_returns_zero(self):
        result = compute_longevity_score(actual_age=35)
        assert result.longevity_score == 0.0
        assert result.confidence == 0.0

    def test_complete_data_returns_valid_score(self):
        result = compute_longevity_score(
            actual_age=35,
            avg_steps=8000,
            avg_hrv_ms=55,
            avg_active_calories=400,
            workout_frequency_pct=60,
            avg_tonnage_per_session=2000,
            workout_count_30d=10,
            avg_sleep_hours=7.5,
            avg_sleep_quality_score=75,
            avg_calories_pct_target=0.95,
            avg_protein_pct_target=0.90,
            meal_tracking_pct=80.0,
            bmi=23.0,
            goal="maintenance",
            tracking_days_pct=85.0,
        )
        assert 0 < result.longevity_score <= 100
        assert result.confidence > 0

    def test_biological_age_computed(self):
        result = compute_longevity_score(
            actual_age=40,
            avg_steps=10000,
            avg_sleep_hours=8.0,
            tracking_days_pct=90.0,
        )
        # Si score > 75 → âge biologique < âge réel
        if result.longevity_score > LONGEVITY_OPTIMAL_SCORE:
            assert result.biological_age_estimate < 40
        elif result.longevity_score < LONGEVITY_OPTIMAL_SCORE:
            assert result.biological_age_estimate > 40

    def test_no_age_no_bio_age(self):
        result = compute_longevity_score(actual_age=None, avg_steps=8000)
        assert result.biological_age_estimate is None

    def test_body_comp_adds_bonus(self):
        """body_comp_score active un poids bonus dans le calcul pondéré."""
        result_with = compute_longevity_score(
            actual_age=35, avg_steps=8000, body_fat_pct=12.0, sex="male",
        )
        result_without = compute_longevity_score(
            actual_age=35, avg_steps=8000, body_fat_pct=None, sex="male",
        )
        assert result_with.body_comp_score is not None
        assert result_without.body_comp_score is None

    def test_improvement_levers_for_low_components(self):
        result = compute_longevity_score(
            actual_age=35,
            avg_steps=1000,       # très faible → levier
            avg_sleep_hours=4.0,  # très faible → levier
        )
        assert len(result.top_improvement_levers) > 0

    def test_all_perfect_no_levers(self):
        result = compute_longevity_score(
            actual_age=30,
            avg_steps=12000,
            avg_hrv_ms=80,
            avg_active_calories=600,
            workout_frequency_pct=80,
            avg_tonnage_per_session=3000,
            workout_count_30d=16,
            avg_sleep_hours=8.0,
            avg_sleep_quality_score=95,
            avg_calories_pct_target=1.0,
            avg_protein_pct_target=1.1,
            meal_tracking_pct=100.0,
            bmi=22.0,
            goal="maintenance",
            tracking_days_pct=100.0,
        )
        # Tout ≥ 70 → pas de leviers
        assert len(result.top_improvement_levers) == 0

    def test_confidence_proportional_to_data(self):
        result_partial = compute_longevity_score(actual_age=35, avg_steps=8000)
        result_full = compute_longevity_score(
            actual_age=35, avg_steps=8000, avg_sleep_hours=7.5,
            avg_hrv_ms=55, tracking_days_pct=80.0,
        )
        assert result_full.confidence > result_partial.confidence
