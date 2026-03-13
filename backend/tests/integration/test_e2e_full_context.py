"""
E2E Integration Test — Full Coach Context Builder.

Tests that build_coach_context() respects the ≤5500 chars limit
even when all domains are populated.
Requires: SOMA_TEST_DATABASE_URL environment variable.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

SOMA_TEST_DATABASE_URL = os.environ.get("SOMA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not SOMA_TEST_DATABASE_URL,
    reason="PostgreSQL requis (SOMA_TEST_DATABASE_URL non défini)",
)


class TestCoachContextLimit:
    """Tests sur la limite de caractères du contexte coach."""

    def test_context_builder_imports_clean(self):
        """Le context builder s'importe sans erreur."""
        from app.services.context_builder import CoachContext
        assert CoachContext is not None

    def test_context_to_prompt_text_under_limit(self):
        """Un contexte complet reste ≤5500 chars."""
        from app.services.context_builder import CoachContext

        # Créer un contexte avec toutes les sections remplies
        context = CoachContext(
            user_name="Utilisateur Test",
            goal="Perte de poids",
            fitness_level="intermédiaire",
            age=35,
            weight_kg=80.0,
            height_cm=175.0,
            daily_metrics_summary="Calories: 2200 kcal, protéines: 150g, sommeil: 7h30. " * 3,
            readiness_summary="Readiness: 75/100. Tendance stable. Récupération bonne. " * 2,
            longevity_summary="Score longévité: 78/100. Facteurs positifs: sommeil, activité. " * 2,
            recent_insights="Insight 1: Votre métabolisme est en bonne forme. " * 5,
            metabolic_summary="État métabolique: glycogène normal, fatigue modérée. " * 2,
            twin_summary="Jumeau numérique: statut bon, readiness 75/100. " * 2,
            bio_age_summary="Âge biologique: 32 ans (delta -3 ans). Levier: sommeil. " * 2,
            adaptive_nutrition_summary="Nutrition adaptative: type TRAINING, 2500 kcal. " * 2,
            motion_summary="Mouvement: santé 82/100, tendance stable. " * 2,
            learning_summary="Profil appris: métabolisme normal, TDEE 2250 kcal. " * 2,
            injury_risk_summary="Risque blessure: faible (25/100). ACWR: 1.1. " * 2,
            biomarker_summary="Biomarqueurs: vitamine D normale, ferritine ok. " * 2,
            athlete_context=None,
        )
        text = context.to_prompt_text()
        assert len(text) <= 5500, f"Context too long: {len(text)} chars (limit 5500)"

    def test_context_without_optional_fields(self):
        """Un contexte minimal (champs optionnels None) reste valide."""
        from app.services.context_builder import CoachContext
        context = CoachContext(
            user_name="Test",
            goal="maintien",
            fitness_level="débutant",
        )
        text = context.to_prompt_text()
        assert isinstance(text, str)
        assert len(text) > 0
        assert len(text) <= 5500

    def test_context_with_max_content_stays_under_limit(self):
        """Même avec des contenus très longs, la limite de 5500 est respectée."""
        from app.services.context_builder import CoachContext
        long_content = "A" * 1000
        context = CoachContext(
            user_name="Test",
            goal="performance",
            fitness_level="expert",
            daily_metrics_summary=long_content,
            readiness_summary=long_content,
            longevity_summary=long_content,
            recent_insights=long_content,
            metabolic_summary=long_content,
            twin_summary=long_content,
            bio_age_summary=long_content,
            adaptive_nutrition_summary=long_content,
            motion_summary=long_content,
            learning_summary=long_content,
            injury_risk_summary=long_content,
            biomarker_summary=long_content,
        )
        text = context.to_prompt_text()
        assert len(text) <= 5500
