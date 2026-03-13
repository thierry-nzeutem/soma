"""
Biological Age Engine — API endpoints.

Routes:
  GET /longevity/biological-age   → full BiologicalAgeResult (cached 24h)
  GET /longevity/history          → list of BiologicalAgeSnapshot (last N days)
  GET /longevity/levers           → sorted actionable levers only

Data loading: reads LongevityScore, MetabolicStateSnapshot, ReadinessScore, UserProfile.
Cache: 24h (BIO_AGE_TTL) via CacheService.
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
from app.models.scores import LongevityScore, MetabolicStateSnapshot, ReadinessScore
from app.models.advanced import BiologicalAgeSnapshot

from app.domains.biological_age.service import (
    compute_biological_age,
    save_biological_age,
    build_bio_age_summary,
    BiologicalAgeResult,
)
from app.domains.biological_age.schemas import (
    BiologicalAgeResponse,
    BiologicalAgeLeversResponse,
    BiologicalAgeHistoryResponse,
    BiologicalAgeHistoryItem,
    BiologicalAgeComponentResponse,
    BiologicalAgeLeverResponse,
)
from app.cache.cache_service import get_cache_service
from app.cache.cache_keys import CacheKeys, TTL

logger = logging.getLogger(__name__)

bio_age_router = APIRouter(prefix="/longevity", tags=["Biological Age"])


# ── Data loading helper ────────────────────────────────────────────────────────

async def _load_bio_age_inputs(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> dict:
    """Load all data needed for Biological Age computation."""

    # LongevityScore — most recent
    longevity = (await db.execute(
        select(LongevityScore)
        .where(LongevityScore.user_id == user_id,
               LongevityScore.score_date <= target_date)
        .order_by(LongevityScore.score_date.desc())
        .limit(1)
    )).scalar_one_or_none()

    # MetabolicStateSnapshot — most recent (for metabolic_age)
    metabolic = (await db.execute(
        select(MetabolicStateSnapshot)
        .where(MetabolicStateSnapshot.user_id == user_id,
               MetabolicStateSnapshot.snapshot_date <= target_date)
        .order_by(MetabolicStateSnapshot.snapshot_date.desc())
        .limit(1)
    )).scalar_one_or_none()

    # ReadinessScore — most recent (for recovery component)
    readiness = (await db.execute(
        select(ReadinessScore)
        .where(ReadinessScore.user_id == user_id,
               ReadinessScore.score_date <= target_date)
        .order_by(ReadinessScore.score_date.desc())
        .limit(1)
    )).scalar_one_or_none()

    # Previous BiologicalAgeSnapshot — for trend computation
    prev_snapshot = (await db.execute(
        select(BiologicalAgeSnapshot)
        .where(BiologicalAgeSnapshot.user_id == user_id,
               BiologicalAgeSnapshot.snapshot_date < target_date)
        .order_by(BiologicalAgeSnapshot.snapshot_date.desc())
        .limit(1)
    )).scalar_one_or_none()

    # UserProfile — for chronological age
    from app.models.user import UserProfile
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )).scalar_one_or_none()

    # Compute chronological age from birth_date or fall back to age field
    chronological_age: int = 30  # default if no data
    if profile:
        if getattr(profile, "birth_date", None):
            birth = profile.birth_date
            chronological_age = (
                target_date.year - birth.year
                - ((target_date.month, target_date.day) < (birth.month, birth.day))
            )
        elif getattr(profile, "age", None):
            chronological_age = int(profile.age)

    return {
        "chronological_age": chronological_age,
        "cardio_score": getattr(longevity, "cardio_score", None),
        "strength_score": getattr(longevity, "strength_score", None),
        "sleep_score": getattr(longevity, "sleep_score", None),
        "weight_score": getattr(longevity, "weight_score", None),
        "body_comp_score": getattr(longevity, "body_comp_score", None),
        "consistency_score": getattr(longevity, "consistency_score", None),
        "metabolic_age": getattr(metabolic, "metabolic_age", None),
        "readiness_score": getattr(readiness, "overall_readiness", None),
        "prev_biological_age": getattr(prev_snapshot, "biological_age", None),
    }


def _result_to_response(result: BiologicalAgeResult) -> BiologicalAgeResponse:
    """Convert BiologicalAgeResult dataclass to Pydantic response schema."""
    return BiologicalAgeResponse(
        chronological_age=result.chronological_age,
        biological_age=result.biological_age,
        biological_age_delta=result.biological_age_delta,
        longevity_risk_score=result.longevity_risk_score,
        trend_direction=result.trend_direction,
        confidence=result.confidence,
        explanation=result.explanation,
        components=[
            BiologicalAgeComponentResponse(
                factor_name=c.factor_name,
                display_name=c.display_name,
                score=c.score,
                weight=c.weight,
                age_delta_years=c.age_delta_years,
                explanation=c.explanation,
                is_available=c.is_available,
            )
            for c in result.components
        ],
        levers=[
            BiologicalAgeLeverResponse(
                lever_id=l.lever_id,
                title=l.title,
                description=l.description,
                potential_years_gained=l.potential_years_gained,
                difficulty=l.difficulty,
                timeframe=l.timeframe,
                component=l.component,
            )
            for l in result.levers
        ],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@bio_age_router.get("/biological-age", response_model=BiologicalAgeResponse)
async def get_biological_age(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BiologicalAgeResponse:
    """
    Return the Biological Age analysis for today (or target_date).
    Cached 24h. Persists result as BiologicalAgeSnapshot.
    """
    snap_date = target_date or date.today()
    cache = get_cache_service()
    cache_key = CacheKeys.biological_age(current_user.id, snap_date)

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return BiologicalAgeResponse(**cached)

    # Load inputs and compute
    inputs = await _load_bio_age_inputs(db, current_user.id, snap_date)
    result = compute_biological_age(**inputs)

    # Persist snapshot
    try:
        await save_biological_age(db, current_user.id, result, snap_date)
    except Exception as exc:
        logger.warning("Failed to persist BiologicalAge: %s", exc)

    response = _result_to_response(result)

    # Cache the response
    await cache.set(cache_key, response.model_dump(), ttl=TTL.BIO_AGE)

    return response


@bio_age_router.get("/history", response_model=BiologicalAgeHistoryResponse)
async def get_biological_age_history(
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BiologicalAgeHistoryResponse:
    """Return list of Biological Age snapshots for the last N days."""
    since = date.today() - timedelta(days=days)
    rows = (await db.execute(
        select(BiologicalAgeSnapshot)
        .where(
            BiologicalAgeSnapshot.user_id == current_user.id,
            BiologicalAgeSnapshot.snapshot_date >= since,
        )
        .order_by(BiologicalAgeSnapshot.snapshot_date.desc())
    )).scalars().all()

    items = [
        BiologicalAgeHistoryItem(
            snapshot_date=row.snapshot_date.isoformat(),
            biological_age=float(row.biological_age or 0),
            biological_age_delta=float(row.biological_age_delta or 0),
            trend_direction=row.trend_direction or "stable",
            confidence=float(row.confidence or 0),
        )
        for row in rows
    ]

    return BiologicalAgeHistoryResponse(
        user_id=str(current_user.id),
        days_requested=days,
        snapshots=items,
        total_count=len(items),
    )


@bio_age_router.get("/levers", response_model=BiologicalAgeLeversResponse)
async def get_biological_age_levers(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BiologicalAgeLeversResponse:
    """
    Return actionable levers sorted by potential years gained.
    Fast path — no cache, computed fresh each time.
    """
    snap_date = target_date or date.today()
    inputs = await _load_bio_age_inputs(db, current_user.id, snap_date)
    result = compute_biological_age(**inputs)

    total_potential = round(
        sum(l.potential_years_gained for l in result.levers), 1
    )

    return BiologicalAgeLeversResponse(
        chronological_age=result.chronological_age,
        biological_age=result.biological_age,
        biological_age_delta=result.biological_age_delta,
        levers=[
            BiologicalAgeLeverResponse(
                lever_id=l.lever_id,
                title=l.title,
                description=l.description,
                potential_years_gained=l.potential_years_gained,
                difficulty=l.difficulty,
                timeframe=l.timeframe,
                component=l.component,
            )
            for l in result.levers
        ],
        total_potential_years=total_potential,
    )
