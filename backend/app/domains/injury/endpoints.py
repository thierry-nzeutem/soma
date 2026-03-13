"""SOMA LOT 15 -- Injury Prevention Engine endpoints."""
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
from app.cache.cache_keys import TTL

from .service import compute_injury_prevention_analysis, build_injury_summary
from .schemas import (
    InjuryRiskResponse,
    InjuryHistoryResponse,
    InjuryHistoryItem,
    InjuryRecommendationsResponse,
    RiskZoneResponse,
)

logger = logging.getLogger(__name__)
injury_router = APIRouter(prefix="/injury", tags=["injury"])
cache = get_cache_service()


async def _load_injury_inputs(
    db: AsyncSession,
    user_id,
    days: int = 30,
) -> dict:
    """Load inputs for injury prevention analysis."""
    from app.models.metrics import DailyMetrics
    from app.models.scores import ReadinessScore
    from app.models.workout import WorkoutSession
    from app.models.advanced import MotionIntelligenceSnapshot, DigitalTwinSnapshot

    since = date.today() - timedelta(days=days)
    today = date.today()

    # Latest DailyMetrics (sleep)
    metrics_result = await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.user_id == user_id, DailyMetrics.metrics_date >= since)
        .order_by(DailyMetrics.metrics_date.desc())
        .limit(7)
    )
    metrics_rows = metrics_result.scalars().all()

    sleep_minutes_list = [m.sleep_duration_minutes for m in metrics_rows if m.sleep_duration_minutes]
    avg_sleep = sum(sleep_minutes_list) / len(sleep_minutes_list) if sleep_minutes_list else None

    # Latest Readiness
    readiness_result = await db.execute(
        select(ReadinessScore)
        .where(ReadinessScore.user_id == user_id, ReadinessScore.score_date >= since)
        .order_by(ReadinessScore.score_date.desc())
        .limit(1)
    )
    latest_readiness = readiness_result.scalar_one_or_none()
    readiness_score = latest_readiness.overall_readiness if latest_readiness else None

    # Training loads for last 7 days
    workout_result = await db.execute(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= (today - timedelta(days=7)),
        )
        .order_by(WorkoutSession.session_date)
    )
    workout_rows = workout_result.scalars().all()
    training_loads = [(w.duration_minutes or 45) * 7.0 for w in workout_rows]

    # ACWR approximation
    acwr = None
    if len(training_loads) >= 3:
        acute = sum(training_loads[-7:]) / 7
        chronic = sum(training_loads) / len(training_loads) if training_loads else 1
        if chronic > 0:
            acwr = acute / chronic

    # Latest Motion Intelligence snapshot
    motion_result = await db.execute(
        select(MotionIntelligenceSnapshot)
        .where(MotionIntelligenceSnapshot.user_id == user_id)
        .order_by(MotionIntelligenceSnapshot.snapshot_date.desc())
        .limit(1)
    )
    motion_snap = motion_result.scalar_one_or_none()

    asymmetry_score = motion_snap.asymmetry_score if motion_snap else None
    exercise_profiles = motion_snap.exercise_profiles if motion_snap else None

    # Fatigue from Digital Twin
    twin_result = await db.execute(
        select(DigitalTwinSnapshot)
        .where(DigitalTwinSnapshot.user_id == user_id)
        .order_by(DigitalTwinSnapshot.snapshot_date.desc())
        .limit(1)
    )
    twin_snap = twin_result.scalar_one_or_none()

    fatigue_score = None
    if twin_snap and twin_snap.components:
        fatigue_comp = twin_snap.components.get("fatigue", {})
        fatigue_score = fatigue_comp.get("value") if isinstance(fatigue_comp, dict) else None

    return {
        "acwr": acwr,
        "fatigue_score": fatigue_score,
        "asymmetry_score": asymmetry_score,
        "sleep_minutes_avg": avg_sleep,
        "training_loads_7d": training_loads,
        "exercise_profiles": exercise_profiles,
        "readiness_score": readiness_score,
    }


@injury_router.get("/risk", response_model=InjuryRiskResponse)
async def get_injury_risk(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive injury risk analysis."""
    user_id = str(current_user.id)
    cache_key = "injury_risk:" + user_id

    cached = await cache.get(cache_key)
    if cached:
        return InjuryRiskResponse(**cached)

    inputs = await _load_injury_inputs(db, current_user.id)
    result = compute_injury_prevention_analysis(**inputs)

    response_dict = result.to_dict()
    response = InjuryRiskResponse(**response_dict)

    await cache.set(cache_key, response.model_dump(), ttl=TTL.TWIN)
    return response


@injury_router.get("/history", response_model=InjuryHistoryResponse)
async def get_injury_history(
    days: int = Query(default=30, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get injury risk history (computed from available snapshots)."""
    user_id = str(current_user.id)
    inputs = await _load_injury_inputs(db, current_user.id, days=days)
    result = compute_injury_prevention_analysis(**inputs)

    snapshot = InjuryHistoryItem(
        snapshot_date=date.today().isoformat(),
        injury_risk_score=result.injury_risk_score,
        injury_risk_category=result.injury_risk_category,
        primary_risk_zone=result.risk_zones[0].body_part if result.risk_zones else None,
    )

    return InjuryHistoryResponse(
        user_id=user_id,
        days_requested=days,
        snapshots=[snapshot],
        total_count=1,
    )


@injury_router.get("/recommendations", response_model=InjuryRecommendationsResponse)
async def get_injury_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prioritized injury prevention recommendations."""
    inputs = await _load_injury_inputs(db, current_user.id)
    result = compute_injury_prevention_analysis(**inputs)

    return InjuryRecommendationsResponse(
        injury_risk_score=result.injury_risk_score,
        injury_risk_category=result.injury_risk_category,
        immediate_actions=result.immediate_actions,
        recommendations=result.recommendations,
        risk_zones=[
            RiskZoneResponse(**z.to_dict())
            for z in result.risk_zones
        ],
    )
