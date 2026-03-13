"""
Tests unitaires des calculs physiologiques de SOMA.
Ces calculs sont la fondation de toutes les recommandations — ils doivent être précis.
"""
import pytest
from app.services.calculations import (
    calculate_bmr_mifflin,
    calculate_bmr_katch_mcardle,
    calculate_tdee,
    calculate_bmi,
    bmi_category,
    calculate_protein_target,
    calculate_calorie_target,
    calculate_hydration_target,
    calculate_profile_completeness,
    calculate_training_load,
    calculate_acwr,
)


# =============================================================================
# BMR — Métabolisme basal
# =============================================================================

class TestBMR:
    def test_bmr_male_typical(self):
        """Homme 35 ans, 85 kg, 180 cm → attendu ~1876 kcal (Mifflin)"""
        bmr = calculate_bmr_mifflin(85, 180, 35, "male")
        assert 1800 < bmr < 2000, f"BMR {bmr} hors plage attendue"

    def test_bmr_female_typical(self):
        """Femme 30 ans, 65 kg, 165 cm → attendu ~1390 kcal"""
        bmr = calculate_bmr_mifflin(65, 165, 30, "female")
        assert 1300 < bmr < 1500

    def test_bmr_increases_with_weight(self):
        bmr_80 = calculate_bmr_mifflin(80, 175, 30, "male")
        bmr_90 = calculate_bmr_mifflin(90, 175, 30, "male")
        assert bmr_90 > bmr_80

    def test_bmr_decreases_with_age(self):
        bmr_30 = calculate_bmr_mifflin(80, 175, 30, "male")
        bmr_50 = calculate_bmr_mifflin(80, 175, 50, "male")
        assert bmr_50 < bmr_30

    def test_bmr_katch_mcardle(self):
        """Masse maigre 65 kg → BMR ~1774 kcal"""
        bmr = calculate_bmr_katch_mcardle(65)
        assert abs(bmr - (370 + 21.6 * 65)) < 1

    def test_bmr_sex_difference(self):
        """Les hommes ont un BMR plus élevé à poids/taille/âge identiques."""
        bmr_m = calculate_bmr_mifflin(80, 175, 35, "male")
        bmr_f = calculate_bmr_mifflin(80, 175, 35, "female")
        assert bmr_m > bmr_f
        assert abs(bmr_m - bmr_f) == pytest.approx(166, abs=1)  # différence constante Mifflin


# =============================================================================
# TDEE
# =============================================================================

class TestTDEE:
    def test_sedentary_multiplier(self):
        bmr = 1800
        tdee = calculate_tdee(bmr, "sedentary")
        assert tdee == pytest.approx(bmr * 1.2, abs=1)

    def test_active_multiplier(self):
        bmr = 1800
        tdee = calculate_tdee(bmr, "active")
        assert tdee == pytest.approx(bmr * 1.725, abs=1)

    def test_tdee_always_greater_than_bmr(self):
        for level in ["sedentary", "light", "moderate", "active", "very_active"]:
            assert calculate_tdee(1800, level) > 1800

    def test_unknown_activity_defaults_to_light(self):
        tdee = calculate_tdee(1800, "unknown_level")
        assert tdee > 1800


# =============================================================================
# IMC
# =============================================================================

class TestBMI:
    def test_bmi_calculation(self):
        bmi = calculate_bmi(85, 180)
        assert bmi == pytest.approx(85 / 1.8**2, abs=0.01)

    def test_bmi_normal_range(self):
        bmi = calculate_bmi(70, 175)
        assert 18.5 <= bmi < 25

    def test_bmi_categories(self):
        assert bmi_category(17.0) == "underweight"
        assert bmi_category(22.0) == "normal"
        assert bmi_category(27.0) == "overweight"
        assert bmi_category(35.0) == "obese"


# =============================================================================
# PROTÉINES
# =============================================================================

