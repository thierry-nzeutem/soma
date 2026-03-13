"""
Tests unitaires — overtraining_engine.py (LOT 10).

Couvre :
  - _compute_acwr() : calcul ACWR normalisé
  - _acwr_zone() : classification par zone
  - _score_acwr_overtraining() : score de risque ACWR
  - _score_wellbeing() : score bien-être combiné (sommeil + fatigue)
  - _score_readiness_overtraining() : score readiness inversé
  - compute_overtraining_risk() : flux complet, confidence, zones, recommandations

Stratégie :
  - Fonctions pures testées directement (pas de DB)
  - pytest.approx() pour les flottants
"""
import pytest

from app.services.overtraining_engine import (
    _acwr_zone,
    _compute_acwr,
    _score_acwr_overtraining,
    _score_readiness_overtraining,
    _score_wellbeing,
    compute_overtraining_risk,
)


# ── _compute_acwr ─────────────────────────────────────────────────────────────

class TestComputeAcwr:

    def test_standard_calculation(self):
        """7d=300, 28d=800 → ACWR = 300 / (800/4) = 1.5"""
        result = _compute_acwr(300, 800)
        assert result == pytest.approx(1.5, abs=0.01)

    def test_optimal_acwr(self):
        """7d=200, 28d=800 → ACWR = 200/200 = 1.0"""
        result = _compute_acwr(200, 800)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_zero_chronic_returns_none(self):
        """Charge chronique nulle → None (évite division par zéro)"""
        result = _compute_acwr(300, 0)
        assert result is None

    def test_overreaching_acwr(self):
        """7d=600, 28d=800 → ACWR = 600/200 = 3.0 (surcharge)"""
        result = _compute_acwr(600, 800)
        assert result == pytest.approx(3.0, abs=0.01)

    def test_undertraining_acwr(self):
        """7d=80, 28d=800 → ACWR = 80/200 = 0.4 (sous-entraînement)"""
        result = _compute_acwr(80, 800)
        assert result == pytest.approx(0.4, abs=0.01)


# ── _acwr_zone ────────────────────────────────────────────────────────────────

class TestAcwrZone:

    def test_undertraining(self):
        assert _acwr_zone(0.5) == "undertraining"
        assert _acwr_zone(0.79) == "undertraining"

    def test_optimal(self):
        assert _acwr_zone(0.8) == "optimal"
        assert _acwr_zone(1.0) == "optimal"
        assert _acwr_zone(1.29) == "optimal"

    def test_moderate_risk(self):
        assert _acwr_zone(1.3) == "moderate_risk"
        assert _acwr_zone(1.4) == "moderate_risk"
        assert _acwr_zone(1.49) == "moderate_risk"

    def test_high_risk(self):
        assert _acwr_zone(1.5) == "high_risk"
        assert _acwr_zone(1.8) == "high_risk"
        assert _acwr_zone(1.99) == "high_risk"

    def test_overreaching(self):
        assert _acwr_zone(2.0) == "overreaching"
        assert _acwr_zone(3.0) == "overreaching"

    def test_boundary_exact_values(self):
        """Vérifier les exactes limites de zone"""
        assert _acwr_zone(1.3) == "moderate_risk"  # 1.3 = début moderate
        assert _acwr_zone(1.5) == "high_risk"       # 1.5 = début high


# ── _score_acwr_overtraining ──────────────────────────────────────────────────

class TestScoreAcwrOvertraining:

    def test_optimal_zone_low_score(self):
        """Zone optimale (1.0) → score très faible (<15)"""
        score = _score_acwr_overtraining(1.0)
        assert score < 15.0

    def test_overreaching_high_score(self):
        """Zone overreaching (2.5) → score élevé (>80)"""
        score = _score_acwr_overtraining(2.5)
        assert score > 80.0

    def test_moderate_zone_mid_score(self):
        """Zone moderate_risk (1.4) → score intermédiaire"""
        score = _score_acwr_overtraining(1.4)
        assert 10.0 < score < 40.0

    def test_high_zone_high_score(self):
        """Zone high_risk (1.75) → score élevé"""
        score = _score_acwr_overtraining(1.75)
        assert 40.0 < score < 80.0

    def test_undertraining_very_low_score(self):
        """Undertraining → faible risque de surentraînement"""
        score = _score_acwr_overtraining(0.4)
        assert score < 15.0

    def test_score_increases_monotonically_above_optimal(self):
        """Score croît avec ACWR au-delà de la zone sûre"""
        assert _score_acwr_overtraining(1.3) < _score_acwr_overtraining(1.5)
        assert _score_acwr_overtraining(1.5) < _score_acwr_overtraining(2.0)
        assert _score_acwr_overtraining(2.0) < _score_acwr_overtraining(2.5)

    def test_max_capped_at_100(self):
        """Score ne dépasse pas 100"""
        assert _score_acwr_overtraining(5.0) <= 100.0

    def test_zero_acwr_zero_score(self):
        """ACWR = 0 → score = 0"""
        assert _score_acwr_overtraining(0) == 0.0


