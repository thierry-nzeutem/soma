"""
Tests unitaires — injury_risk_engine.py (LOT 10).

Couvre :
  - _compute_acwr() : calcul ACWR avec division par zéro
  - _score_acwr_risk() : zones de risque ACWR
  - _score_fatigue_risk() : seuils fatigue
  - _score_biomechanics_risk() : qualité mouvement inversée
  - _score_readiness_risk() : readiness faible = risque élevé
  - compute_injury_risk() : flux complet, confidence, risk_level, risk_area

Stratégie :
  - Fonctions pures testées directement (pas de DB)
  - pytest.approx() pour les flottants
"""
import pytest

from app.services.injury_risk_engine import (
    _compute_acwr,
    _score_acwr_risk,
    _score_biomechanics_risk,
    _score_fatigue_risk,
    _score_readiness_risk,
    compute_injury_risk,
)


# ── _compute_acwr ─────────────────────────────────────────────────────────────

class TestComputeAcwr:

    def test_standard_calculation(self):
        """7d=300, 28d=800 → ACWR = 300 / (800/4) = 300/200 = 1.5"""
        result = _compute_acwr(300, 800)
        assert result == pytest.approx(1.5, abs=0.01)

    def test_optimal_zone(self):
        """7d=250, 28d=800 → ACWR = 250/200 = 1.25 (zone optimale)"""
        result = _compute_acwr(250, 800)
        assert result == pytest.approx(1.25, abs=0.01)

    def test_overreaching_zone(self):
        """Charge très élevée → ACWR > 2"""
        result = _compute_acwr(600, 800)
        assert result is not None
        assert result > 2.0

    def test_zero_chronic_load_returns_none(self):
        """Division par zéro si charge chronique nulle → None"""
        result = _compute_acwr(300, 0)
        assert result is None

    def test_undertraining(self):
        """Charge aiguë très faible → ACWR < 0.8"""
        result = _compute_acwr(50, 800)
        assert result is not None
        assert result < 0.8

    def test_equal_loads(self):
        """Charges égales → ACWR = 4 (7d = 28d/4 * 4 → 7d/28d*4 = 1.0)"""
        result = _compute_acwr(200, 800)
        assert result == pytest.approx(1.0, abs=0.01)


# ── _score_acwr_risk ──────────────────────────────────────────────────────────

class TestScoreAcwrRisk:

    def test_optimal_zone_low_risk(self):
        """ACWR = 1.0 → zone sûre → score faible"""
        score = _score_acwr_risk(1.0)
        assert score == pytest.approx(10.0, abs=0.1)

    def test_optimal_zone_upper_edge(self):
        """ACWR = 1.3 (limite haute zone sûre) → score faible"""
        score = _score_acwr_risk(1.3)
        assert score == pytest.approx(10.0, abs=0.1)

    def test_moderate_risk_zone(self):
        """ACWR = 1.4 → risque modéré"""
        score = _score_acwr_risk(1.4)
        assert 10.0 < score < 45.0

    def test_high_risk_zone(self):
        """ACWR = 1.6 → risque élevé"""
        score = _score_acwr_risk(1.6)
        assert 45.0 < score < 80.0

    def test_critical_zone(self):
        """ACWR = 2.1 → risque critique (>80)"""
        score = _score_acwr_risk(2.1)
        assert score > 80.0

    def test_undertraining_low_risk(self):
        """ACWR = 0.5 → undertraining → risque faible (≤20)"""
        score = _score_acwr_risk(0.5)
        assert score <= 20.0

    def test_zero_acwr_no_risk(self):
        """ACWR = 0 → pas de charge → score = 0"""
        score = _score_acwr_risk(0.0)
        assert score == 0.0

    def test_score_increases_with_acwr(self):
        """Le score doit croître avec l'ACWR au-delà de la zone sûre"""
        assert _score_acwr_risk(1.4) < _score_acwr_risk(1.6)
        assert _score_acwr_risk(1.6) < _score_acwr_risk(2.0)
        assert _score_acwr_risk(2.0) < _score_acwr_risk(2.5)

    def test_max_cap_at_100(self):
        """Score ne dépasse pas 100 pour un ACWR extrême"""
        score = _score_acwr_risk(10.0)
        assert score <= 100.0


# ── _score_fatigue_risk ───────────────────────────────────────────────────────