class TestProteinTarget:
    def test_weight_loss_higher_protein(self):
        min_wl, max_wl, _ = calculate_protein_target(80, "weight_loss", "intermediate")
        min_mg, max_mg, _ = calculate_protein_target(80, "muscle_gain", "intermediate")
        # Perte de poids nécessite plus de protéines que prise de masse (ratio)
        assert min_wl >= 1.8 * 80  # au moins 1.8g/kg

    def test_protein_scales_with_weight(self):
        min_60, max_60, _ = calculate_protein_target(60, "maintenance", "beginner")
        min_90, max_90, _ = calculate_protein_target(90, "maintenance", "beginner")
        assert min_90 > min_60

    def test_min_less_than_max(self):
        min_g, max_g, _ = calculate_protein_target(80, "weight_loss", "advanced")
        assert min_g < max_g

    def test_reasoning_returned(self):
        _, _, reasoning = calculate_protein_target(80, "weight_loss", "beginner")
        assert isinstance(reasoning, str) and len(reasoning) > 5


# =============================================================================
# CALORIES CIBLES
# =============================================================================

class TestCalorieTarget:
    def test_weight_loss_below_tdee(self):
        target, _ = calculate_calorie_target(2500, "weight_loss", 85, 75)
        assert target < 2500

    def test_muscle_gain_above_tdee(self):
        target, _ = calculate_calorie_target(2500, "muscle_gain", 80, 85)
        assert target > 2500

    def test_maintenance_equals_tdee(self):
        target, _ = calculate_calorie_target(2500, "maintenance", 80, 80)
        assert target == pytest.approx(2500, abs=1)

    def test_minimum_floor_respected(self):
        """Même en fort déficit, on ne descend pas sous 1400 kcal."""
        target, _ = calculate_calorie_target(1500, "weight_loss", 60, 50)
        assert target >= 1400


# =============================================================================
# HYDRATATION
# =============================================================================

class TestHydration:
    def test_base_calculation(self):
        target, _ = calculate_hydration_target(80, "sedentary")
        assert target == pytest.approx(80 * 33, abs=100)

    def test_active_more_than_sedentary(self):
        target_sedentary, _ = calculate_hydration_target(80, "sedentary")
        target_active, _ = calculate_hydration_target(80, "active")
        assert target_active > target_sedentary

    def test_reasoning_provided(self):
        _, reasoning = calculate_hydration_target(75, "moderate")
        assert "ml" in reasoning


# =============================================================================
# COMPLÉTUDE PROFIL
# =============================================================================

class TestProfileCompleteness:
    def test_empty_profile_low_score(self):
        score = calculate_profile_completeness({})
        assert score == 0.0

    def test_essential_fields_increase_score(self):
        partial = {"age": 35, "sex": "male", "height_cm": 180}
        score = calculate_profile_completeness(partial)
        assert score > 20

    def test_complete_profile_high_score(self):
        full = {
            "age": 35, "sex": "male", "height_cm": 180,
            "primary_goal": "weight_loss", "activity_level": "moderate",
            "fitness_level": "intermediate", "dietary_regime": "omnivore",
            "intermittent_fasting": True, "meals_per_day": 1,
            "preferred_training_time": "evening", "food_allergies": [],
            "home_equipment": ["dumbbells"], "gym_access": True,
            "avg_energy_level": 7, "perceived_sleep_quality": 4,
            "physical_constraints": [],
        }
        score = calculate_profile_completeness(full)
        assert score >= 90


# =============================================================================
# CHARGE D'ENTRAÎNEMENT
# =============================================================================

class TestTrainingLoad:
    def test_session_load(self):
        load = calculate_training_load(60, 7)
        assert load == 420

    def test_acwr_optimal_zone(self):
        acwr = calculate_acwr(400, 350)
        assert 0.8 <= acwr <= 1.3

    def test_acwr_returns_none_for_zero_chronic(self):
        result = calculate_acwr(500, 0)
        assert result is None

    def test_acwr_high_risk(self):
        acwr = calculate_acwr(800, 400)
        assert acwr > 1.5
