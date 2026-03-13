"""
Digital Twin V2 API endpoints.

Routes:
  GET /twin/today            → compute or return cached DigitalTwinState
  GET /twin/history          → list of snapshots (last N days)
  GET /twin/summary          → compact summary for coach/dashboard

Data loading: reads DailyMetrics, MetabolicStateSnapshot, ReadinessScore, VisionSessions.
Cache: 4h (TWIN_TTL) via CacheService.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.metrics import DailyMetrics
from app.models.scores import ReadinessScore, MetabolicStateSnapshot
from app.models.vision_session import VisionSession
from app.models.advanced import DigitalTwinSnapshot

from app.domains.twin.service import (
    compute_digital_twin_state,
    save_digital_twin,
    build_twin_summary,
    DigitalTwinState,
)
from app.domains.twin.schemas import (
    DigitalTwinStateResponse,
    DigitalTwinSummaryResponse,
    DigitalTwinHistoryResponse,
    DigitalTwinHistoryItem,
    TwinComponentResponse,
)
from app.cache.cache_service import get_cache_service
from app.cache.cache_keys import CacheKeys, TTL

twin_router = APIRouter(prefix="/twin", tags=["Digital Twin"])


# ── Data loading helpers ──────────────────────────────────────────────────────

async def _load_twin_inputs(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> dict:
    """Load all data needed for Digital Twin computation."""
    # DailyMetrics — last 7 days
    since = target_date - timedelta(days=6)
    metrics_rows = (await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.user_id == user_id, DailyMetrics.metrics_date >= since)
        .order_by(DailyMetrics.metrics_date.desc())
    )).scalars().all()

    # Today's metrics (most recent)
    today_metrics = metrics_rows[0] if metrics_rows else None

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

    # VisionSessions — last 7 days
    vision_rows = (await db.execute(
        select(VisionSession)
        .where(VisionSession.user_id == user_id, VisionSession.session_date >= since)
        .order_by(VisionSession.session_date.desc())
    )).scalars().all()

    # Aggregate sleep minutes per day from metrics
    sleep_minutes_7d = [
        m.sleep_minutes for m in metrics_rows
        if m.sleep_minutes is not None
    ]

    # Avg carbs (7d)
    carbs_g_avg = (
        mean(m.carbs_g for m in metrics_rows if m.carbs_g is not None)
        if any(m.carbs_g for m in metrics_rows) else None
    )

    # ACWR from metabolic snapshot
    acwr: Optional[float] = None
    if metabolic and metabolic.training_load_7d and metabolic.training_load_28d:
        chronic_weekly = metabolic.training_load_28d / 4.0
        if chronic_weekly > 0:
            acwr = round(metabolic.training_load_7d / chronic_weekly, 3)

    # User profile for weight/goal
    from app.models.user import UserProfile
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )).scalar_one_or_none()

    return {
        "calories_consumed": getattr(today_metrics, "calories_consumed", None),
        "estimated_tdee": getattr(metabolic, "estimated_tdee_kcal", None),
        "carbs_g_avg": carbs_g_avg,
        "protein_g": getattr(today_metrics, "protein_g", None),
        "hydration_ml": getattr(today_metrics, "hydration_ml", None),
        "hydration_target_ml": getattr(today_metrics, "hydration_target_ml", None),
        "training_load_7d": getattr(metabolic, "training_load_7d", None),
        "acwr": acwr,
        "sleep_score_avg": (
            mean(m.sleep_score for m in metrics_rows if m.sleep_score is not None)
            if any(m.sleep_score for m in metrics_rows) else None
        ),
        "sleep_minutes_7d": sleep_minutes_7d or None,
        "hrv_ms": getattr(today_metrics, "hrv_ms", None),
        "resting_hr_bpm": getattr(today_metrics, "resting_heart_rate_bpm", None),
        "readiness_score": getattr(readiness, "overall_readiness", None),
        "weight_kg": getattr(today_metrics, "weight_kg", None) or getattr(profile, "current_weight_kg", None) if profile else None,
        "goal": getattr(profile, "primary_goal", None) if profile else None,
        "has_if_protocol": bool(getattr(profile, "intermittent_fasting", False)) if profile else False,
        "plateau_risk": bool(getattr(metabolic, "plateau_risk", False)),
        "target_date": target_date,
    }


def _state_to_response(state: DigitalTwinState) -> DigitalTwinStateResponse:
    """Convert DigitalTwinState dataclass to Pydantic response schema."""
    def _comp(c):
        return TwinComponentResponse(
            value=c.value, status=c.status, confidence=c.confidence,
            explanation=c.explanation, variables_used=c.variables_used,
        )
    return DigitalTwinStateResponse(
        snapshot_date=state.snapshot_date.isoformat(),
        energy_balance=_comp(state.energy_balance),
        glycogen=_comp(state.glycogen),
        carb_availability=_comp(state.carb_availability),
        protein_status=_comp(state.protein_status),
        hydration=_comp(state.hydration),
        fatigue=_comp(state.fatigue),
        inflammation=_comp(state.inflammation),
        sleep_debt=_comp(state.sleep_debt),
        recovery_capacity=_comp(state.recovery_capacity),
        training_readiness=_comp(state.training_readiness),
        stress_load=_comp(state.stress_load),
        metabolic_flexibility=_comp(state.metabolic_flexibility),
        plateau_risk=state.plateau_risk,
        under_recovery_risk=state.under_recovery_risk,
        overall_status=state.overall_status,
        primary_concern=state.primary_concern,
        global_confidence=state.global_confidence,
        recommendations=state.recommendations,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@twin_router.get("/today", response_model=DigitalTwinStateResponse)
async def get_digital_twin_today(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DigitalTwinStateResponse:
    """
    Return the Digital Twin state for today (or target_date).
    Computed fresh or from cache (4h TTL).
    Persists the result as DigitalTwinSnapshot.
    """
    snap_date = target_date or date.today()
    cache = get_cache_service()
    cache_key = CacheKeys.twin_today(current_user.id, snap_date)

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return DigitalTwinStateResponse(**cached)

    # Load inputs and compute
    inputs = await _load_twin_inputs(db, current_user.id, snap_date)
    state = compute_digital_twin_state(**inputs)

    # Persist snapshot
    try:
        await save_digital_twin(db, current_user.id, state)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to persist DigitalTwin: %s", exc)

    response = _state_to_response(state)

    # Cache the response
    await cache.set(cache_key, response.model_dump(), ttl=TTL.TWIN)

    return response


@twin_router.get("/summary", response_model=DigitalTwinSummaryResponse)
async def get_digital_twin_summary(
    target_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DigitalTwinSummaryResponse:
    """Compact Digital Twin summary for dashboard cards and coach context."""
    snap_date = target_date or date.today()
    inputs = await _load_twin_inputs(db, current_user.id, snap_date)
    state = compute_digital_twin_state(**inputs)

    return DigitalTwinSummaryResponse(
        snapshot_date=snap_date.isoformat(),
        overall_status=state.overall_status,
        training_readiness=state.training_readiness.value,
        fatigue=state.fatigue.value,
        glycogen_status=state.glycogen.status,
        primary_concern=state.primary_concern,
        plateau_risk=state.plateau_risk,
        under_recovery_risk=state.under_recovery_risk,
        global_confidence=state.global_confidence,
        summary_text=build_twin_summary(state),
    )


@twin_router.get("/history", response_model=DigitalTwinHistoryResponse)
async def get_digital_twin_history(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DigitalTwinHistoryResponse:
    """Return list of Digital Twin snapshots for the last N days."""
    since = date.today() - timedelta(days=days)
    rows = (await db.execute(
        select(DigitalTwinSnapshot)
        .where(
            DigitalTwinSnapshot.user_id == current_user.id,
            DigitalTwinSnapshot.snapshot_date >= since,
        )
        .order_by(DigitalTwinSnapshot.snapshot_date.desc())
    )).scalars().all()

    items = [
        DigitalTwinHistoryItem(
            snapshot_date=row.snapshot_date.isoformat(),
            overall_status=row.overall_status or "unknown",
            training_readiness=float(
                (row.components or {}).get("training_readiness", {}).get("value", 0)
            ),
            fatigue=float(
                (row.components or {}).get("fatigue", {}).get("value", 0)
            ),
            global_confidence=float(row.global_confidence or 0),
        )
        for row in rows
    ]

    return DigitalTwinHistoryResponse(
        user_id=str(current_user.id),
        days_requested=days,
        snapshots=items,
        total_count=len(items),
    )
