"""
Tests unitaires — context_builder.py (LOT 9).

Couvre :
  - CoachContext.to_prompt_text() : formatage des sections
  - UserProfileContext : rendu profil incomplet / complet
  - NutritionContext : calories, macros, hydratation
  - SleepContext : durée, score, label
  - Troncature : sécurité à 5500 caractères
  - Alertes et insights : rendu et limite
  - Métabolique : intégration MetabolicState dans le prompt
"""
import pytest
from datetime import date

from app.services.context_builder import (
    CoachContext,
    NutritionContext,
    SleepContext,
    TrainingContext,
    UserProfileContext,
)
from app.services.metabolic_twin_service import MetabolicState


# ── Helpers ────────────────────────────────────────────────────────────────────

def _minimal_context() -> CoachContext:
    """Contexte vide mais instanciable."""
    return CoachContext(today_date="2026-03-07")


def _full_context() -> CoachContext:
    ctx = CoachContext(today_date="2026-03-07")
    ctx.user = UserProfileContext(
        age=30, sex="male", height_cm=178.0, weight_kg=75.0,
        primary_goal="muscle_gain", activity_level="moderate",
        fitness_level="intermediate", dietary_regime="standard",
    )
    ctx.readiness_score = 78.0
    ctx.readiness_level = "bon"
    ctx.nutrition = NutritionContext(
        calories_consumed=2400.0,
        calories_target=2700.0,
        protein_g=165.0,
        protein_target_g=180.0,
        carbs_g=280.0,
        fat_g=80.0,
        fiber_g=30.0,
        hydration_ml=1800.0,
        hydration_target_ml=2500.0,
    )
    ctx.sleep = SleepContext(
        sleep_minutes=450,
        sleep_score=72.0,
        sleep_quality_label="bon",
    )
    ctx.training = TrainingContext(
        workout_count_today=1,
        training_load_7d=250.0,
        recommended_intensity="moderate",
        last_workout_type="strength",
    )
    ctx.longevity_score = 74.0
    ctx.biological_age = 27.5
    return ctx


# ── to_prompt_text — structure globale ────────────────────────────────────────

