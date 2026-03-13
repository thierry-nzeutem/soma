"""
Tests SOMA LOT 15 — Injury Prevention Engine.
~35 tests purs.
"""
import pytest
from datetime import date

from app.domains.injury.service import (
    compute_injury_prevention_analysis,
    _score_acwr_risk,
    _score_fatigue_risk,
    _score_asymmetry_risk,
    _score_sleep_risk,
    _score_monotony_risk,
    _determine_risk_category,
    _identify_risk_zones,
    CRITICAL_ACWR,
    HIGH_ACWR,
    MODERATE_ACWR,
)


# ── Tests: _score_acwr_risk ────────────────────────────────────────────────────

class TestScoreAcwrRisk:
    def test_optimal_acwr_low_risk(self):
        score = _score_acwr_risk(1.0)
        assert score < 20.0

    def test_moderate_acwr_moderate_risk(self):
        score = _score_acwr_risk(MODERATE_ACWR + 0.1)  # slightly above 1.3
        assert 10 < score < 50

    def test_high_acwr_high_risk(self):
        score = _score_acwr_risk(HIGH_ACWR + 0.1)  # 1.6
        assert score > 50

    def test_critical_acwr_very_high_risk(self):
        score = _score_acwr_risk(CRITICAL_ACWR + 0.1)  # 1.9
        assert score > 85

    def test_none_acwr_returns_small_default(self):
        score = _score_acwr_risk(None)
        assert 10 <= score <= 30

    def test_below_optimal_acwr_slight_risk(self):
        score = _score_acwr_risk(0.5)  # detraining
        assert score > 0

    def test_score_range_0_100(self):
        for acwr in [0.3, 0.8, 1.0, 1.3, 1.5, 1.8, 2.0, 2.5]:
            score = _score_acwr_risk(acwr)
            assert 0 <= score <= 100, f"Score out of range for ACWR={acwr}: {score}"


# ── Tests: _score_fatigue_risk ─────────────────────────────────────────────────

class TestScoreFatigueRisk:
    def test_low_fatigue_zero_risk(self):
        score = _score_fatigue_risk(20.0)
        assert score == 0.0

    def test_moderate_fatigue_moderate_risk(self):
        score = _score_fatigue_risk(60.0)
        assert 15 < score < 60

    def test_high_fatigue_high_risk(self):
        score = _score_fatigue_risk(80.0)
        assert score > 50

    def test_critical_fatigue_near_max(self):
        score = _score_fatigue_risk(95.0)
        assert score > 85

    def test_none_returns_small_default(self):
        score = _score_fatigue_risk(None)
        assert score > 0

    def test_score_range_0_100(self):
        for fatigue in [0, 25, 50, 70, 85, 100]:
            score = _score_fatigue_risk(float(fatigue))
            assert 0 <= score <= 100


# ── Tests: _score_asymmetry_risk ──────────────────────────────────────────────

class TestScoreAsymmetryRisk:
    def test_symmetric_zero_risk(self):
        score = _score_asymmetry_risk(5.0)
        assert score == 0.0

    def test_moderate_asymmetry_moderate_risk(self):
        score = _score_asymmetry_risk(30.0)
        assert 20 < score < 65

    def test_high_asymmetry_high_risk(self):
        score = _score_asymmetry_risk(50.0)
        assert score > 60

    def test_critical_asymmetry_near_max(self):
        score = _score_asymmetry_risk(70.0)
        assert score > 90

    def test_none_returns_small_default(self):
        score = _score_asymmetry_risk(None)
        assert score > 0

    def test_score_range_0_100(self):
        for asym in [0, 15, 30, 50, 70, 100]:
            score = _score_asymmetry_risk(float(asym))
            assert 0 <= score <= 100


# ── Tests: _score_sleep_risk ───────────────────────────────────────────────────

class TestScoreSleepRisk:
    def test_8h_no_risk(self):
        assert _score_sleep_risk(480) == 0.0

    def test_7h_low_risk(self):
        assert _score_sleep_risk(420) == 10.0

    def test_6h_moderate_risk(self):
        assert _score_sleep_risk(360) == 25.0

    def test_5h_high_risk(self):
        score = _score_sleep_risk(300)
        assert score > 50

    def test_4h_very_high_risk(self):
        score = _score_sleep_risk(240)
        assert score >= 80

    def test_none_returns_small_default(self):
        score = _score_sleep_risk(None)
        assert score > 0

    def test_score_range_0_100(self):
        for sleep in [120, 240, 360, 420, 480, 540]:
            score = _score_sleep_risk(float(sleep))
            assert 0 <= score <= 100


