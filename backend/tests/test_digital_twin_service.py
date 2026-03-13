"""
Tests pour Digital Twin V2 Service — LOT 11.
~50 tests purs (aucun accès DB).
"""
import pytest
from datetime import date

from app.domains.twin.service import (
    TwinComponent,
    DigitalTwinState,
    _score_energy_balance,
    _score_glycogen,
    _score_carb_availability,
    _score_protein_status,
    _score_hydration,
    _score_fatigue,
    _score_inflammation,
    _score_sleep_debt,
    _score_recovery_capacity,
    _score_training_readiness,
    _score_stress_load,
    _score_metabolic_flexibility,
    compute_digital_twin_state,
    build_twin_summary,
)


# ── TwinComponent ─────────────────────────────────────────────────────────────

class TestTwinComponent:
    def test_to_dict_contains_all_fields(self):
        comp = TwinComponent(
            value=75.0, status="good", confidence=0.8,
            explanation="test", variables_used=["a", "b"]
        )
        d = comp.to_dict()
        assert d["value"] == 75.0
        assert d["status"] == "good"
        assert d["confidence"] == 0.8
        assert d["explanation"] == "test"
        assert d["variables_used"] == ["a", "b"]


# ── _score_energy_balance ─────────────────────────────────────────────────────

class TestScoreEnergyBalance:
    def test_surplus_gives_positive_value(self):
        comp = _score_energy_balance(calories_consumed=2500, estimated_tdee=2000)
        assert comp.value == pytest.approx(500.0)
        assert comp.confidence > 0

    def test_deficit_gives_negative_value(self):
        comp = _score_energy_balance(calories_consumed=1700, estimated_tdee=2000)
        assert comp.value == pytest.approx(-300.0)

    def test_no_data_returns_zero_confidence(self):
        comp = _score_energy_balance(calories_consumed=None, estimated_tdee=None)
        assert comp.confidence == 0.0

    def test_partial_data_uses_available(self):
        comp = _score_energy_balance(calories_consumed=2000, estimated_tdee=None)
        assert comp.confidence < 1.0

    def test_status_surplus(self):
        comp = _score_energy_balance(calories_consumed=3000, estimated_tdee=2000)
        assert comp.status == "surplus"

    def test_status_deficit(self):
        # -300 kcal → dans la plage "deficit" (-400 à -101)
        comp = _score_energy_balance(calories_consumed=1700, estimated_tdee=2000)
        assert comp.status == "deficit"

    def test_status_balanced(self):
        # +50 kcal → "maintenance" (-100 à +299)
        comp = _score_energy_balance(calories_consumed=2050, estimated_tdee=2000)
        assert comp.status == "maintenance"


# ── _score_glycogen ───────────────────────────────────────────────────────────

class TestScoreGlycogen:
    def test_no_data_returns_zero_confidence(self):
        # Sans poids, la confiance est minimale (≤ 0.2, valeur par défaut)
        comp = _score_glycogen(None, None, None)
        assert comp.confidence < 0.3

    def test_high_carbs_low_load_fills_glycogen(self):
        comp = _score_glycogen(training_load_7d=50, carbs_g_avg=300, weight_kg=75)
        assert comp.value > 200  # significant glycogen stores

    def test_high_load_no_carbs_depletes_glycogen(self):
        # Charge extrême + zéro glucides → déplétion
        comp = _score_glycogen(training_load_7d=5000, carbs_g_avg=0, weight_kg=75)
        assert comp.status in ("depleted", "low")

    def test_glycogen_clamped_to_max(self):
        comp = _score_glycogen(training_load_7d=0, carbs_g_avg=1000, weight_kg=75)
        assert comp.value <= 75 * 15  # max = weight × 15g

    def test_weight_only_sets_max(self):
        comp = _score_glycogen(None, None, weight_kg=80)
        assert comp.confidence > 0


# ── _score_protein_status ─────────────────────────────────────────────────────