class TestScoreFatigueRisk:

    def test_low_fatigue(self):
        """Fatigue = 20 → risque faible (<12)"""
        score = _score_fatigue_risk(20)
        assert score < 12.0

    def test_moderate_fatigue(self):
        """Fatigue = 55 → risque modéré (12–48)"""
        score = _score_fatigue_risk(55)
        assert 12.0 <= score <= 48.0

    def test_high_fatigue(self):
        """Fatigue = 75 → risque élevé (48–78)"""
        score = _score_fatigue_risk(75)
        assert 48.0 <= score <= 78.0

    def test_critical_fatigue(self):
        """Fatigue = 90 → risque critique (>78)"""
        score = _score_fatigue_risk(90)
        assert score > 78.0

    def test_zero_fatigue(self):
        """Fatigue = 0 → risque nul"""
        score = _score_fatigue_risk(0)
        assert score == 0.0

    def test_fatigue_at_40_threshold(self):
        """Fatigue = 40 → limite basse/modérée"""
        score = _score_fatigue_risk(40)
        assert score == pytest.approx(12.0, abs=0.5)

    def test_score_increases_with_fatigue(self):
        """Score croît avec la fatigue"""
        assert _score_fatigue_risk(30) < _score_fatigue_risk(60)
        assert _score_fatigue_risk(60) < _score_fatigue_risk(80)
        assert _score_fatigue_risk(80) < _score_fatigue_risk(95)

    def test_max_cap_at_100(self):
        """Score ne dépasse pas 100"""
        assert _score_fatigue_risk(100) <= 100.0


# ── _score_biomechanics_risk ──────────────────────────────────────────────────

class TestScoreBiomecanicsRisk:

    def test_high_quality_low_risk(self):
        """Qualité = 85 → bonne biomécanique → risque faible (10)"""
        score = _score_biomechanics_risk(85)
        assert score == pytest.approx(10.0, abs=0.5)

    def test_good_quality_boundary(self):
        """Qualité = 80 → score = 10 (seuil)"""
        score = _score_biomechanics_risk(80)
        assert score == pytest.approx(10.0, abs=0.5)

    def test_moderate_quality(self):
        """Qualité = 65 → risque modéré"""
        score = _score_biomechanics_risk(65)
        assert 10.0 < score < 30.0

    def test_low_quality(self):
        """Qualité = 50 → risque modéré élevé (30–70)"""
        score = _score_biomechanics_risk(50)
        assert 30.0 <= score <= 70.0

    def test_very_low_quality(self):
        """Qualité = 30 → risque élevé (>70)"""
        score = _score_biomechanics_risk(30)
        assert score >= 70.0

    def test_score_decreases_with_quality(self):
        """Le risque diminue quand la qualité augmente"""
        assert _score_biomechanics_risk(30) > _score_biomechanics_risk(60)
        assert _score_biomechanics_risk(60) > _score_biomechanics_risk(85)

    def test_max_cap_at_100(self):
        """Score ne dépasse pas 100 pour qualité nulle"""
        assert _score_biomechanics_risk(0) <= 100.0


# ── _score_readiness_risk ─────────────────────────────────────────────────────

class TestScoreReadinessRisk:

    def test_high_readiness_low_risk(self):
        """Readiness = 80 → bonne récupération → risque faible (10)"""
        score = _score_readiness_risk(80)
        assert score == pytest.approx(10.0, abs=0.5)

    def test_moderate_readiness(self):
        """Readiness = 60 → risque modéré"""
        score = _score_readiness_risk(60)
        assert 10.0 < score <= 40.0

    def test_low_readiness(self):
        """Readiness = 40 → risque élevé"""
        score = _score_readiness_risk(40)
        assert 40.0 <= score <= 80.0

    def test_critical_readiness(self):
        """Readiness = 20 → risque très élevé (>80)"""
        score = _score_readiness_risk(20)
        assert score > 80.0

    def test_score_decreases_with_readiness(self):
        """Le risque diminue quand la readiness augmente"""
        assert _score_readiness_risk(20) > _score_readiness_risk(50)
        assert _score_readiness_risk(50) > _score_readiness_risk(80)

    def test_max_cap_at_100(self):
        """Score ne dépasse pas 100"""
        assert _score_readiness_risk(0) <= 100.0


# ── compute_injury_risk ───────────────────────────────────────────────────────