# ── Tests: _score_monotony_risk ────────────────────────────────────────────────

class TestScoreMonotonyRisk:
    def test_varied_loads_low_monotony(self):
        loads = [50.0, 80.0, 30.0, 90.0, 20.0, 70.0, 40.0]
        score = _score_monotony_risk(loads)
        assert score < 30

    def test_constant_loads_high_monotony(self):
        loads = [60.0] * 7  # same every day
        score = _score_monotony_risk(loads)
        assert score > 50

    def test_insufficient_data_returns_zero(self):
        loads = [60.0, 70.0]
        score = _score_monotony_risk(loads)
        assert score == 0.0

    def test_empty_returns_zero(self):
        assert _score_monotony_risk([]) == 0.0


# ── Tests: _determine_risk_category ───────────────────────────────────────────

class TestDetermineRiskCategory:
    def test_below_15_is_minimal(self):
        assert _determine_risk_category(10) == "minimal"

    def test_between_15_30_is_low(self):
        assert _determine_risk_category(20) == "low"

    def test_between_30_55_is_moderate(self):
        assert _determine_risk_category(45) == "moderate"

    def test_between_55_75_is_high(self):
        assert _determine_risk_category(65) == "high"

    def test_above_75_is_critical(self):
        assert _determine_risk_category(80) == "critical"

    def test_edge_values(self):
        assert _determine_risk_category(0) == "minimal"
        assert _determine_risk_category(100) == "critical"


# ── Tests: compute_injury_prevention_analysis ──────────────────────────────────

class TestComputeInjuryPreventionAnalysis:
    def test_no_data_graceful_degradation(self):
        result = compute_injury_prevention_analysis()
        assert 0 <= result.injury_risk_score <= 100
        assert result.injury_risk_category in ("minimal", "low", "moderate", "high", "critical")
        assert result.confidence == 0.0  # no data

    def test_high_risk_scenario(self):
        result = compute_injury_prevention_analysis(
            acwr=1.9,
            fatigue_score=85.0,
            asymmetry_score=55.0,
            sleep_minutes_avg=240.0,  # 4h sleep
        )
        assert result.injury_risk_score > 60
        assert result.injury_risk_category in ("high", "critical")
        assert result.training_overload_risk is True
        assert result.fatigue_compensation_risk is True

    def test_low_risk_scenario(self):
        result = compute_injury_prevention_analysis(
            acwr=1.1,
            fatigue_score=25.0,
            asymmetry_score=10.0,
            sleep_minutes_avg=480.0,
        )
        assert result.injury_risk_score < 25
        assert result.injury_risk_category in ("minimal", "low")
        assert result.training_overload_risk is False

    def test_critical_acwr_triggers_overload_flag(self):
        result = compute_injury_prevention_analysis(acwr=CRITICAL_ACWR)
        assert result.training_overload_risk is True

    def test_high_fatigue_triggers_compensation_flag(self):
        result = compute_injury_prevention_analysis(fatigue_score=85.0)
        assert result.fatigue_compensation_risk is True

    def test_confidence_increases_with_more_data(self):
        result_sparse = compute_injury_prevention_analysis(acwr=1.2)
        result_full = compute_injury_prevention_analysis(
            acwr=1.2,
            fatigue_score=50.0,
            asymmetry_score=20.0,
            sleep_minutes_avg=420.0,
            training_loads_7d=[60.0] * 5,
            exercise_profiles={"squat": {"quality_trend": "stable", "avg_stability": 80.0}},
        )
        assert result_full.confidence > result_sparse.confidence

    def test_recommendations_not_empty_for_high_risk(self):
        result = compute_injury_prevention_analysis(
            acwr=1.8,
            fatigue_score=82.0,
        )
        assert len(result.recommendations) > 0 or len(result.immediate_actions) > 0

    def test_result_fields_all_present(self):
        result = compute_injury_prevention_analysis()
        assert hasattr(result, "injury_risk_score")
        assert hasattr(result, "injury_risk_category")
        assert hasattr(result, "acwr_risk_score")
        assert hasattr(result, "fatigue_risk_score")
        assert hasattr(result, "asymmetry_risk_score")
        assert hasattr(result, "sleep_risk_score")
        assert hasattr(result, "monotony_risk_score")
        assert hasattr(result, "risk_zones")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "immediate_actions")

    def test_monotony_risk_with_constant_loads(self):
        result = compute_injury_prevention_analysis(
            training_loads_7d=[60.0] * 7  # same load every day
        )
        assert result.monotony_risk_score > 0

    def test_analysis_date_is_today(self):
        from datetime import date
        result = compute_injury_prevention_analysis()
        assert result.analysis_date == date.today()
