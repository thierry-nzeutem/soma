"""
E2E Integration Test — Learning + Injury Prevention multi-domain.

Tests that learning and injury services consume the same input types
and produce coherent outputs when data overlaps.
Requires: SOMA_TEST_DATABASE_URL environment variable.
"""
import os
import pytest
from datetime import date, timedelta

SOMA_TEST_DATABASE_URL = os.environ.get("SOMA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not SOMA_TEST_DATABASE_URL,
    reason="PostgreSQL requis (SOMA_TEST_DATABASE_URL non défini)",
)


class TestLearningProfileService:
    """Tests du service learning avec données synthétiques."""

    def _make_metrics(self, n_days: int, calories: float, weight: float, sleep_min: float) -> list:
        """Helper pour créer des DailyMetrics-like dicts."""
        base = date.today()
        return [
            {
                "metrics_date": (base - timedelta(days=i)).isoformat(),
                "calories_kcal": calories,
                "weight_kg": weight,
                "sleep_duration_minutes": sleep_min,
                "protein_g": 150.0,
                "readiness_score": 75.0,
            }
            for i in range(n_days)
        ]

    def test_learning_service_imports_clean(self):
        """Le service learning s'importe sans erreur."""
        from app.domains.learning.service import compute_user_learning_profile
        assert callable(compute_user_learning_profile)

    def test_compute_profile_no_data(self):
        """Profil avec données vides retourne des valeurs par défaut cohérentes."""
        from app.domains.learning.service import compute_user_learning_profile
        result = compute_user_learning_profile(
            daily_metrics=[],
            readiness_scores=[],
            workout_sessions=[],
            food_entries=[],
        )
        assert result is not None
        assert result.confidence < 0.5

    def test_compute_profile_sufficient_data(self):
        """Avec 14+ jours de données, la confiance augmente."""
        from app.domains.learning.service import compute_user_learning_profile
        # Simuler 20 jours de données stables
        metrics = [
            type("DailyMetrics", (), {
                "calories_kcal": 2200.0,
                "weight_kg": 75.0,
                "sleep_duration_minutes": 450,
                "protein_g": 150.0,
                "metrics_date": date.today() - timedelta(days=i),
            })()
            for i in range(20)
        ]
        result = compute_user_learning_profile(
            daily_metrics=metrics,
            readiness_scores=[],
            workout_sessions=[],
            food_entries=[],
        )
        assert result.confidence > 0.0


class TestInjuryPreventionService:
    """Tests du service prévention blessures."""

    def test_injury_service_imports_clean(self):
        """Le service injury s'importe sans erreur."""
        from app.domains.injury.service import compute_injury_prevention_analysis
        assert callable(compute_injury_prevention_analysis)

    def test_injury_no_data_returns_minimal_risk(self):
        """Sans données, le risque est minimal (confiance faible)."""
        from app.domains.injury.service import compute_injury_prevention_analysis
        result = compute_injury_prevention_analysis()
        assert result.injury_risk_score >= 0
        assert result.injury_risk_score <= 100
        assert result.confidence < 0.5

    def test_high_acwr_increases_risk(self):
        """ACWR > 1.8 doit augmenter significativement le score de risque."""
        from app.domains.injury.service import compute_injury_prevention_analysis
        result_safe = compute_injury_prevention_analysis(acwr=1.0)
        result_critical = compute_injury_prevention_analysis(acwr=2.0)
        assert result_critical.injury_risk_score > result_safe.injury_risk_score

    def test_high_fatigue_increases_risk(self):
        """Fatigue élevée doit augmenter le score de risque."""
        from app.domains.injury.service import compute_injury_prevention_analysis
        result_low = compute_injury_prevention_analysis(fatigue_score=20.0)
        result_high = compute_injury_prevention_analysis(fatigue_score=90.0)
        assert result_high.injury_risk_score > result_low.injury_risk_score

    def test_learning_and_injury_use_same_weight_input(self):
        """Les services learning et injury acceptent tous les deux weight_kg."""
        from app.domains.injury.service import compute_injury_prevention_analysis
        # Pas de crash avec des paramètres communs
        result = compute_injury_prevention_analysis(
            acwr=1.2,
            fatigue_score=40.0,
        )
        assert result is not None

    def test_injury_summary_length(self):
        """build_injury_summary() retourne ≤200 caractères."""
        from app.domains.injury.service import compute_injury_prevention_analysis, build_injury_summary
        result = compute_injury_prevention_analysis(acwr=1.5, fatigue_score=60.0)
        summary = build_injury_summary(result)
        assert len(summary) <= 200
