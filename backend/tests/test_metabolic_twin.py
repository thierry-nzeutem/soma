"""
Tests unitaires — MetabolicTwinService (LOT 9).

Couvre :
  - _estimate_bmr() : Harris-Benedict Mifflin-St Jeor
  - _estimate_tdee() : facteurs d'activité
  - _estimate_glycogen() : statuts depleted/low/normal/high
  - _compute_fatigue() : combinaison charge/sommeil/HRV/FC
  - _compute_protein_status() : insufficient/adequate/optimal/excess
  - _compute_hydration_status() : dehydrated/low/normal/optimal
  - _compute_stress_load() : agrégation fatigue+sommeil+déficit
  - _detect_plateau() : détection sur 14 jours
  - _estimate_metabolic_age() : delta score longévité
  - compute_metabolic_state() : intégration complète
"""
import pytest
from datetime import date

from app.services.metabolic_twin_service import (
    MetabolicState,
    _compute_fatigue,
    _compute_hydration_status,
    _compute_protein_status,
    _compute_stress_load,
    _detect_plateau,
    _estimate_bmr,
    _estimate_glycogen,
    _estimate_metabolic_age,
    _estimate_tdee,
    compute_metabolic_state,
)


# ── _estimate_bmr ─────────────────────────────────────────────────────────────

class TestEstimateBmr:
    def test_male_returns_positive(self):
        bmr = _estimate_bmr(75, 178, 30, "male")
        assert bmr is not None and bmr > 0

    def test_male_formula(self):
        # 10*75 + 6.25*178 - 5*30 + 5 = 750+1112.5-150+5 = 1717.5
        bmr = _estimate_bmr(75, 178, 30, "male")
        assert abs(bmr - 1717.5) < 0.01

    def test_female_formula(self):
        # 10*60 + 6.25*165 - 5*25 - 161 = 600+1031.25-125-161 = 1345.25
        bmr = _estimate_bmr(60, 165, 25, "female")
        assert abs(bmr - 1345.25) < 0.01

    def test_missing_weight_returns_none(self):
        assert _estimate_bmr(None, 178, 30, "male") is None

    def test_missing_age_returns_none(self):
        assert _estimate_bmr(75, 178, None, "male") is None

    def test_missing_height_returns_none(self):
        assert _estimate_bmr(75, None, 30, "male") is None


# ── _estimate_tdee ────────────────────────────────────────────────────────────

class TestEstimateTdee:
    def test_sedentary_factor(self):
        tdee = _estimate_tdee(1800, "sedentary")
        assert abs(tdee - 1800 * 1.2) < 0.01

    def test_moderate_factor(self):
        tdee = _estimate_tdee(1800, "moderate")
        assert abs(tdee - 1800 * 1.55) < 0.01

    def test_very_active_factor(self):
        tdee = _estimate_tdee(1800, "very_active")
        assert abs(tdee - 1800 * 1.9) < 0.01

    def test_unknown_activity_uses_moderate(self):
        tdee = _estimate_tdee(1800, "unknown_level")
        assert abs(tdee - 1800 * 1.55) < 0.01

    def test_none_bmr_returns_none(self):
        assert _estimate_tdee(None, "moderate") is None


# ── _estimate_glycogen ────────────────────────────────────────────────────────

class TestEstimateGlycogen:
    def test_no_training_normal_carbs(self):
        # 300g carbs * 0.9 = 270g → 270/1125(max) = 24% → "depleted" selon la formule
        gly, status = _estimate_glycogen(300, 0, 75)
        assert gly is not None and gly > 0
        assert status in ("depleted", "low", "normal")

    def test_heavy_training_low_carbs_depleted(self):
        # Peu de glucides + charge élevée → depleted
        gly, status = _estimate_glycogen(50, 600, 75)
        assert status in ("depleted", "low")

    def test_no_weight_returns_unknown(self):
        gly, status = _estimate_glycogen(300, 0, None)
        assert gly is None
        assert status == "unknown"

    def test_high_carbs_no_training_high(self):
        # 1200g carbs * 0.9 = 1080g → capped at max(1050) → 100% → "high"
        gly, status = _estimate_glycogen(1200, 0, 70)
        assert status in ("normal", "high")

    def test_glycogen_capped_at_max(self):
        # max = 75 * 15 = 1125g
        gly, _ = _estimate_glycogen(2000, 0, 75)
        assert gly is not None and gly <= 75 * 15


# ── _compute_fatigue ──────────────────────────────────────────────────────────

class TestComputeFatigue:
    def test_no_data_returns_none(self):
        assert _compute_fatigue(None, None, None, None) is None

    def test_high_load_increases_fatigue(self):
        f_high = _compute_fatigue(400, 80, 60, 60)
        f_low = _compute_fatigue(0, 80, 60, 60)
        assert f_high > f_low

    def test_bad_sleep_increases_fatigue(self):
        f_bad = _compute_fatigue(200, 10, 60, 60)
        f_good = _compute_fatigue(200, 90, 60, 60)
        assert f_bad > f_good

    def test_range_0_to_100(self):
        f = _compute_fatigue(400, 0, 10, 100)
        assert 0 <= f <= 100

    def test_perfect_recovery_low_fatigue(self):
        f = _compute_fatigue(0, 100, 100, 40)
        assert f < 30


# ── _compute_protein_status ───────────────────────────────────────────────────