class TestScoreProteinStatus:
    def test_adequate_protein_for_weight_loss(self):
        comp = _score_protein_status(protein_g=128, weight_kg=80, goal="weight_loss")
        # target = 1.6 g/kg = 128 g → ratio = 1.0
        assert comp.value >= 1.0

    def test_insufficient_protein(self):
        comp = _score_protein_status(protein_g=50, weight_kg=80, goal="muscle_gain")
        # target = 1.8 g/kg = 144 g → ratio = 50/144 ≈ 0.35 → insufficient
        assert comp.status in ("insufficient", "low")

    def test_no_protein_data(self):
        comp = _score_protein_status(None, None, None)
        assert comp.confidence == 0.0

    def test_excess_protein_caps_at_optimal(self):
        # Le service retourne "adequate" (≥100% de la cible) — pas de statut "optimal"
        comp = _score_protein_status(protein_g=300, weight_kg=70, goal="muscle_gain")
        assert comp.status == "adequate"


# ── _score_hydration ──────────────────────────────────────────────────────────

class TestScoreHydration:
    def test_full_hydration(self):
        # value = hydration_ml brut (2500), statut selon ratio
        comp = _score_hydration(hydration_ml=2500, hydration_target_ml=2500, weight_kg=70)
        assert comp.value >= 2000
        assert comp.status in ("optimal", "good", "adequate")

    def test_dehydrated(self):
        comp = _score_hydration(hydration_ml=500, hydration_target_ml=2500, weight_kg=70)
        assert comp.status == "dehydrated"

    def test_no_data(self):
        comp = _score_hydration(None, None, None)
        assert comp.confidence == 0.0

    def test_estimate_from_weight_only(self):
        comp = _score_hydration(hydration_ml=2000, hydration_target_ml=None, weight_kg=70)
        assert comp.confidence > 0


# ── _score_fatigue ────────────────────────────────────────────────────────────

class TestScoreFatigue:
    def test_high_load_causes_high_fatigue(self):
        # load=1000 + sleep_score=10 → fatigue normalisée > 60
        comp = _score_fatigue(training_load_7d=1000, sleep_score_avg=10, hrv_ms=None, resting_hr_bpm=None)
        assert comp.value > 60

    def test_no_data_low_fatigue(self):
        comp = _score_fatigue(None, None, None, None)
        assert comp.confidence == 0.0

    def test_good_hrv_reduces_fatigue(self):
        comp_bad_hrv = _score_fatigue(None, None, hrv_ms=20, resting_hr_bpm=None)
        comp_good_hrv = _score_fatigue(None, None, hrv_ms=80, resting_hr_bpm=None)
        assert comp_good_hrv.value < comp_bad_hrv.value

    def test_fatigue_clamped_0_100(self):
        comp = _score_fatigue(1000, 10, 10, 90)
        assert 0 <= comp.value <= 100

    def test_status_labels(self):
        comp = _score_fatigue(training_load_7d=500, sleep_score_avg=20, hrv_ms=15, resting_hr_bpm=85)
        assert comp.status in ("very_tired", "tired", "moderate", "good", "fresh")


# ── _score_inflammation ───────────────────────────────────────────────────────

class TestScoreInflammation:
    def test_high_fatigue_poor_sleep_high_acwr(self):
        # score ≈ 66.5 avec ces valeurs (formule pondérée)
        comp = _score_inflammation(fatigue_value=85, sleep_score=30, acwr=1.8)
        assert comp.value > 60
        assert comp.status in ("very_high", "high", "elevated")

    def test_low_fatigue_good_sleep_no_acwr(self):
        comp = _score_inflammation(fatigue_value=20, sleep_score=85, acwr=None)
        assert comp.value < 30

    def test_acwr_excess_component(self):
        # ACWR exactly 1.5 → excess = 0 → no ACWR contribution
        comp_below = _score_inflammation(30, 70, acwr=1.3)
        comp_above = _score_inflammation(30, 70, acwr=1.8)
        assert comp_above.value > comp_below.value

    def test_clamped_0_100(self):
        comp = _score_inflammation(fatigue_value=0, sleep_score=100, acwr=0.5)
        assert 0 <= comp.value <= 100


