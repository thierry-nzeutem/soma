"""Endpoint Onboarding Intelligent — LOT 18.

POST /profile/onboarding : initialise SOMA pour un nouvel utilisateur.

Flow :
  1. PATCH UserProfile (âge, sexe, taille, objectif, activité, sommeil, etc.)
  2. POST BodyMetric (poids initial)
  3. Calcul des objectifs initiaux via calculate_* (réutilise l'existant)
  4. Track analytics "onboarding_complete"
  5. Retourne OnboardingResponse avec les objectifs et un message de bienvenue

Ce endpoint est conçu pour être appelé une seule fois, après l'inscription,
mais peut être rappelé pour mettre à jour le profil (idempotent).
"""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserProfile, BodyMetric
from app.core.deps import get_current_user
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse, OnboardingInitialTargets
from app.services.calculations import (
    calculate_bmr_mifflin,
    calculate_tdee,
    calculate_calorie_target,
    calculate_protein_target,
    calculate_hydration_target,
)
from app.core.analytics import track_event

logger = logging.getLogger(__name__)

onboarding_router = APIRouter(prefix="/profile", tags=["Onboarding"])

# ── Messages de bienvenue par objectif ────────────────────────────────────────
_WELCOME_MESSAGES: dict[str, str] = {
    "performance": (
        "Bienvenue dans SOMA, coach IA de performance. "
        "Vos objectifs nutritionnels et d'entraînement sont configurés. "
        "Commencez par logger votre première séance pour que SOMA apprenne votre profil."
    ),
    "health": (
        "Bienvenue dans SOMA. Votre profil santé est prêt. "
        "SOMA analysera chaque jour vos données pour vous guider vers un équilibre optimal. "
        "Votre premier briefing matinal sera disponible demain matin."
    ),
    "weight_loss": (
        "Bienvenue dans SOMA. Votre objectif de transformation est enregistré. "
        "SOMA calcule votre déficit calorique optimal et adapte vos recommandations chaque jour. "
        "Consultez votre plan nutrition dès maintenant."
    ),
    "longevity": (
        "Bienvenue dans SOMA. Votre parcours longévité commence aujourd'hui. "
        "SOMA suit votre âge biologique et identifie vos leviers d'amélioration. "
        "Ajoutez vos biomarqueurs pour des analyses plus précises."
    ),
}

_DEFAULT_WELCOME = (
    "Bienvenue dans SOMA, votre coach santé IA personnel. "
    "Votre profil est configuré. Commencez à logger vos données pour des recommandations personnalisées."
)

# Objectif de pas par niveau d'activité
_STEPS_BY_ACTIVITY: dict[str, int] = {
    "sedentary": 7000,
    "moderate": 10000,
    "athlete": 12000,
}


@onboarding_router.post("/onboarding", response_model=OnboardingResponse)
async def complete_onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Flow d'onboarding SOMA en une seule requête.

    Initialise le profil utilisateur, log le poids initial et retourne
    les objectifs journaliers calculés.

    Peut être rappelé pour mettre à jour le profil (idempotent).
    """
    # ── 1. Récupérer ou créer le profil ───────────────────────────────────────
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    profile_updated = False
    if profile is None:
        profile = UserProfile(
            id=uuid.uuid4(),
            user_id=current_user.id,
        )
        db.add(profile)
        profile_updated = True

    # Mise à jour des champs onboarding
    if body.first_name:
        profile.first_name = body.first_name
    profile.age = body.age
    profile.sex = body.sex
    profile.height_cm = body.height_cm
    profile.goal_weight_kg = body.goal_weight_kg

    # Mapping objectif → valeur ProfileUpdate
    _goal_map = {
        "performance": "performance",
        "health": "maintenance",
        "weight_loss": "weight_loss",
        "longevity": "maintenance",
    }
    profile.primary_goal = _goal_map.get(body.primary_goal, body.primary_goal)

    # Mapping activité → valeur ProfileUpdate
    _activity_map = {
        "sedentary": "sedentary",
        "moderate": "moderate",
        "athlete": "very_active",
    }
    profile.activity_level = _activity_map.get(body.activity_level, body.activity_level)
    profile.fitness_level = body.fitness_level

    # Sommeil
    profile.perceived_sleep_quality = body.estimated_sleep_quality

    profile_updated = True

    # ── 2. Logger le poids initial ────────────────────────────────────────────
    body_metric_logged = False
    try:
        metric = BodyMetric(
            id=uuid.uuid4(),
            user_id=current_user.id,
            weight_kg=body.weight_kg,
            measured_at=datetime.now(timezone.utc),
            source="onboarding",
            data_quality="self_reported",
        )
        db.add(metric)
        body_metric_logged = True
    except Exception:
        logger.warning("onboarding: could not log body metric", exc_info=True)

    await db.commit()
    await db.refresh(profile)

    # ── 3. Calculer les objectifs initiaux ────────────────────────────────────
    try:
        bmr = calculate_bmr_mifflin(body.weight_kg, body.height_cm, body.age, body.sex)
        tdee = calculate_tdee(bmr, profile.activity_level or "moderate")
        cal_target, _ = calculate_calorie_target(
            tdee, profile.primary_goal or "maintenance", body.weight_kg, body.goal_weight_kg
        )
        p_min, p_max, _ = calculate_protein_target(
            body.weight_kg, profile.primary_goal or "maintenance", body.fitness_level or "beginner"
        )
        hydration, _ = calculate_hydration_target(body.weight_kg, profile.activity_level or "moderate")
        protein_target = round((p_min + p_max) / 2, 0)
    except Exception:
        logger.warning("onboarding: calculation fallback", exc_info=True)
        cal_target = 2000.0
        protein_target = 120.0
        hydration = 2500

    initial_targets = OnboardingInitialTargets(
        calories_target_kcal=round(cal_target, 0),
        protein_target_g=float(protein_target),
        hydration_target_ml=int(hydration),
        steps_goal=_STEPS_BY_ACTIVITY.get(body.activity_level, 10000),
        sleep_hours_target=body.sleep_hours_per_night,
    )

    # ── 4. Analytics ──────────────────────────────────────────────────────────
    await track_event(db, current_user.id, "onboarding_complete", {
        "primary_goal": body.primary_goal,
        "activity_level": body.activity_level,
        "has_biomarker_access": body.has_biomarker_access,
    })

    # ── 5. Message de bienvenue ───────────────────────────────────────────────
    welcome = _WELCOME_MESSAGES.get(body.primary_goal, _DEFAULT_WELCOME)

    # Prochaine étape recommandée
    next_step = "view_briefing" if body.sport_frequency_per_week > 0 else "explore"

    return OnboardingResponse(
        profile_updated=profile_updated,
        body_metric_logged=body_metric_logged,
        initial_targets=initial_targets,
        next_step=next_step,
        coach_welcome_message=welcome,
    )
