"""SOMA LOT 13 - Learning domain API endpoints."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.cache.cache_service import get_cache_service
from app.cache.cache_keys import CacheKeys, TTL

from .service import (
    compute_user_learning_profile,
    build_learning_summary,
    WeightCalorieObservation,
    ReadinessObservation,
    TrainingObservation,
    NutritionReadinessObservation,
)
from .schemas import (
    UserLearningProfileResponse,
    LearningInsightsResponse,
    LearningInsightResponse,
    LearningRecomputeResponse,
)

logger = logging.getLogger(__name__)
learning_router = APIRouter(prefix="/learning", tags=["learning"])
cache = get_cache_service()


# --- Helpers ------------------------------------------------------------------

async def _load_learning_inputs(
    db: AsyncSession,
    user_id: str,
    days: int = 90,
):
    """Load all history data needed for learning analysis."""
    from app.models.metrics import DailyMetrics
    from app.models.scores import ReadinessScore
    from app.models.workout import WorkoutSession
    from app.models.nutrition import FoodEntry

    since = date.today() - timedelta(days=days)
    user_uuid = user_id

    # DailyMetrics: weight + calories
    metrics_result = await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.user_id == user_uuid, DailyMetrics.metrics_date >= since)
        .order_by(DailyMetrics.metrics_date)
    )
    metrics_rows = metrics_result.scalars().all()

    weight_calorie_obs = []
    readiness_by_date = {}
    sleep_by_date = {}

    for m in metrics_rows:
        if m.weight_kg and m.total_calories:
            weight_calorie_obs.append(
                WeightCalorieObservation(
                    obs_date=m.metrics_date,
                    weight_kg=m.weight_kg,
                    calories_consumed=m.total_calories,
                )
            )

    # ReadinessScores
    readiness_result = await db.execute(
        select(ReadinessScore)
        .where(ReadinessScore.user_id == user_uuid, ReadinessScore.score_date >= since)
        .order_by(ReadinessScore.score_date)
    )
    readiness_rows = readiness_result.scalars().all()

    readiness_obs = []
    readiness_list = []
    for r in readiness_rows:
        readiness_obs.append(
            ReadinessObservation(
                obs_date=r.score_date,
                readiness_score=r.overall_readiness or 60.0,
            )
        )
        readiness_list.append(r.overall_readiness or 60.0)
        readiness_by_date[r.score_date] = r.overall_readiness or 60.0

    # Training sessions -> load observations
    workout_result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_uuid, WorkoutSession.session_date >= since)
        .order_by(WorkoutSession.session_date)
    )
    workout_rows = workout_result.scalars().all()

    training_obs = []
    for w in workout_rows:
        duration_min = w.duration_minutes or 45
        rpe = 7.0  # default RPE (no RPE stored currently)
        load = duration_min * rpe  # simple load metric
        training_obs.append(
            TrainingObservation(
                session_date=w.session_date,
                training_load=load,
            )
        )

    # Nutrition + readiness pairing
    nutrition_obs = []
    for m in metrics_rows:
        if m.carbs_g and m.protein_g:
            next_date = m.metrics_date + timedelta(days=1)
            next_readiness = readiness_by_date.get(next_date)
            nutrition_obs.append(
                NutritionReadinessObservation(
                    obs_date=m.metrics_date,
                    carbs_g=m.carbs_g,
                    protein_g=m.protein_g,
                    weight_kg=m.weight_kg or 75.0,
                    next_day_readiness=next_readiness,
                )
            )

    # Sleep minutes from DailyMetrics
    sleep_minutes = [m.sleep_duration_minutes for m in metrics_rows if m.sleep_duration_minutes]

    return {
        "weight_calorie_obs": weight_calorie_obs,
        "readiness_obs": readiness_obs,
        "training_obs": training_obs,
        "nutrition_readiness_obs": nutrition_obs,
        "sleep_minutes": sleep_minutes,
        "readiness_scores": readiness_list,
    }


# --- Endpoints ----------------------------------------------------------------

@learning_router.get("/profile", response_model=UserLearningProfileResponse)
async def get_learning_profile(
    days: int = Query(default=90, ge=14, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized learning profile computed from user's history."""
    user_id = str(current_user.id)
    cache_key = f"learning_profile:{user_id}"

    # Try cache
    cached = await cache.get(cache_key)
    if cached:
        return UserLearningProfileResponse(**cached)

    inputs = await _load_learning_inputs(db, current_user.id, days=days)
    result = compute_user_learning_profile(**inputs)

    response = UserLearningProfileResponse(**result.to_dict())

    await cache.set(cache_key, response.model_dump(), ttl=TTL.BIOLOGICAL_AGE)  # 24h
    return response


@learning_router.get("/insights", response_model=LearningInsightsResponse)
async def get_learning_insights(
    days: int = Query(default=90, ge=14, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized insights derived from learning profile."""
    user_id = str(current_user.id)
    inputs = await _load_learning_inputs(db, current_user.id, days=days)
    result = compute_user_learning_profile(**inputs)

    profile_resp = UserLearningProfileResponse(**result.to_dict())

    # Convert text insights to structured responses
    typed_insights = []
    for insight in result.insights:
        if "metabolisme" in insight.lower() or "tdee" in insight.lower():
            itype = "metabolism"
        elif "recupera" in insight.lower():
            itype = "recovery"
        elif "glucide" in insight.lower() or "carb" in insight.lower():
            itype = "nutrition_carbs"
        elif "proteine" in insight.lower():
            itype = "nutrition_protein"
        elif "sommeil" in insight.lower():
            itype = "sleep"
        else:
            itype = "training"

        typed_insights.append(
            LearningInsightResponse(
                insight_type=itype,
                title=insight[:60],
                description=insight,
                confidence=result.confidence,
                actionable=True,
            )
        )

    recommendations = []
    if result.true_tdee:
        recommendations.append(
            f"Utilisez {round(result.true_tdee)} kcal/j comme cible calorique reelle "
            f"(vs {round(result.estimated_mifflin_tdee or 0)} kcal estime)."
        )
    if result.recovery_profile == "slow":
        recommendations.append(
            "Planifiez 48h de recuperation entre seances intenses."
        )
    if result.carb_response > 0.2:
        recommendations.append(
            "Augmentez les glucides les jours d'entrainement pour optimiser vos performances."
        )

    return LearningInsightsResponse(
        user_id=user_id,
        profile=profile_resp,
        top_insights=typed_insights,
        recommendations=recommendations,
    )


@learning_router.post("/recompute", response_model=LearningRecomputeResponse)
async def recompute_learning_profile(
    days: int = Query(default=90, ge=14, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Force recompute of learning profile (clears cache)."""
    user_id = str(current_user.id)
    cache_key = f"learning_profile:{user_id}"
    await cache.delete(cache_key)

    inputs = await _load_learning_inputs(db, current_user.id, days=days)
    result = compute_user_learning_profile(**inputs)

    return LearningRecomputeResponse(
        success=True,
        message=f"Profil recalcule sur {result.days_analyzed} jours d'historique.",
        days_analyzed=result.days_analyzed,
        confidence=result.confidence,
    )