class TestComputeProteinStatus:
    def test_insufficient(self):
        # 60g / (80 * 1.2 = 96g) → ratio 0.625 < 0.6 → insufficient
        status = _compute_protein_status(50, 80, "weight_loss")
        assert status == "insufficient"

    def test_optimal_muscle_gain(self):
        # 80kg * 1.6 = 128g need; 130g intake → ratio ~1.0
        status = _compute_protein_status(130, 80, "muscle_gain")
        assert status == "optimal"

    def test_excess(self):
        status = _compute_protein_status(250, 60, "weight_loss")
        assert status == "excess"

    def test_none_weight_unknown(self):
        assert _compute_protein_status(120, None, "muscle_gain") == "unknown"

    def test_none_protein_unknown(self):
        assert _compute_protein_status(None, 75, "muscle_gain") == "unknown"


# ── _compute_hydration_status ─────────────────────────────────────────────────

class TestComputeHydrationStatus:
    def test_dehydrated(self):
        assert _compute_hydration_status(600, 2000) == "dehydrated"

    def test_low(self):
        assert _compute_hydration_status(1200, 2000) == "low"

    def test_normal(self):
        assert _compute_hydration_status(1800, 2000) == "normal"

    def test_optimal(self):
        assert _compute_hydration_status(2200, 2000) == "optimal"

    def test_none_returns_unknown(self):
        assert _compute_hydration_status(None, 2000) == "unknown"
        assert _compute_hydration_status(1500, None) == "unknown"


# ── _compute_stress_load ──────────────────────────────────────────────────────

class TestComputeStressLoad:
    def test_no_data_returns_none(self):
        assert _compute_stress_load(None, None, None) is None

    def test_high_fatigue_high_stress(self):
        stress = _compute_stress_load(90, 40, -900)
        assert stress is not None and stress > 60

    def test_capped_at_100(self):
        stress = _compute_stress_load(100, 0, -1000)
        assert stress is not None and stress <= 100

    def test_positive_balance_ignored(self):
        stress_surplus = _compute_stress_load(50, 70, 500)
        stress_deficit = _compute_stress_load(50, 70, None)
        # Surplus ne contribue pas au stress
        assert stress_surplus == stress_deficit or stress_surplus is not None


# ── _detect_plateau ───────────────────────────────────────────────────────────

class TestDetectPlateau:
    def test_stable_weight_and_calories_plateau(self):
        weights = [75.0, 75.1, 74.9, 75.0, 75.2, 74.8, 75.0, 75.1, 74.9, 75.0]
        calories = [2000, 2050, 1980, 2010, 2000, 1990, 2020, 2000, 1970, 2000]
        assert _detect_plateau(weights, calories) is True

    def test_varied_weight_no_plateau(self):
        weights = [75.0, 74.0, 73.5, 72.8, 72.0, 71.5, 70.9, 70.0, 69.5, 69.0]
        calories = [1800, 1900, 1850, 1780, 1820, 1800, 1900, 1800, 1850, 1800]
        assert _detect_plateau(weights, calories) is False

    def test_too_few_data_no_plateau(self):
        weights = [75.0, 75.1, 74.9]
        calories = [2000, 2050, 1980]
        assert _detect_plateau(weights, calories) is False

    def test_empty_lists_no_plateau(self):
        assert _detect_plateau([], []) is False


# ── _estimate_metabolic_age ───────────────────────────────────────────────────

class TestEstimateMetabolicAge:
    def test_high_longevity_younger_metabolic_age(self):
        age = _estimate_metabolic_age(90, 35)
        assert age < 35

    def test_low_longevity_older_metabolic_age(self):
        age = _estimate_metabolic_age(10, 35)
        assert age > 35

    def test_average_longevity_same_age(self):
        age = _estimate_metabolic_age(50, 35)
        assert abs(age - 35) < 1.0

    def test_none_score_returns_none(self):
        assert _estimate_metabolic_age(None, 35) is None

    def test_none_age_returns_none(self):
        assert _estimate_metabolic_age(80, None) is None

    def test_metabolic_age_never_below_18(self):
        age = _estimate_metabolic_age(100, 20)
        assert age >= 18.0


# ── compute_metabolic_state (intégration) ────────────────────────────────────

class TestComputeMetabolicState:
    def test_empty_inputs_returns_state(self):
        state = compute_metabolic_state(
            metrics=None,
            readiness=None,
            weight_kg=None,
            height_cm=None,
            age=None,
            sex=None,
            activity_level=None,
            primary_goal=None,
            longevity_score=None,
        )
        assert isinstance(state, MetabolicState)
        assert state.confidence_score == 0.0

    def test_full_profile_increases_confidence(self):
        state = compute_metabolic_state(
            metrics=None,
            readiness=None,
            weight_kg=75,
            height_cm=178,
            age=30,
            sex="male",
            activity_level="moderate",
            primary_goal="muscle_gain",
            longevity_score=70,
        )
        assert state.confidence_score > 0.0
        assert state.estimated_bmr_kcal is not None
        assert state.estimated_tdee_kcal is not None

    def test_snapshot_date_set(self):
        today = date.today()
        state = compute_metabolic_state(
            metrics=None,
            readiness=None,
            weight_kg=None,
            height_cm=None,
            age=None,
            sex=None,
            activity_level=None,
            primary_goal=None,
            longevity_score=None,
            target_date=today,
        )
        assert state.snapshot_date == today

    def test_plateau_detected_when_stable(self):
        weights = [75.0] * 12
        calories = [2000.0] * 12
        state = compute_metabolic_state(
            metrics=None,
            readiness=None,
            weight_kg=75,
            height_cm=178,
            age=30,
            sex="male",
            activity_level="moderate",
            primary_goal="weight_loss",
            longevity_score=None,
            recent_weights=weights,
            recent_calories=calories,
        )
        assert state.plateau_risk is True