class TestComputeInjuryRisk:

    def test_no_data_returns_zero_confidence(self):
        """Sans données, confidence = 0.0"""
        result = compute_injury_risk()
        assert result.confidence == 0.0
        assert result.injury_risk_score == 0.0

    def test_no_data_risk_level_low(self):
        """Sans données, niveau = low"""
        result = compute_injury_risk()
        assert result.risk_level == "low"

    def test_no_data_has_recommendation(self):
        """Sans données, recommandation = message d'insuffisance"""
        result = compute_injury_risk()
        assert len(result.recommendations) > 0

    def test_all_data_confidence_near_one(self):
        """Toutes données → confidence ≈ 1.0"""
        result = compute_injury_risk(
            training_load_7d=250, training_load_28d=800,
            fatigue_score=45, avg_vision_quality=75, readiness_score=70,
        )
        assert result.confidence == pytest.approx(1.0, abs=0.01)

    def test_high_acwr_gives_high_risk(self):
        """ACWR élevé seul → risque high ou critical"""
        result = compute_injury_risk(training_load_7d=600, training_load_28d=400)
        assert result.injury_risk_score > 50
        assert result.risk_level in ("high", "critical")

    def test_optimal_conditions_gives_low_risk(self):
        """Conditions optimales → risque faible"""
        result = compute_injury_risk(
            training_load_7d=250, training_load_28d=800,  # ACWR=1.25 optimal
            fatigue_score=20,
            avg_vision_quality=85,
            readiness_score=80,
        )
        assert result.risk_level == "low"
        assert result.injury_risk_score < 25.0

    def test_risk_level_thresholds(self):
        """Vérification des seuils low/moderate/high/critical"""
        # Score faible → low
        r_low = compute_injury_risk(
            training_load_7d=200, training_load_28d=800,
            fatigue_score=15, readiness_score=85,
        )
        assert r_low.risk_level == "low"

    def test_acwr_only_risk_area_training_load(self):
        """Seul ACWR disponible → risk_area = training_load"""
        result = compute_injury_risk(training_load_7d=500, training_load_28d=400)
        assert result.risk_area == "training_load"

    def test_acwr_value_stored(self):
        """ACWR calculé et stocké dans le résultat"""
        result = compute_injury_risk(training_load_7d=300, training_load_28d=800)
        assert result.acwr is not None
        assert result.acwr == pytest.approx(1.5, abs=0.01)

    def test_components_dict_populated(self):
        """Le dict components contient les composantes disponibles"""
        result = compute_injury_risk(
            training_load_7d=300, training_load_28d=800,
            fatigue_score=50,
        )
        assert "acwr" in result.components
        assert "fatigue" in result.components
        assert "biomechanics" not in result.components

    def test_partial_data_confidence_between_0_and_1(self):
        """Données partielles → confidence entre 0 et 1"""
        result = compute_injury_risk(fatigue_score=60)
        assert 0.0 < result.confidence < 1.0

    def test_critical_risk_has_urgent_recommendation(self):
        """Risque critique → recommandation d'urgence"""
        result = compute_injury_risk(
            training_load_7d=900, training_load_28d=400,  # ACWR >> 2
            fatigue_score=90,
            readiness_score=15,
        )
        assert result.risk_level == "critical"
        recs = " ".join(result.recommendations).lower()
        assert any(word in recs for word in ["repos", "risque", "blessure", "urgence", "⚠"])


# ── compute_injury_risk — recommandations ────────────────────────────────────

class TestInjuryRiskRecommendations:

    def test_recommendations_not_empty_with_data(self):
        result = compute_injury_risk(training_load_7d=300, training_load_28d=600)
        assert len(result.recommendations) >= 1

    def test_low_risk_gives_positive_message(self):
        result = compute_injury_risk(
            training_load_7d=200, training_load_28d=800,
            fatigue_score=15, readiness_score=85,
        )
        assert result.risk_level == "low"
        # Message encourageant
        rec_text = " ".join(result.recommendations).lower()
        assert any(w in rec_text for w in ["faible", "continue", "programme", "actuel"])

    def test_high_training_load_triggers_reduce_advice(self):
        result = compute_injury_risk(training_load_7d=600, training_load_28d=500)
        recs = " ".join(result.recommendations).lower()
        assert any(w in recs for w in ["réduis", "charge", "progressi", "10"])
