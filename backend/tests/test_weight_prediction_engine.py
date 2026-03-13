"""
Tests unitaires — weight_prediction_engine.py (LOT 10).

Couvre :
  - _compute_tdee() : préférence TDEE estimé vs fallback active_calories
  - _compute_delta_kg() : modèle linéaire + facteur d'adaptation
  - _trend_direction() : classification perte/gain/stable
  - compute_weight_predictions() : flux complet, confidence, prédictions 7/14/30j

Stratégie :
  - Fonctions pures testées directement (pas de DB)
  - pytest.approx() pour les flottants
"""
import pytest

from app.services.weight_prediction_engine import (
    KCAL_PER_KG,
    _compute_delta_kg,
    _compute_tdee,
    _trend_direction,
    compute_weight_predictions,
)


# ── _compute_tdee ─────────────────────────────────────────────────────────────

class TestComputeTdee:

    def test_prefers_estimated_tdee(self):
        """TDEE estimé disponible → retourne TDEE (plus précis)"""
        result = _compute_tdee(estimated_tdee_kcal=2500, active_calories_kcal=1800)
        assert result == 2500

    def test_fallback_active_calories(self):
        """Pas de TDEE estimé → fallback sur calories actives"""
        result = _compute_tdee(estimated_tdee_kcal=None, active_calories_kcal=1800)
        assert result == 1800

    def test_both_none_returns_none(self):
        """Aucune donnée → None"""
        result = _compute_tdee(estimated_tdee_kcal=None, active_calories_kcal=None)
        assert result is None

    def test_zero_tdee_returns_none(self):
        """TDEE = 0 invalide → fallback ou None"""
        result = _compute_tdee(estimated_tdee_kcal=0, active_calories_kcal=1500)
        assert result == 1500  # fallback

    def test_zero_active_calories_none_tdee(self):
        """TDEE None + active_calories = 0 → None"""
        result = _compute_tdee(estimated_tdee_kcal=None, active_calories_kcal=0)
        assert result is None


# ── _compute_delta_kg ─────────────────────────────────────────────────────────

class TestComputeDeltaKg:

    def test_deficit_gives_negative_delta(self):
        """Déficit de 500 kcal/j → perte de poids"""
        delta = _compute_delta_kg(-500, days=7, adaptation_factor=1.0)
        expected = (-500 * 7 * 1.0) / KCAL_PER_KG
        assert delta == pytest.approx(expected, abs=0.001)

    def test_surplus_gives_positive_delta(self):
        """Surplus de 300 kcal/j → gain de poids"""
        delta = _compute_delta_kg(300, days=7, adaptation_factor=1.0)
        assert delta > 0

    def test_balance_zero_gives_zero_delta(self):
        """Bilan zéro → delta nul"""
        delta = _compute_delta_kg(0, days=7, adaptation_factor=1.0)
        assert delta == pytest.approx(0.0, abs=0.001)

    def test_adaptation_factor_reduces_delta(self):
        """Facteur d'adaptation < 1 réduit le delta"""
        d7 = _compute_delta_kg(-500, 7, 1.0)
        d14 = _compute_delta_kg(-500, 14, 0.90)
        # À 14j, le delta absolu / jours est inférieur par unité de temps
        assert abs(d14 / 14) < abs(d7 / 7)

    def test_7700_kcal_equals_1kg(self):
        """7700 kcal de déficit sur 1j → -1 kg (avec facteur 1.0)"""
        delta = _compute_delta_kg(-7700, days=1, adaptation_factor=1.0)
        assert delta == pytest.approx(-1.0, abs=0.001)

    def test_adaptation_factors(self):
        """Vérification des 3 facteurs d'adaptation"""
        balance = -500
        d7  = _compute_delta_kg(balance, 7,  1.00)
        d14 = _compute_delta_kg(balance, 14, 0.90)
        d30 = _compute_delta_kg(balance, 30, 0.80)
        # d14/14 < d7/7 (par unité de jour)
        assert abs(d14) / 14 < abs(d7) / 7
        # d30/30 < d14/14
        assert abs(d30) / 30 < abs(d14) / 14


# ── _trend_direction ──────────────────────────────────────────────────────────

class TestTrendDirection:

    def test_loss_when_large_negative_delta(self):
        """Delta < −0.3 kg/semaine → loss"""
        assert _trend_direction(-0.5) == "loss"

    def test_gain_when_large_positive_delta(self):
        """Delta > +0.3 kg/semaine → gain"""
        assert _trend_direction(0.5) == "gain"

    def test_stable_when_small_delta(self):
        """Delta dans ±0.3 kg → stable"""
        assert _trend_direction(0.1) == "stable"
        assert _trend_direction(-0.1) == "stable"
        assert _trend_direction(0.0) == "stable"

    def test_boundary_negative(self):
        """Delta = −0.3 exactement → stable (seuil exclusif)"""
        assert _trend_direction(-0.3) == "stable"

    def test_boundary_positive(self):
        """Delta = +0.3 exactement → stable"""
        assert _trend_direction(0.3) == "stable"

    def test_just_below_boundary(self):
        """Delta = −0.31 → loss"""
        assert _trend_direction(-0.31) == "loss"

    def test_just_above_boundary(self):
        """Delta = +0.31 → gain"""
        assert _trend_direction(0.31) == "gain"


