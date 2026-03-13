"""Schémas Pydantic — Onboarding Intelligent — LOT 18.

POST /profile/onboarding : initialise SOMA pour un nouvel utilisateur.
"""
from typing import Optional

from pydantic import BaseModel, Field


class OnboardingRequest(BaseModel):
    """Données collectées lors du flow onboarding en 7 étapes."""

    # ── Identité ──────────────────────────────────────────────────────────────
    first_name: Optional[str] = Field(None, max_length=100)
    age: int = Field(..., ge=13, le=120, description="Âge en années")
    sex: str = Field(..., pattern="^(male|female|other)$")
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=30, le=300)
    goal_weight_kg: Optional[float] = Field(None, ge=30, le=300)

    # ── Objectif ──────────────────────────────────────────────────────────────
    primary_goal: str = Field(
        ...,
        pattern="^(performance|health|weight_loss|longevity)$",
        description="Objectif principal : performance, santé, perte de poids ou longévité",
    )

    # ── Activité ──────────────────────────────────────────────────────────────
    activity_level: str = Field(
        ...,
        pattern="^(sedentary|moderate|athlete)$",
        description="Niveau d'activité général",
    )
    sport_frequency_per_week: int = Field(
        default=3,
        ge=0,
        le=21,
        description="Nombre de séances de sport par semaine",
    )
    fitness_level: str = Field(
        default="beginner",
        pattern="^(beginner|intermediate|advanced|athlete)$",
    )

    # ── Sommeil ───────────────────────────────────────────────────────────────
    estimated_sleep_quality: str = Field(
        default="fair",
        pattern="^(poor|fair|good|excellent)$",
        description="Qualité de sommeil estimée par l'utilisateur",
    )
    sleep_hours_per_night: float = Field(
        default=7.5,
        ge=3.0,
        le=12.0,
        description="Heures de sommeil par nuit",
    )

    # ── Optionnel ─────────────────────────────────────────────────────────────
    has_biomarker_access: bool = Field(
        default=False,
        description="L'utilisateur a-t-il accès à des analyses biologiques ?",
    )


class OnboardingInitialTargets(BaseModel):
    """Objectifs initiaux calculés immédiatement après onboarding."""

    calories_target_kcal: float
    protein_target_g: float
    hydration_target_ml: int
    steps_goal: int
    sleep_hours_target: float


class OnboardingResponse(BaseModel):
    """Réponse de l'onboarding — confirme la configuration et retourne les objectifs."""

    profile_updated: bool = True
    body_metric_logged: bool = True

    # Objectifs calculés depuis le profil
    initial_targets: OnboardingInitialTargets

    # Prochaine étape suggérée pour l'UI
    next_step: str = Field(
        default="explore",
        description="'explore' | 'add_first_workout' | 'view_briefing'",
    )

    # Message de bienvenue du coach (statique, non IA)
    coach_welcome_message: str