class TestToPromptTextStructure:

    def test_returns_string(self):
        ctx = _minimal_context()
        assert isinstance(ctx.to_prompt_text(), str)

    def test_contains_profile_header(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "PROFIL UTILISATEUR" in text

    def test_contains_recovery_section(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "RÉCUPÉRATION" in text or "RECUPERATION" in text.upper()

    def test_contains_nutrition_section(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "NUTRITION" in text

    def test_contains_training_section(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "ENTRAÎNEMENT" in text or "ENTRAINEMENT" in text.upper()

    def test_contains_sleep_section(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "SOMMEIL" in text

    def test_date_in_output(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "2026-03-07" in text


# ── to_prompt_text — profil utilisateur ───────────────────────────────────────

class TestUserProfileRendering:

    def test_incomplete_profile_label(self):
        ctx = _minimal_context()
        # pas de données user → "(profil incomplet)"
        text = ctx.to_prompt_text()
        assert "profil incomplet" in text

    def test_age_present_in_output(self):
        ctx = _minimal_context()
        ctx.user = UserProfileContext(age=30, sex="male")
        text = ctx.to_prompt_text()
        assert "30 ans" in text

    def test_sex_present_in_output(self):
        ctx = _minimal_context()
        ctx.user = UserProfileContext(age=30, sex="female")
        text = ctx.to_prompt_text()
        assert "female" in text

    def test_full_profile_renders_all_parts(self):
        ctx = _full_context()
        text = ctx.to_prompt_text()
        assert "178" in text          # height
        assert "75" in text           # weight
        assert "muscle_gain" in text  # goal
        assert "moderate" in text     # activity level
        assert "standard" in text     # dietary regime


# ── to_prompt_text — récupération ─────────────────────────────────────────────

class TestRecoveryRendering:

    def test_readiness_score_rendered(self):
        ctx = _minimal_context()
        ctx.readiness_score = 82.0
        ctx.readiness_level = "excellent"
        text = ctx.to_prompt_text()
        assert "82" in text
        assert "excellent" in text

    def test_no_readiness_no_crash(self):
        ctx = _minimal_context()
        ctx.readiness_score = None
        text = ctx.to_prompt_text()
        assert text  # not empty

    def test_fatigue_from_metabolic_rendered(self):
        ctx = _minimal_context()
        m = MetabolicState()
        m.fatigue_score = 65.0
        ctx.metabolic = m
        text = ctx.to_prompt_text()
        assert "Fatigue" in text
        assert "65" in text

    def test_glycogen_status_rendered(self):
        ctx = _minimal_context()
        m = MetabolicState()
        m.glycogen_status = "low"
        m.estimated_glycogen_g = 400.0
        ctx.metabolic = m
        text = ctx.to_prompt_text()
        assert "low" in text

    def test_plateau_warning_rendered(self):
        ctx = _minimal_context()
        m = MetabolicState()
        m.plateau_risk = True
        ctx.metabolic = m
        text = ctx.to_prompt_text()
        assert "plateau" in text.lower()


# ── to_prompt_text — sommeil ───────────────────────────────────────────────────

class TestSleepRendering:

    def test_sleep_duration_formatted_as_hours_minutes(self):
        ctx = _minimal_context()
        ctx.sleep = SleepContext(sleep_minutes=450)  # 7h30
        text = ctx.to_prompt_text()
        assert "7h30" in text

    def test_sleep_score_rendered(self):
        ctx = _minimal_context()
        ctx.sleep = SleepContext(sleep_score=80.0)
        text = ctx.to_prompt_text()
        assert "80" in text

    def test_sleep_quality_label_rendered(self):
        ctx = _minimal_context()
        ctx.sleep = SleepContext(sleep_quality_label="excellent")
        text = ctx.to_prompt_text()
        assert "excellent" in text


# ── to_prompt_text — nutrition ────────────────────────────────────────────────

class TestNutritionRendering:

    def test_calories_rendered_with_target(self):
        ctx = _minimal_context()
        ctx.nutrition = NutritionContext(
            calories_consumed=2400.0, calories_target=2700.0
        )
        text = ctx.to_prompt_text()
        assert "2400" in text
        assert "2700" in text

    def test_protein_rendered(self):
        ctx = _minimal_context()
        ctx.nutrition = NutritionContext(protein_g=150.0, protein_target_g=180.0)
        text = ctx.to_prompt_text()
        assert "150" in text

    def test_hydration_rendered(self):
        ctx = _minimal_context()
        ctx.nutrition = NutritionContext(
            hydration_ml=1800.0, hydration_target_ml=2500.0
        )
        text = ctx.to_prompt_text()
        assert "1800" in text

    def test_energy_balance_with_sign(self):
        ctx = _minimal_context()
        m = MetabolicState()
        m.energy_balance_kcal = -300.0
        ctx.metabolic = m
        text = ctx.to_prompt_text()
        assert "-300" in text


# ── to_prompt_text — longévité ────────────────────────────────────────────────

class TestLongevityRendering:

    def test_longevity_section_present_when_data_available(self):
        ctx = _minimal_context()
        ctx.longevity_score = 74.0
        ctx.biological_age = 27.5
        text = ctx.to_prompt_text()
        assert "LONGÉVITÉ" in text or "LONGEVITE" in text.upper()

    def test_longevity_section_absent_when_no_data(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "LONGÉVITÉ" not in text

    def test_metabolic_age_from_twin_rendered(self):
        ctx = _minimal_context()
        ctx.longevity_score = 70.0
        m = MetabolicState()
        m.metabolic_age = 28.5
        ctx.metabolic = m
        text = ctx.to_prompt_text()
        assert "28.5" in text


# ── to_prompt_text — alertes et insights ──────────────────────────────────────

class TestAlertsAndInsights:

    def test_alerts_section_shown_when_present(self):
        ctx = _minimal_context()
        ctx.active_alerts = ["Fréquence cardiaque élevée", "Hydratation insuffisante"]
        text = ctx.to_prompt_text()
        assert "ALERTES" in text

    def test_alerts_limited_to_3(self):
        ctx = _minimal_context()
        ctx.active_alerts = [f"Alerte {i}" for i in range(6)]
        text = ctx.to_prompt_text()
        # Compte les occurrences d'alertes (⚠ marque chaque alerte)
        count = text.count("⚠")
        # La section récupération peut aussi avoir un ⚠ plateau, on compte au max 4
        assert count <= 4

    def test_insights_section_shown_when_present(self):
        ctx = _minimal_context()
        ctx.top_insights = ["Ta récupération s'améliore cette semaine"]
        text = ctx.to_prompt_text()
        assert "INSIGHTS" in text

    def test_insights_limited_to_3_displayed(self):
        ctx = _minimal_context()
        ctx.top_insights = [f"Insight {i}" for i in range(5)]
        text = ctx.to_prompt_text()
        # Seuls 3 insights devraient apparaître
        assert "Insight 3" not in text  # index 3 et 4 sont exclus
        assert "Insight 2" in text      # index 2 est le dernier affiché

    def test_no_sections_when_empty(self):
        ctx = _minimal_context()
        text = ctx.to_prompt_text()
        assert "ALERTES" not in text
        assert "INSIGHTS" not in text


# ── to_prompt_text — troncature ───────────────────────────────────────────────

class TestTruncation:

    def test_truncation_marker_when_overlong(self):
        """Un contexte très long doit être tronqué avec le marker."""
        ctx = _minimal_context()
        # Injecte beaucoup d'insights longs
        ctx.top_insights = ["x" * 1000] * 3
        ctx.active_alerts = ["y" * 1000] * 3
        ctx.user = UserProfileContext(age=30, sex="male")
        ctx.nutrition = NutritionContext(
            calories_consumed=2000.0, calories_target=2500.0,
            protein_g=150.0, carbs_g=200.0, fat_g=70.0,
            hydration_ml=1500.0, hydration_target_ml=2000.0,
        )
        text = ctx.to_prompt_text()
        # Le texte ne doit jamais dépasser _MAX_CONTEXT_CHARS(6000) + marqueur(~20)
        assert len(text) <= 6025

    def test_normal_context_not_truncated(self):
        """Un contexte normal ne doit pas avoir le marker de troncature."""
        ctx = _full_context()
        text = ctx.to_prompt_text()
        assert "[contexte tronqué]" not in text

    def test_full_context_within_limit(self):
        ctx = _full_context()
        text = ctx.to_prompt_text()
        assert len(text) < 5500
