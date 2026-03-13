"""
Adaptive Nutrition Engine — API endpoints.

Routes:
  GET  /nutrition/adaptive-targets   → compact macro targets
  GET  /nutrition/adaptive-plan      → full AdaptiveNutritionPlan
  POST /nutrition/adaptive-plan/recompute → force recompute + invalidate cache

Data loading: reads MetabolicStateSnapshot, ReadinessScore, UserProfile, DailyMetrics.
Cache: 6h (ADAPTIVE_NUTRITION_TTL) via CacheService.
"""
from __future__ import annotations

import uuid
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.scores import MetabolicStateSnapshot, ReadinessScore
from app.models.metrics import DailyMetrics

from app.domains.adaptive_nutrition.service import (
    compute_adaptive_plan,
    build_adaptive_nutrition_summary,
    AdaptiveNutritionPlan,
)
from app.domains.adaptive_nutrition.schemas import (
    AdaptiveNutritionPlanResponse,
    AdaptiveNutritionTargetsResponse,
    NutritionTargetResponse,
)
from app.cache.cache_service import get_cache_service
from app.cache.cache_keys import CacheKeys, TTL

logger = logging.getLogger(__name__)

adaptive_nutrition_router = APIRouter(prefix="/nutrition", tags=["Adaptive Nutrition"])


# ── Data loading helper ────────────────────────────────────────────────────────

async def _load_adaptive_inputs(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> dict:
    """Load all inputs needed for the Adaptive Nutrition Engine."""

    # MetabolicStateSnapshot — most recent
    metabolic = (await db.execute(
        select(MetabolicStateSnapshot)
        .where(MetabolicStateSnapshot.user_id == user_id,
               MetabolicStateSnapshot.snapshot_date <= target_date)
        .order_by(MetabolicStateSnapshot.snapshot_date.desc())
        .limit(1)
    )).scalar_one_or_none()

    # ReadinessScore — most recent
    readiness = (await db.execute(
        select(ReadinessScore)
        .where(ReadinessScore.user_id == user_id,
               ReadinessScore.score_date <= target_date)
        .order_by(ReadinessScore.score_date.desc())
        .limit(1)
    )).scalar_one_or_none()

    # DailyMetrics — today (for training load today)
    today_metrics = (await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.user_id == user_id,
               DailyMetrics.metrics_date == target_date)
        .limit(1)
    )).scalar_one_or_none()

    # UserProfile — for weight and goal
    from app.models.user import UserProfile
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )).scalar_one_or_none()

    # ACWR from metabolic snapshot
    acwr: Optional[float] = None
    if metabolic and metabolic.training_load_7d and metabolic.training_load_28d:
        chronic_weekly = metabolic.training_load_28d / 4.0
        if chronic_weekly > 0:
            acwr = round(metabolic.training_load_7d / chronic_weekly, 3)

    # Training load today from DailyMetrics (if available) or from metabolic snapshot
    training_load_today = getattr(today_metrics, "training_load", None)

    # Glycogen status from metabolic snapshot
    glycogen_status = getattr(metabolic, "glycogen_status", None) or "unknown"

    return {
        "target_date": target_date,
        "training_load_today": training_load_today,
        "readiness_score": getattr(readiness, "overall_readiness", None),
        "fatigue_score": getattr(metabolic, "fatigue_score", None),
        "acwr": acwr,
        "tdee": getattr(metabolic, "estimated_tdee_kcal", None),
        "goal": getattr(profile, "primary_goal", None) if profile else None,
        "weight_kg": (
            getattr(today_metrics, "weight_kg", None)
            or getattr(profile, "current_weight_kg", None)
            if profile else None
        ),
        "glycogen_status": glycogen_status,
        "plateau_risk": bool(getattr(metabolic, "plateau_risk", False)),
        "has_if_protocol": bool(getattr(profile, "intermittent_fasting", False)) if profile else False,
    }