# ── compute_weight_predictions ────────────────────────────────────────────────

class TestComputeWeightPredictions:

    def test_no_weight_returns_zero_confidence(self):
        """Sans poids actuel → confidence = 0, pas de prédictions"""
        result = compute_weight_predictions(
            current_weight_kg=None,
            calories_consumed_avg=2500,
            estimated_tdee_kcal=2200,
        )
        assert result.confidence == 0.0
        assert result.expected_weight_7d is None
        assert result.expected_weight_14d is None
        assert result.expected_weight_30d is None

    def test_no_energy_data_returns_zero_confidence(self):
        """Sans données énergétiques → confidence = 0"""
        result = compute_weight_predictions(current_weight_kg=75.0)
        assert result.confidence == 0.0
        assert result.expected_weight_7d is None

    def test_all_data_predictions_computed(self):
        """Toutes données → 3 prédictions calculées"""
        result = compute_weight_predictions(
            current_weight_kg=80.0,
            calories_consumed_avg=2800,
            estimated_tdee_kcal=2500,
        )
        assert result.expected_weight_7d is not None
        assert result.expected_weight_14d is not None
        assert result.expected_weight_30d is not None

    def test_caloric_surplus_gives_gain(self):
        """Surplus calorique → prédiction gain de poids"""
        result = compute_weight_predictions(
            current_weight_kg=70.0,
            calories_consumed_avg=3000,   # +500 kcal
            estimated_tdee_kcal=2500,
        )
        assert result.trend_direction == "gain"
        assert result.expected_weight_7d > 70.0

    def test_caloric_deficit_gives_loss(self):
        """Déficit calorique → prédiction perte de poids"""
        result = compute_weight_predictions(
            current_weight_kg=80.0,
            calories_consumed_avg=2000,   # −500 kcal
            estimated_tdee_kcal=2500,
        )
        assert result.trend_direction == "loss"
        assert result.expected_weight_7d < 80.0

    def test_balanced_intake_gives_stable(self):
        """Apport = dépense → stable"""
        result = compute_weight_predictions(
            current_weight_kg=75.0,
            calories_consumed_avg=2500,
            estimated_tdee_kcal=2500,
        )
        assert result.trend_direction == "stable"
        assert result.weekly_weight_change_kg == pytest.approx(0.0, abs=0.001)

    def test_adaptation_factor_applied(self):
        """Le facteur d'adaptation réduit le delta à 14j et 30j"""
        result = compute_weight_predictions(
            current_weight_kg=80.0,
            calories_consumed_avg=2000,
            estimated_tdee_kcal=2500,  # −500 kcal/j
        )
        # Delta/jour doit être plus petit à 14j et 30j qu'à 7j
        delta_7_per_day = abs(result.expected_weight_7d - result.current_weight_kg) / 7
        delta_14_per_day = abs(result.expected_weight_14d - result.current_weight_kg) / 14
        delta_30_per_day = abs(result.expected_weight_30d - result.current_weight_kg) / 30
        assert delta_14_per_day < delta_7_per_day
        assert delta_30_per_day < delta_14_per_day

    def test_energy_balance_computed(self):
        """Bilan énergétique stocké dans le résultat"""
        result = compute_weight_predictions(
            current_weight_kg=70.0,
            calories_consumed_avg=2800,
            estimated_tdee_kcal=2500,
        )
        assert result.daily_energy_balance_kcal == pytest.approx(300.0, abs=0.1)

    def test_assumptions_not_empty(self):
        """Les hypothèses du modèle sont listées"""
        result = compute_weight_predictions(
            current_weight_kg=75.0,
            calories_consumed_avg=2400,
            estimated_tdee_kcal=2200,
        )
        assert len(result.assumptions) > 0

    def test_current_weight_stored(self):
        """Le poids actuel est conservé dans le résultat"""
        result = compute_weight_predictions(
            current_weight_kg=72.5,
            calories_consumed_avg=2300,
            estimated_tdee_kcal=2100,
        )
        assert result.current_weight_kg == pytest.approx(72.5, abs=0.01)

    def test_confidence_with_all_data(self):
        """Toutes données disponibles → confidence élevée"""
        result = compute_weight_predictions(
            current_weight_kg=75.0,
            calories_consumed_avg=2400,
            estimated_tdee_kcal=2200,
        )
        assert result.confidence >= 0.9

    def test_7d_delta_formula_correctness(self):
        """Vérification manuelle : -500 kcal/j × 7j × 1.0 / 7700 = −0.455 kg"""
        result = compute_weight_predictions(
            current_weight_kg=80.0,
            calories_consumed_avg=2000,
            estimated_tdee_kcal=2500,   # balance = -500
        )
        expected_delta = (-500 * 7 * 1.0) / 7700
        assert result.weekly_weight_change_kg == pytest.approx(expected_delta, abs=0.01)

    def test_fallback_active_calories_used(self):
        """Sans TDEE estimé → utilise active_calories_kcal"""
        result = compute_weight_predictions(
            current_weight_kg=75.0,
            calories_consumed_avg=2000,
            estimated_tdee_kcal=None,
            active_calories_kcal=2200,   # fallback
        )
        # Balance = 2000 - 2200 = -200 kcal/j → perte
        assert result.expected_weight_7d is not None
        assert result.expected_weight_7d < 75.0
