"""
SOMA LOT 18 — Tests unitaires Onboarding.

Couvre :
  - OnboardingRequest : validation Pydantic (champs, constraints)
  - OnboardingInitialTargets : champs et types
  - OnboardingResponse : structure et champs obligatoires
  - Messages de bienvenue : un message par objectif

~12 tests purs, aucune dépendance DB.
"""
import pytest
from pydantic import ValidationError

from app.schemas.onboarding import (
    OnboardingRequest,
    OnboardingInitialTargets,
    OnboardingResponse,
)


# ── Tests OnboardingRequest ─────────────────────────────────────────────────

class TestOnboardingRequest:
    """Validation des champs de la requête d'onboarding."""

    def _valid_payload(self, **overrides) -> dict:
        base = {
            "age": 28,
            "sex": "male",
            "height_cm": 178.0,
            "weight_kg": 75.0,
            "primary_goal": "performance",
            "activity_level": "moderate",
        }
        base.update(overrides)
        return base

    def test_valid_minimal_request(self):
        req = OnboardingRequest(**self._valid_payload())
        assert req.age == 28
        assert req.sex == "male"
        assert req.primary_goal == "performance"

    def test_optional_first_name(self):
        req = OnboardingRequest(**self._valid_payload(first_name="Lucas"))
        assert req.first_name == "Lucas"

    def test_first_name_defaults_none(self):
        req = OnboardingRequest(**self._valid_payload())
        assert req.first_name is None

    def test_age_minimum_is_13(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(age=12))

    def test_age_13_is_valid(self):
        req = OnboardingRequest(**self._valid_payload(age=13))
        assert req.age == 13

    def test_age_maximum_is_120(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(age=121))

    def test_invalid_sex_raises(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(sex="unknown"))

    def test_sex_other_is_valid(self):
        req = OnboardingRequest(**self._valid_payload(sex="other"))
        assert req.sex == "other"

    def test_primary_goal_weight_loss_is_valid(self):
        req = OnboardingRequest(**self._valid_payload(primary_goal="weight_loss"))
        assert req.primary_goal == "weight_loss"

    def test_primary_goal_longevity_is_valid(self):
        req = OnboardingRequest(**self._valid_payload(primary_goal="longevity"))
        assert req.primary_goal == "longevity"

    def test_invalid_primary_goal_raises(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(primary_goal="muscle_gain"))

    def test_activity_level_athlete_is_valid(self):
        req = OnboardingRequest(**self._valid_payload(activity_level="athlete"))
        assert req.activity_level == "athlete"

    def test_invalid_activity_level_raises(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(activity_level="very_active"))

    def test_fitness_level_default_beginner(self):
        req = OnboardingRequest(**self._valid_payload())
        assert req.fitness_level == "beginner"

    def test_has_biomarker_access_defaults_false(self):
        req = OnboardingRequest(**self._valid_payload())
        assert req.has_biomarker_access is False

    def test_sleep_hours_default(self):
        req = OnboardingRequest(**self._valid_payload())
        assert req.sleep_hours_per_night == 7.5

    def test_sleep_hours_min_3(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(sleep_hours_per_night=2.9))

    def test_sleep_hours_max_12(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(sleep_hours_per_night=12.1))

    def test_sport_frequency_default(self):
        req = OnboardingRequest(**self._valid_payload())
        assert req.sport_frequency_per_week == 3

    def test_sport_frequency_max_21(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(sport_frequency_per_week=22))

    def test_estimated_sleep_quality_valid_values(self):
        for quality in ("poor", "fair", "good", "excellent"):
            req = OnboardingRequest(**self._valid_payload(estimated_sleep_quality=quality))
            assert req.estimated_sleep_quality == quality

    def test_estimated_sleep_quality_invalid_raises(self):
        with pytest.raises(ValidationError):
            OnboardingRequest(**self._valid_payload(estimated_sleep_quality="mediocre"))


# ── Tests OnboardingInitialTargets ─────────────────────────────────────────

class TestOnboardingInitialTargets:
    """Structure des objectifs initiaux calculés."""

    def test_all_fields_present(self):
        targets = OnboardingInitialTargets(
            calories_target_kcal=2200.0,
            protein_target_g=150.0,
            hydration_target_ml=2500,
            steps_goal=10000,
            sleep_hours_target=7.5,
        )
        assert targets.calories_target_kcal == 2200.0
        assert targets.protein_target_g == 150.0
        assert targets.hydration_target_ml == 2500
        assert targets.steps_goal == 10000
        assert targets.sleep_hours_target == 7.5


# ── Tests OnboardingResponse ────────────────────────────────────────────────

class TestOnboardingResponse:
    """Structure de la réponse d'onboarding."""

    def _make_response(self, **overrides) -> dict:
        base = {
            "profile_updated": True,
            "body_metric_logged": True,
            "initial_targets": OnboardingInitialTargets(
                calories_target_kcal=2200.0,
                protein_target_g=150.0,
                hydration_target_ml=2500,
                steps_goal=10000,
                sleep_hours_target=7.5,
            ),
            "next_step": "view_briefing",
            "coach_welcome_message": "Bienvenue dans SOMA.",
        }
        base.update(overrides)
        return base

    def test_valid_response(self):
        resp = OnboardingResponse(**self._make_response())
        assert resp.profile_updated is True
        assert resp.body_metric_logged is True
        assert resp.next_step == "view_briefing"

    def test_coach_welcome_message_not_empty(self):
        resp = OnboardingResponse(**self._make_response())
        assert len(resp.coach_welcome_message) > 0

    def test_initial_targets_structure(self):
        resp = OnboardingResponse(**self._make_response())
        assert resp.initial_targets.calories_target_kcal == 2200.0
        assert resp.initial_targets.steps_goal == 10000
