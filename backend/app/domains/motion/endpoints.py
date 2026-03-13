"""
Motion Intelligence Engine — API endpoints.

Routes:
  GET /vision/motion-summary    → full MotionIntelligenceResult (cached 6h)
  GET /vision/motion-history    → list of MotionIntelligenceSnapshot (last N days)
  GET /vision/asymmetry-risk    → asymmetry score only (fast path, no cache)

Data loading: reads VisionSessions for the last N days.
Cache: 6h (MOTION_TTL) via CacheService.
"""
from __future__ import annotations

import uuid
import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.vision_session import VisionSession
from app.models.advanced import MotionIntelligenceSnapshot

from app.domains.motion.service import (
    compute_motion_intelligence,
    save_motion_intelligence,
    build_motion_summary,
    SessionData,
    MotionIntelligenceResult,
)
from app.domains.motion.schemas import (
    MotionIntelligenceResponse,
    AsymmetryRiskResponse,
    MotionHistoryResponse,
    MotionHistoryItem,
    ExerciseMotionProfileResponse,
)
from app.cache.cache_service import get_cache_service
from app.cache.cache_keys import CacheKeys, TTL

logger = logging.getLogger(__name__)

motion_router = APIRouter(prefix="/vision", tags=["Motion Intelligence"])


# ── Data loading helper ────────────────────────────────────────────────────────

async def _load_vision_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    since: date,
) -> list[SessionData]:
    """Load VisionSessions and convert to SessionData DTOs."""
    rows = (await db.execute(
        select(VisionSession)
        .where(
            VisionSession.user_id == user_id,
            VisionSession.session_date >= since,
        )
        .order_by(VisionSession.session_date.asc())
    )).scalars().all()

    return [
        SessionData(
            exercise_type=row.exercise_type,
            session_date=row.session_date,
            stability_score=row.stability_score,
            amplitude_score=row.amplitude_score,
            quality_score=row.quality_score,
            rep_count=row.rep_count or 0,
        )
        for row in rows
    ]


def _result_to_response(result: MotionIntelligenceResult) -> MotionIntelligenceResponse:
    """Convert MotionIntelligenceResult dataclass to Pydantic response."""
    return MotionIntelligenceResponse(
        analysis_date=result.analysis_date.isoformat(),
        sessions_analyzed=result.sessions_analyzed,
        days_analyzed=result.days_analyzed,
        movement_health_score=result.movement_health_score,
        stability_score=result.stability_score,
        mobility_score=result.mobility_score,
        asymmetry_score=result.asymmetry_score,
        overall_quality_trend=result.overall_quality_trend,
        consecutive_quality_sessions=result.consecutive_quality_sessions,
        exercise_profiles={
            ex: ExerciseMotionProfileResponse(
                exercise_type=p.exercise_type,
                sessions_analyzed=p.sessions_analyzed,
                avg_stability=p.avg_stability,
                avg_amplitude=p.avg_amplitude,
                avg_quality=p.avg_quality,
                stability_trend=p.stability_trend,
                amplitude_trend=p.amplitude_trend,
                quality_trend=p.quality_trend,
                quality_variance=p.quality_variance,
                last_session_date=p.last_session_date.isoformat() if p.last_session_date else None,
                alerts=p.alerts,
            )
            for ex, p in result.exercise_profiles.items()
        },
        recommendations=result.recommendations,
        risk_alerts=result.risk_alerts,
        confidence=result.confidence,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@motion_router.get("/motion-summary", response_model=MotionIntelligenceResponse)
async def get_motion_summary(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MotionIntelligenceResponse:
    """
    Full motion intelligence analysis for the last N days.
    Cached 6h. Persists result as MotionIntelligenceSnapshot.
    """
    today = date.today()
    cache = get_cache_service()
    cache_key = CacheKeys.motion_summary(current_user.id, today)

    # Try cache first (ignores `days` param for cache key simplicity — 30d default)
    cached = await cache.get(cache_key)
    if cached:
        return MotionIntelligenceResponse(**cached)

    since = today - timedelta(days=days)
    sessions = await _load_vision_sessions(db, current_user.id, since)
    result = compute_motion_intelligence(sessions, analysis_date=today, days_analyzed=days)

    # Persist snapshot
    try:
        await save_motion_intelligence(db, current_user.id, result)
    except Exception as exc:
        logger.warning("Failed to persist MotionIntelligence: %s", exc)

    response = _result_to_response(result)
    await cache.set(cache_key, response.model_dump(), ttl=TTL.MOTION)
    return response


@motion_router.get("/motion-history", response_model=MotionHistoryResponse)
async def get_motion_history(
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MotionHistoryResponse:
    """Return list of Motion Intelligence snapshots for the last N days."""
    since = date.today() - timedelta(days=days)
    rows = (await db.execute(
        select(MotionIntelligenceSnapshot)
        .where(
            MotionIntelligenceSnapshot.user_id == current_user.id,
            MotionIntelligenceSnapshot.snapshot_date >= since,
        )
        .order_by(MotionIntelligenceSnapshot.snapshot_date.desc())
    )).scalars().all()

    items = [
        MotionHistoryItem(
            snapshot_date=row.snapshot_date.isoformat(),
            movement_health_score=float(row.movement_health_score or 0),
            stability_score=float(row.stability_score or 0),
            mobility_score=float(row.mobility_score or 0),
            asymmetry_score=float(row.asymmetry_score or 0),
            overall_quality_trend=row.overall_quality_trend or "stable",
            confidence=float(row.confidence or 0),
        )
        for row in rows
    ]

    return MotionHistoryResponse(
        user_id=str(current_user.id),
        days_requested=days,
        snapshots=items,
        total_count=len(items),
    )


@motion_router.get("/asymmetry-risk", response_model=AsymmetryRiskResponse)
async def get_asymmetry_risk(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AsymmetryRiskResponse:
    """
    Fast-path asymmetry risk assessment — computes only asymmetry score.
    No cache, no persistence (lightweight).
    """
    today = date.today()
    since = today - timedelta(days=days)
    sessions = await _load_vision_sessions(db, current_user.id, since)
    result = compute_motion_intelligence(sessions, analysis_date=today, days_analyzed=days)

    # Classify risk level
    asym = result.asymmetry_score
    if asym < 15:
        risk_level = "low"
    elif asym < 35:
        risk_level = "moderate"
    else:
        risk_level = "high"

    return AsymmetryRiskResponse(
        analysis_date=today.isoformat(),
        asymmetry_score=asym,
        risk_level=risk_level,
        sessions_analyzed=result.sessions_analyzed,
        confidence=result.confidence,
        alerts=result.risk_alerts,
    )
