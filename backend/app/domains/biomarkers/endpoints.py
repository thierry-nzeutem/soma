"""SOMA LOT 16 (updated LOT 17) — Biomarker API endpoints.

LOT 17 changes:
- Removed _lab_store in-memory dict
- Lab results now persisted to PostgreSQL via LabResultDB
- get_db injected in all endpoints
"""
from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.cache.cache_service import get_cache_service
from app.cache.cache_keys import TTL

from .models import LabResultDB
from .service import (
    compute_biomarker_analysis,
    build_biomarker_summary,
    BiomarkerResult,
    REFERENCE_RANGES,
)
from .schemas import (
    LabResultCreate,
    LabResultResponse,
    BiomarkerDetailedResponse,
    BiomarkerMarkerAnalysis,
    LongevityImpactResponse,
)

logger = logging.getLogger(__name__)
biomarkers_router = APIRouter(prefix="/labs", tags=["biomarkers"])
cache = get_cache_service()


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _get_user_labs(db: AsyncSession, user_id: uuid.UUID) -> list[BiomarkerResult]:
    """Load all LabResultDB rows for a user and convert to BiomarkerResult."""
    result = await db.execute(
        select(LabResultDB)
        .where(LabResultDB.user_id == user_id)
        .order_by(LabResultDB.test_date.desc())
    )
    rows = result.scalars().all()
    return [
        BiomarkerResult(
            marker_name=r.marker_name,
            value=r.value,
            unit=r.unit,
            lab_date=r.test_date,
            source="manual",
            confidence=1.0,
        )
        for r in rows
    ]


# ─── Endpoints ───────────────────────────────────────────────────────────────

@biomarkers_router.post("/result", response_model=LabResultResponse, status_code=201)
async def add_lab_result(
    lab_result: LabResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a single lab result for the current user.

    Supported marker names: vitamin_d, ferritin, crp, testosterone_total, hba1c,
    fasting_glucose, cholesterol_total, hdl, ldl, triglycerides, cortisol,
    homocysteine, magnesium, omega3_index.
    """
    if lab_result.marker_name not in REFERENCE_RANGES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Marqueur '{lab_result.marker_name}' non reconnu. "
                f"Marqueurs supportés : {', '.join(sorted(REFERENCE_RANGES.keys()))}"
            ),
        )

    lab_db = LabResultDB(
        id=uuid.uuid4(),
        user_id=current_user.id,
        marker_name=lab_result.marker_name,
        value=lab_result.value,
        unit=lab_result.unit,
        test_date=lab_result.lab_date,
        notes=None,
    )
    db.add(lab_db)
    await db.commit()
    await db.refresh(lab_db)

    # Invalidate cached analysis so next GET recomputes
    user_id_str = str(current_user.id)
    await cache.delete(f"biomarker_analysis:{user_id_str}")
    logger.info(
        "Lab result added: user=%s marker=%s value=%s",
        user_id_str, lab_result.marker_name, lab_result.value,
    )

    return LabResultResponse(
        id=str(lab_db.id),
        marker_name=lab_db.marker_name,
        value=lab_db.value,
        unit=lab_db.unit,
        lab_date=lab_db.test_date.isoformat(),
        source=lab_result.source,
        confidence=lab_result.confidence,
    )


@biomarkers_router.get("/results", response_model=list[LabResultResponse])
async def get_lab_results(
    marker_name: Optional[str] = Query(default=None, description="Filter by marker name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all stored lab results for the current user, optionally filtered by marker name."""
    query = select(LabResultDB).where(LabResultDB.user_id == current_user.id)
    if marker_name:
        query = query.where(LabResultDB.marker_name == marker_name)
    query = query.order_by(LabResultDB.test_date.desc())

    result = await db.execute(query)
    rows = result.scalars().all()

    return [
        LabResultResponse(
            id=str(r.id),
            marker_name=r.marker_name,
            value=r.value,
            unit=r.unit,
            lab_date=r.test_date.isoformat(),
            source="manual",
            confidence=1.0,
        )
        for r in rows
    ]


@biomarkers_router.get("/analysis", response_model=BiomarkerDetailedResponse)
async def get_biomarker_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute and return a comprehensive biomarker analysis.

    Scores returned:
    - metabolic_health_score: 0-100 (higher = better)
    - inflammation_score: 0-100 (higher = worse)
    - cardiovascular_risk: 0-100 (higher = worse)
    - longevity_modifier: -10 to +10 years (negative = biologically younger)

    Result is cached for 24h. Adding a new lab result invalidates the cache.
    """
    user_id_str = str(current_user.id)
    cache_key = f"biomarker_analysis:{user_id_str}"

    cached = await cache.get(cache_key)
    if cached:
        return BiomarkerDetailedResponse(**cached)

    lab_results = await _get_user_labs(db, current_user.id)
    analysis = compute_biomarker_analysis(lab_results)

    analysis_dict = analysis.to_dict()
    marker_analyses_data = analysis_dict.pop("marker_analyses")

    response = BiomarkerDetailedResponse(
        **analysis_dict,
        marker_analyses=[BiomarkerMarkerAnalysis(**m) for m in marker_analyses_data],
    )

    await cache.set(cache_key, response.model_dump(), ttl=TTL.BIOLOGICAL_AGE)  # 24h
    return response


@biomarkers_router.get("/longevity-impact", response_model=LongevityImpactResponse)
async def get_longevity_impact(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the longevity impact of the current biomarker profile.

    Provides the longevity_modifier (in years) that integrates with the
    Biological Age computation from LOT 11.
    """
    lab_results = await _get_user_labs(db, current_user.id)
    analysis = compute_biomarker_analysis(lab_results)

    key_factors: list[str] = []
    for m in analysis.marker_analyses:
        if m.status == "optimal":
            key_factors.append(f"OK {m.marker_name}: optimal")
        elif m.status in ("deficient", "toxic"):
            key_factors.append(f"ALERTE {m.marker_name}: {m.status}")

    longevity_recs = analysis.priority_actions + analysis.supplementation_recommendations
    seen: set[str] = set()
    unique_recs: list[str] = []
    for r in longevity_recs:
        if r not in seen:
            seen.add(r)
            unique_recs.append(r)

    return LongevityImpactResponse(
        longevity_modifier=analysis.longevity_modifier,
        metabolic_health_score=analysis.metabolic_health_score,
        inflammation_score=analysis.inflammation_score,
        cardiovascular_risk=analysis.cardiovascular_risk,
        key_longevity_factors=key_factors[:6],
        longevity_recommendations=unique_recs[:5],
    )
