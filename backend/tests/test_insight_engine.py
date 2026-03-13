"""
Tests unitaires — Insight Engine (LOT 3).

Couvre :
  - detect_low_protein (5 tests)
  - detect_excessive_calorie_deficit (5 tests)
  - detect_low_activity (4 tests)
  - detect_accumulated_fatigue (4 tests)
  - detect_sleep_debt (4 tests)
  - detect_dehydration_pattern (4 tests)
  - detect_overtraining_risk (5 tests)
  - run_insight_engine — intégration (6 tests)
"""
import pytest
from app.services.insight_engine import (
    detect_low_protein,
    detect_excessive_calorie_deficit,
    detect_low_activity,
    detect_accumulated_fatigue,
    detect_sleep_debt,
    detect_dehydration_pattern,
    detect_overtraining_risk,
    run_insight_engine,
    MIN_SLEEP_HOURS,
    STEPS_DAILY_GOAL,
    PROTEIN_RATIO_MIN,
    READINESS_LOW,
)


# ── Mock DailyMetrics ─────────────────────────────────────────────────────────

class _MockMetrics:
    """Proxy minimal pour simuler un objet DailyMetrics."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _mock_7d(**daily_values):
    """Crée 7 jours de métriques avec les mêmes valeurs."""
    return [_MockMetrics(**daily_values) for _ in range(7)]


# ── detect_low_protein ────────────────────────────────────────────────────────

class TestDetectLowProtein:

    def test_no_target_returns_none(self):
        metrics = _mock_7d(protein_g=60, protein_target_g=None)
        assert detect_low_protein(metrics) is None

    def test_insufficient_on_3_days_triggers(self):
        metrics = [
            _MockMetrics(protein_g=40, protein_target_g=150),  # 27% < 60%
            _MockMetrics(protein_g=50, protein_target_g=150),  # 33% < 60%
            _MockMetrics(protein_g=60, protein_target_g=150),  # 40% < 60%
            _MockMetrics(protein_g=160, protein_target_g=150), # 107% ok
            _MockMetrics(protein_g=170, protein_target_g=150), # ok
            _MockMetrics(protein_g=None, protein_target_g=150),
            _MockMetrics(protein_g=None, protein_target_g=150),
        ]
        result = detect_low_protein(metrics)
        assert result is not None
        assert result.category == "nutrition"
        assert result.severity == "warning"

    def test_sufficient_protein_returns_none(self):
        metrics = _mock_7d(protein_g=150, protein_target_g=150)
        assert detect_low_protein(metrics) is None

    def test_only_2_bad_days_returns_none(self):
        metrics = [
            _MockMetrics(protein_g=40, protein_target_g=150),  # bas
            _MockMetrics(protein_g=50, protein_target_g=150),  # bas
            _MockMetrics(protein_g=160, protein_target_g=150), # ok
            _MockMetrics(protein_g=160, protein_target_g=150), # ok
            _MockMetrics(protein_g=160, protein_target_g=150), # ok
            _MockMetrics(protein_g=None, protein_target_g=None),
            _MockMetrics(protein_g=None, protein_target_g=None),
        ]
        assert detect_low_protein(metrics) is None

    def test_evidence_contains_days_count(self):
        metrics = _mock_7d(protein_g=40, protein_target_g=150)  # tous bas
        result = detect_low_protein(metrics)
        assert result is not None
        assert "days_below_threshold" in result.data_evidence


# ── detect_excessive_calorie_deficit ──────────────────────────────────────────

class TestDetectExcessiveCalorieDeficit:

    def test_no_data_returns_none(self):
        metrics = _mock_7d(calories_consumed=None, calories_target=2000)
        assert detect_excessive_calorie_deficit(metrics) is None

    def test_severe_deficit_triggers_critical(self):
        metrics = _mock_7d(calories_consumed=800, calories_target=2000)  # 40% < 60%
        result = detect_excessive_calorie_deficit(metrics)
        assert result is not None
        assert result.severity == "critical"

    def test_mild_deficit_returns_none(self):
        metrics = _mock_7d(calories_consumed=1700, calories_target=2000)  # 85% ok
        assert detect_excessive_calorie_deficit(metrics) is None

    def test_1_day_insufficient_data(self):
        metrics = [
            _MockMetrics(calories_consumed=800, calories_target=2000),
            _MockMetrics(calories_consumed=None, calories_target=2000),
            _MockMetrics(calories_consumed=None, calories_target=2000),
            _MockMetrics(calories_consumed=None, calories_target=2000),
            _MockMetrics(calories_consumed=None, calories_target=2000),
            _MockMetrics(calories_consumed=None, calories_target=2000),
            _MockMetrics(calories_consumed=None, calories_target=2000),
        ]
        # Seul 1 jour de données → pas assez
        assert detect_excessive_calorie_deficit(metrics) is None

    def test_no_target_returns_none(self):
        metrics = _mock_7d(calories_consumed=1200, calories_target=None)
        result = detect_excessive_calorie_deficit(metrics)
        assert result is None  # Pas de cible = pas de seuil de comparaison


# ── detect_low_activity ───────────────────────────────────────────────────────

class TestDetectLowActivity:

    def test_very_low_steps_triggers(self):
        # < 4000 pas (50% de 8000) pendant 5+ jours
        metrics = _mock_7d(steps=2000)
        result = detect_low_activity(metrics)
        assert result is not None
        assert result.category == "activity"

    def test_active_user_returns_none(self):
        metrics = _mock_7d(steps=10000)
        assert detect_low_activity(metrics) is None

    def test_only_4_bad_days_returns_none(self):
        metrics = [
            _MockMetrics(steps=1000),  # bas
            _MockMetrics(steps=1000),  # bas
            _MockMetrics(steps=1000),  # bas
            _MockMetrics(steps=1000),  # bas
            _MockMetrics(steps=10000), # ok
            _MockMetrics(steps=10000), # ok
            _MockMetrics(steps=10000), # ok
        ]
        assert detect_low_activity(metrics) is None

    def test_no_steps_data_returns_none(self):
        metrics = _mock_7d(steps=None)
        assert detect_low_activity(metrics) is None


# ── detect_accumulated_fatigue ────────────────────────────────────────────────

class TestDetectAccumulatedFatigue:

    def test_low_readiness_triggers_critical(self):
        metrics = _mock_7d(readiness_score=35.0)
        result = detect_accumulated_fatigue(metrics)
        assert result is not None
        assert result.severity == "critical"

    def test_good_readiness_returns_none(self):
        metrics = _mock_7d(readiness_score=75.0)
        assert detect_accumulated_fatigue(metrics) is None

    def test_only_2_bad_days_returns_none(self):
        metrics = [
            _MockMetrics(readiness_score=30.0),  # bas
            _MockMetrics(readiness_score=30.0),  # bas
            _MockMetrics(readiness_score=80.0),
            _MockMetrics(readiness_score=80.0),
            _MockMetrics(readiness_score=None),
            _MockMetrics(readiness_score=None),
            _MockMetrics(readiness_score=None),
        ]
        assert detect_accumulated_fatigue(metrics) is None

    def test_evidence_has_avg_readiness(self):
        metrics = _mock_7d(readiness_score=40.0)
        result = detect_accumulated_fatigue(metrics)
        assert result is not None
        assert "avg_readiness" in result.data_evidence


# ── detect_sleep_debt ─────────────────────────────────────────────────────────

class TestDetectSleepDebt:

    def test_short_sleep_triggers_critical(self):
        # < 6h = < 360 minutes
        metrics = _mock_7d(sleep_minutes=300)  # 5h
        result = detect_sleep_debt(metrics)
        assert result is not None
        assert result.severity == "critical"
        assert result.category == "sleep"

    def test_adequate_sleep_returns_none(self):
        metrics = _mock_7d(sleep_minutes=480)  # 8h
        assert detect_sleep_debt(metrics) is None

    def test_only_2_short_nights_returns_none(self):
        metrics = [
            _MockMetrics(sleep_minutes=300),  # 5h
            _MockMetrics(sleep_minutes=300),  # 5h
            _MockMetrics(sleep_minutes=480),
            _MockMetrics(sleep_minutes=480),
            _MockMetrics(sleep_minutes=480),
            _MockMetrics(sleep_minutes=None),
            _MockMetrics(sleep_minutes=None),
        ]
        assert detect_sleep_debt(metrics) is None

    def test_evidence_has_avg_hours(self):
        metrics = _mock_7d(sleep_minutes=300)
        result = detect_sleep_debt(metrics)
        assert result is not None
        assert "avg_sleep_hours" in result.data_evidence


# ── detect_dehydration_pattern ────────────────────────────────────────────────

class TestDetectDehydrationPattern:

    def test_chronic_dehydration_triggers(self):
        metrics = _mock_7d(hydration_ml=800, hydration_target_ml=2500)  # 32% < 60%
        result = detect_dehydration_pattern(metrics)
        assert result is not None
        assert result.category == "hydration"

    def test_adequate_hydration_returns_none(self):
        metrics = _mock_7d(hydration_ml=2500, hydration_target_ml=2500)
        assert detect_dehydration_pattern(metrics) is None

    def test_only_3_bad_days_returns_none(self):
        metrics = [
            _MockMetrics(hydration_ml=500, hydration_target_ml=2500),   # bas
            _MockMetrics(hydration_ml=500, hydration_target_ml=2500),   # bas
            _MockMetrics(hydration_ml=500, hydration_target_ml=2500),   # bas
            _MockMetrics(hydration_ml=2500, hydration_target_ml=2500),  # ok
            _MockMetrics(hydration_ml=2500, hydration_target_ml=2500),  # ok
            _MockMetrics(hydration_ml=2500, hydration_target_ml=2500),  # ok
            _MockMetrics(hydration_ml=2500, hydration_target_ml=2500),  # ok
        ]
        assert detect_dehydration_pattern(metrics) is None

    def test_no_target_returns_none(self):
        metrics = _mock_7d(hydration_ml=1000, hydration_target_ml=None)
        assert detect_dehydration_pattern(metrics) is None


# ── detect_overtraining_risk ──────────────────────────────────────────────────

class TestDetectOvertrainingRisk:

    def test_acwr_above_1_5_triggers(self):
        result = detect_overtraining_risk(training_load_7d=800, training_load_28d=300)
        assert result is not None
        assert result.category == "training"

    def test_acwr_above_2_is_critical(self):
        result = detect_overtraining_risk(training_load_7d=1000, training_load_28d=300)
        assert result is not None
        assert result.severity == "critical"

    def test_normal_acwr_returns_none(self):
        result = detect_overtraining_risk(training_load_7d=400, training_load_28d=400)
        assert result is None

    def test_none_28d_returns_none(self):
        result = detect_overtraining_risk(training_load_7d=800, training_load_28d=None)
        assert result is None

    def test_zero_28d_returns_none(self):
        result = detect_overtraining_risk(training_load_7d=800, training_load_28d=0)
        assert result is None

    def test_evidence_has_acwr(self):
        result = detect_overtraining_risk(training_load_7d=800, training_load_28d=400)
        assert result is not None
        assert "acwr" in result.data_evidence
        assert result.data_evidence["acwr"] == pytest.approx(2.0, abs=0.01)


# ── run_insight_engine — intégration ─────────────────────────────────────────

class TestRunInsightEngine:

    def test_empty_metrics_returns_empty(self):
        result = run_insight_engine([])
        assert result == []

    def test_healthy_user_no_insights(self):
        metrics = _mock_7d(
            protein_g=150, protein_target_g=150,
            calories_consumed=2000, calories_target=2000,
            steps=10000,
            readiness_score=80.0,
            sleep_minutes=480,
            hydration_ml=2500, hydration_target_ml=2500,
            training_load=100,
        )
        result = run_insight_engine(metrics, training_load_28d=600)
        assert len(result) == 0

    def test_critical_sorted_first(self):
        metrics = [
            _MockMetrics(
                protein_g=40, protein_target_g=150,       # warning
                calories_consumed=600, calories_target=2000,  # critical
                steps=1000,
                readiness_score=30.0,                      # critical
                sleep_minutes=240,                         # critical
                hydration_ml=500, hydration_target_ml=2500,
                training_load=0,
            )
            for _ in range(7)
        ]
        result = run_insight_engine(metrics)
        if len(result) > 1:
            assert result[0].severity in ("critical", "warning")
            for i in range(len(result) - 1):
                sev_order = {"critical": 0, "warning": 1, "info": 2}
                assert sev_order[result[i].severity] <= sev_order[result[i + 1].severity]

    def test_all_rules_evaluated(self):
        # Utilisateur avec tout en mauvais état
        metrics = _mock_7d(
            protein_g=40, protein_target_g=150,
            calories_consumed=800, calories_target=2000,
            steps=1000,
            readiness_score=30.0,
            sleep_minutes=300,
            hydration_ml=800, hydration_target_ml=2500,
            training_load=500,
        )
        result = run_insight_engine(metrics, training_load_28d=200)
        # Doit détecter plusieurs insights
        assert len(result) >= 4

    def test_insights_have_required_fields(self):
        metrics = _mock_7d(
            protein_g=40, protein_target_g=150,
            calories_consumed=None, calories_target=2000,
            steps=None, readiness_score=None,
            sleep_minutes=300,
            hydration_ml=None, hydration_target_ml=None,
            training_load=0,
        )
        result = run_insight_engine(metrics)
        for insight in result:
            assert insight.category
            assert insight.severity in ("info", "warning", "critical")
            assert insight.title
            assert insight.message

    def test_rule_errors_are_isolated(self):
        """Les erreurs dans une règle ne doivent pas planter le moteur."""
        # Un objet intentionnellement cassé
        broken = _MockMetrics()  # Aucun attribut
        result = run_insight_engine([broken] * 7)
        # Ne doit pas lever d'exception, retourne une liste (peut être vide)
        assert isinstance(result, list)