# ── _score_sleep_debt ─────────────────────────────────────────────────────────

class TestScoreSleepDebt:
    def test_full_sleep_no_debt(self):
        comp = _score_sleep_debt(sleep_minutes_7d=[480, 480, 480, 480, 480, 480, 480])
        assert comp.value == pytest.approx(0.0)

    def test_severe_sleep_deprivation(self):
        # 4h/night for 7 nights = 240 min, deficit = 480-240 = 240/night avg
        comp = _score_sleep_debt(sleep_minutes_7d=[240, 240, 240, 240, 240, 240, 240])
        assert comp.value == pytest.approx(240.0)
        assert comp.status in ("severe", "high")

    def test_no_sleep_data(self):
        comp = _score_sleep_debt(None)
        assert comp.confidence == 0.0

    def test_nightly_average_debt(self):
        # 5 nights OK, 2 nights short (360 min = 2h deficit each)
        comp = _score_sleep_debt([480, 480, 480, 480, 480, 360, 360])
        # Total deficit = 2 × 120 = 240 min; avg per night = 240/7 ≈ 34
        assert comp.value > 0
        assert comp.value < 60


# ── _score_recovery_capacity ──────────────────────────────────────────────────

class TestScoreRecoveryCapacity:
    def test_high_readiness_low_fatigue_no_debt(self):
        comp = _score_recovery_capacity(readiness_score=90, sleep_debt_value=0, fatigue_value=10)
        assert comp.value > 75

    def test_low_readiness_high_fatigue(self):
        comp = _score_recovery_capacity(readiness_score=30, sleep_debt_value=200, fatigue_value=85)
        assert comp.value < 40

    def test_no_data(self):
        # Sans readiness, sleep_debt=0, fatigue=0 → confiance partielle
        comp = _score_recovery_capacity(readiness_score=None, sleep_debt_value=0, fatigue_value=0)
        assert comp.confidence > 0
        assert comp.value > 0

    def test_partial_data(self):
        comp = _score_recovery_capacity(readiness_score=70, sleep_debt_value=30, fatigue_value=40)
        assert comp.confidence > 0
        assert comp.confidence <= 1.0


# ── _score_training_readiness ─────────────────────────────────────────────────

class TestScoreTrainingReadiness:
    def test_high_recovery_low_fatigue_gives_high_readiness(self):
        comp = _score_training_readiness(recovery_capacity=90, fatigue_value=10, readiness_score=85)
        assert comp.value > 75

    def test_low_recovery_high_fatigue_gives_low_readiness(self):
        comp = _score_training_readiness(recovery_capacity=20, fatigue_value=85, readiness_score=25)
        assert comp.value < 35

    def test_clamped_0_100(self):
        comp = _score_training_readiness(100, 0, 100)
        assert 0 <= comp.value <= 100


# ── _score_stress_load ────────────────────────────────────────────────────────

class TestScoreStressLoad:
    def test_high_fatigue_sleep_deficit_big_energy_deficit(self):
        comp = _score_stress_load(fatigue_value=80, sleep_debt_value=240, energy_balance_kcal=-800)
        assert comp.value > 60

    def test_low_stress(self):
        comp = _score_stress_load(fatigue_value=20, sleep_debt_value=0, energy_balance_kcal=0)
        assert comp.value < 30

    def test_no_data(self):
        # Inputs à 0 → stress minimal
        comp = _score_stress_load(fatigue_value=0, sleep_debt_value=0, energy_balance_kcal=0)
        assert comp.value == 0.0


# ── _score_metabolic_flexibility ─────────────────────────────────────────────