def _plan_to_response(plan: AdaptiveNutritionPlan) -> AdaptiveNutritionPlanResponse:
    """Convert AdaptiveNutritionPlan dataclass to Pydantic response."""
    def _target(t):
        return NutritionTargetResponse(
            value=t.value, unit=t.unit,
            rationale=t.rationale, priority=t.priority,
        )
    return AdaptiveNutritionPlanResponse(
        target_date=plan.target_date.isoformat(),
        day_type=plan.day_type.value,
        glycogen_status=plan.glycogen_status,
        calorie_target=_target(plan.calorie_target),
        protein_target=_target(plan.protein_target),
        carb_target=_target(plan.carb_target),
        fat_target=_target(plan.fat_target),
        fiber_target=_target(plan.fiber_target),
        hydration_target=_target(plan.hydration_target),
        meal_timing_strategy=plan.meal_timing_strategy,
        fasting_compatible=plan.fasting_compatible,
        fasting_rationale=plan.fasting_rationale,
        pre_workout_guidance=plan.pre_workout_guidance,
        post_workout_guidance=plan.post_workout_guidance,
        recovery_nutrition_focus=plan.recovery_nutrition_focus,
        electrolyte_focus=plan.electrolyte_focus,
        supplementation_focus=plan.supplementation_focus,
        confidence=plan.confidence,
        assumptions=plan.assumptions,
        alerts=plan.alerts,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@adaptive_nutrition_router.get(
    "/adaptive-targets",
    response_model=AdaptiveNutritionTargetsResponse,
)
async def get_adaptive_targets(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdaptiveNutritionTargetsResponse:
    """Compact macro targets for the day — quick dashboard card."""
    snap_date = target_date or date.today()
    inputs = await _load_adaptive_inputs(db, current_user.id, snap_date)
    plan = compute_adaptive_plan(**inputs)

    return AdaptiveNutritionTargetsResponse(
        target_date=plan.target_date.isoformat(),
        day_type=plan.day_type.value,
        calorie_target=plan.calorie_target.value,
        protein_g=plan.protein_target.value,
        carb_g=plan.carb_target.value,
        fat_g=plan.fat_target.value,
        hydration_ml=plan.hydration_target.value,
        fasting_compatible=plan.fasting_compatible,
        confidence=plan.confidence,
        alerts=plan.alerts,
    )


@adaptive_nutrition_router.get(
    "/adaptive-plan",
    response_model=AdaptiveNutritionPlanResponse,
)
async def get_adaptive_plan(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdaptiveNutritionPlanResponse:
    """Full adaptive nutrition plan with meal strategies and guidance."""
    snap_date = target_date or date.today()
    cache = get_cache_service()
    cache_key = CacheKeys.adaptive_nutrition(current_user.id, snap_date)

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return AdaptiveNutritionPlanResponse(**cached)

    inputs = await _load_adaptive_inputs(db, current_user.id, snap_date)
    plan = compute_adaptive_plan(**inputs)
    response = _plan_to_response(plan)

    await cache.set(cache_key, response.model_dump(), ttl=TTL.ADAPTIVE_NUTRITION)
    return response


@adaptive_nutrition_router.post(
    "/adaptive-plan/recompute",
    response_model=AdaptiveNutritionPlanResponse,
)
async def recompute_adaptive_plan(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdaptiveNutritionPlanResponse:
    """Force recompute the adaptive plan and invalidate cache."""
    snap_date = target_date or date.today()
    cache = get_cache_service()
    cache_key = CacheKeys.adaptive_nutrition(current_user.id, snap_date)

    # Invalidate cached entry
    await cache.delete(cache_key)

    inputs = await _load_adaptive_inputs(db, current_user.id, snap_date)
    plan = compute_adaptive_plan(**inputs)
    response = _plan_to_response(plan)

    await cache.set(cache_key, response.model_dump(), ttl=TTL.ADAPTIVE_NUTRITION)
    return response