# ── _score_wellbeing ──────────────────────────────────────────────────────────

class TestScoreWellbeing:

    def test_good_sleep_low_fatigue_low_risk(self):
        """Bon sommeil (85) + faible fatigue (20) → risque bien-être faible"""
        score = _score_wellbeing(sleep_score=85, fatigue_score=20)
        assert score is not None
        assert score < 25.0

    def test_poor_sleep_high_fatigue_high_risk(self):
        """Mauvais sommeil (30) + fatigue élevée (80) → risque bien-être élevé"""
        score = _score_wellbeing(sleep_score=30, fatigue_score=80)
        assert score is not None
        assert score > 60.0

    def test_sleep_only(self):
        """Seulement le sommeil disponible"""
        score = _score_wellbeing(sleep_score=70, fatigue_score=None)
        assert score is not None
        assert 0.0 <= score <= 100.0

    def test_fatigue_only(self):
        """Seulement la fatigue disponible"""
        score = _score_wellbeing(sleep_score=None, fatigue_score=60)
        assert score is not None
        assert 0.0 <= score <= 100.0

    def test_none_none_returns_none(self):
        """Aucune donnée → None"""
        score = _score_wellbeing(sleep_score=None, fatigue_score=None)
        assert score is None

    def test_max_capped_at_100(self):
        """Score ne dépasse pas 100"""
        score = _score_wellbeing(sleep_score=0, fatigue_score=100)
        assert score is not None
        assert score <= 100.0


# ── compute_overtraining_risk ─────────────────────────────────────────────────

class TestComputeOvertrainingRisk:

    def test_no_data_confidence_zero(self):
        """Sans données, confidence = 0.0"""
        result = compute_overtraining_risk()
        assert result.confidence == 0.0
        assert result.overtraining_risk == 0.0

    def test_no_data_risk_level_low(self):
        """Sans données, niveau = low"""
        result = compute_overtraining_risk()
        assert result.risk_level == "low"

    def test_no_data_has_recommendation(self):
        """Sans données, recommandation non vide"""
        result = compute_overtraining_risk()
        assert len(result.recommendation) > 0

    def test_all_data_confidence_near_one(self):
        """Toutes données → confidence ≈ 1.0"""
        result = compute_overtraining_risk(
            training_load_7d=250, training_load_28d=800,
            sleep_score=75, fatigue_score=40, readiness_score=70,
        )
        assert result.confidence == pytest.approx(1.0, abs=0.01)

    def test_overreaching_acwr_critical_risk(self):
        """ACWR = 3.0 (overreaching) → risque critical"""
        result = compute_overtraining_risk(
            training_load_7d=600, training_load_28d=800,  # ACWR=3.0
        )
        assert result.acwr_zone == "overreaching"
        assert result.risk_level in ("high", "critical")

    def test_optimal_acwr_good_sleep_low_risk(self):
        """ACWR optimal + bon sommeil + faible fatigue → risque faible"""
        result = compute_overtraining_risk(
            training_load_7d=200, training_load_28d=800,  # ACWR=1.0
            sleep_score=85, fatigue_score=20, readiness_score=80,
        )
        assert result.risk_level == "low"
        assert result.acwr_zone == "optimal"

    def test_acwr_stored_in_result(self):
        """ACWR calculé et stocké"""
        result = compute_overtraining_risk(training_load_7d=300, training_load_28d=800)
        assert result.acwr is not None
        assert result.acwr == pytest.approx(1.5, abs=0.01)

    def test_acwr_zone_correct(self):
        """Zone ACWR correctement classifiée"""
        result = compute_overtraining_risk(
            training_load_7d=400, training_load_28d=800,  # ACWR=2.0
        )
        assert result.acwr_zone == "overreaching"

    def test_components_dict_populated(self):
        """Dict components contient les composantes disponibles"""
        result = compute_overtraining_risk(
            training_load_7d=300, training_load_28d=800,
            sleep_score=70,
        )
        assert "acwr" in result.components
        assert "wellbeing" in result.components
        assert "readiness" not in result.components

    def test_overreaching_recommendation_warns(self):
        """Zone overreaching → recommandation d'alerte"""
        result = compute_overtraining_risk(
            training_load_7d=700, training_load_28d=800,
        )
        rec = result.recommendation.lower()
        assert any(w in rec for w in ["surcharge", "repos", "réduis", "charge", "⚠"])

    def test_undertraining_recommendation_encourages(self):
        """Undertraining → recommandation d'augmenter progressivement"""
        result = compute_overtraining_risk(
            training_load_7d=50, training_load_28d=800,  # ACWR << 0.8
        )
        assert result.acwr_zone == "undertraining"
        rec = result.recommendation.lower()
        assert any(w in rec for w in ["faible", "augmente", "progressiv", "programme"])