class TestScoreMetabolicFlexibility:
    def test_if_protocol_increases_flexibility(self):
        # consistency_days < total_days pour rester sous le plafond 100
        comp_no_if = _score_metabolic_flexibility(has_if_protocol=False, plateau_risk=False, consistency_days=3)
        comp_if = _score_metabolic_flexibility(has_if_protocol=True, plateau_risk=False, consistency_days=3)
        assert comp_if.value > comp_no_if.value

    def test_plateau_risk_decreases_flexibility(self):
        comp_no_plateau = _score_metabolic_flexibility(False, plateau_risk=False, consistency_days=15)
        comp_plateau = _score_metabolic_flexibility(False, plateau_risk=True, consistency_days=15)
        assert comp_plateau.value < comp_no_plateau.value

    def test_clamped_0_100(self):
        comp = _score_metabolic_flexibility(True, False, 30)
        assert 0 <= comp.value <= 100


# ── compute_digital_twin_state ────────────────────────────────────────────────

class TestComputeDigitalTwinState:
    def test_no_data_returns_moderate_status(self):
        # Sans données, la confiance est faible et le statut est "fresh" (défaut optimiste)
        state = compute_digital_twin_state(target_date=date.today())
        assert state.overall_status in ("fresh", "good", "moderate")
        assert state.global_confidence < 0.5

    def test_with_full_data_returns_high_confidence(self):
        state = compute_digital_twin_state(
            calories_consumed=2200, estimated_tdee=2000,
            training_load_7d=100, acwr=1.1,
            sleep_score_avg=80, sleep_minutes_7d=[480]*7,
            hrv_ms=60, resting_hr_bpm=55,
            readiness_score=80,
            weight_kg=75, goal="maintenance",
            has_if_protocol=False, plateau_risk=False,
            target_date=date.today(),
        )
        assert state.global_confidence > 0.5
        assert state.overall_status in ("fresh", "good", "moderate", "tired", "critical")

    def test_high_fatigue_results_in_tired_status(self):
        state = compute_digital_twin_state(
            training_load_7d=600, sleep_score_avg=30,
            hrv_ms=20, resting_hr_bpm=80,
            readiness_score=25,
            target_date=date.today(),
        )
        assert state.overall_status in ("tired", "critical")

    def test_recommendations_not_empty(self):
        state = compute_digital_twin_state(target_date=date.today())
        assert len(state.recommendations) > 0

    def test_all_components_present(self):
        state = compute_digital_twin_state(target_date=date.today())
        assert hasattr(state, "energy_balance")
        assert hasattr(state, "glycogen")
        assert hasattr(state, "fatigue")
        assert hasattr(state, "inflammation")
        assert hasattr(state, "sleep_debt")
        assert hasattr(state, "recovery_capacity")
        assert hasattr(state, "training_readiness")
        assert hasattr(state, "stress_load")
        assert hasattr(state, "metabolic_flexibility")

    def test_under_recovery_risk_detected(self):
        # Condition : recovery < 40 AND fatigue > 65 AND sleep_debt > 30
        state = compute_digital_twin_state(
            training_load_7d=900,
            sleep_score_avg=20,
            readiness_score=15,
            sleep_minutes_7d=[240, 240, 240, 240, 240, 240, 240],  # 4h/nuit → dette élevée
            target_date=date.today(),
        )
        assert state.under_recovery_risk is True

    def test_plateau_risk_passed_through(self):
        state = compute_digital_twin_state(
            plateau_risk=True,
            target_date=date.today(),
        )
        assert state.plateau_risk is True


# ── build_twin_summary ────────────────────────────────────────────────────────

class TestBuildTwinSummary:
    def test_summary_contains_status(self):
        state = compute_digital_twin_state(target_date=date.today())
        summary = build_twin_summary(state)
        # Le résumé contient le statut en majuscules (ex: "Jumeau FRESH | ...")
        assert state.overall_status.upper() in summary

    def test_summary_is_string(self):
        state = compute_digital_twin_state(target_date=date.today())
        assert isinstance(build_twin_summary(state), str)

    def test_summary_is_compact(self):
        state = compute_digital_twin_state(target_date=date.today())
        assert len(build_twin_summary(state)) < 300
