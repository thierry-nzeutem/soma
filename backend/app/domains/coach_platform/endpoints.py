"""SOMA LOT 14 (updated LOT 17) — Coach Platform endpoints.

LOT 17 changes:
- Removed in-memory dicts (_coach_profiles, _athletes, _links, _programs, _notes)
- All data persisted to PostgreSQL via CoachProfileDB, AthleteProfileDB, etc.
- Added GET /coach-platform/dashboard aggregator endpoint
- get_db injected in all write endpoints
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user

from .models import (
    CoachProfileDB,
    AthleteProfileDB,
    CoachAthleteLinkDB,
    TrainingProgramDB,
    AthleteNoteDB,
)
from .service import (
    compute_athlete_dashboard_summary,
)
from .schemas import (
    CoachProfileCreate,
    CoachProfileResponse,
    AthleteCreate,
    AthleteResponse,
    AthleteDashboardSummaryResponse,
    TrainingProgramCreate,
    TrainingProgramResponse,
    AthleteNoteCreate,
    AthleteNoteResponse,
    CoachAthletesOverviewResponse,
)

logger = logging.getLogger(__name__)
coach_platform_router = APIRouter(prefix="/coach-platform", tags=["coach_platform"])


# ─── DB Helpers ──────────────────────────────────────────────────────────────

async def _get_coach_db(db: AsyncSession, user_id: uuid.UUID) -> Optional[CoachProfileDB]:
    """Find coach profile for a user_id."""
    result = await db.execute(
        select(CoachProfileDB).where(CoachProfileDB.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _get_athletes_for_coach(
    db: AsyncSession,
    coach_id: uuid.UUID,
) -> list[AthleteProfileDB]:
    """Get all active athletes linked to a coach."""
    links_result = await db.execute(
        select(CoachAthleteLinkDB.athlete_id)
        .where(
            CoachAthleteLinkDB.coach_id == coach_id,
            CoachAthleteLinkDB.is_active.is_(True),
        )
    )
    athlete_ids = [r[0] for r in links_result.all()]
    if not athlete_ids:
        return []
    athletes_result = await db.execute(
        select(AthleteProfileDB).where(AthleteProfileDB.id.in_(athlete_ids))
    )
    return list(athletes_result.scalars().all())


async def _build_athletes_overview(
    db: AsyncSession,
    coach_db: CoachProfileDB,
) -> CoachAthletesOverviewResponse:
    """Build the athletes overview used by both /athletes and /dashboard."""
    athletes = await _get_athletes_for_coach(db, coach_db.id)
    summaries = []
    for athlete in athletes:
        metrics = await _load_athlete_metrics(db, str(athlete.user_id))
        injury_risk = None
        acwr = metrics.get("acwr")
        fatigue = metrics.get("fatigue_score")
        if acwr is not None or fatigue is not None:
            try:
                from app.domains.injury.service import compute_injury_prevention_analysis
                injury_result = compute_injury_prevention_analysis(
                    acwr=acwr, fatigue_score=fatigue,
                )
                injury_risk = injury_result.injury_risk_score
            except Exception:
                pass
        summary = compute_athlete_dashboard_summary(
            athlete_id=str(athlete.id),
            athlete_name=athlete.display_name,
            injury_risk_score=injury_risk,
            **metrics,
        )
        summaries.append(AthleteDashboardSummaryResponse(**summary.to_dict()))
    athletes_at_risk = sum(1 for s in summaries if s.risk_level in ("orange", "red"))
    return CoachAthletesOverviewResponse(
        coach_id=str(coach_db.id),
        total_athletes=len(athletes),
        athletes_at_risk=athletes_at_risk,
        athletes_summary=summaries,
    )


async def _load_athlete_metrics(
    db: AsyncSession,
    athlete_user_id: str,
) -> dict:
    """Load all health metrics for an athlete from the DB."""
    from app.models.scores import ReadinessScore
    from app.models.workout import WorkoutSession
    from app.models.advanced import DigitalTwinSnapshot, MotionIntelligenceSnapshot, BiologicalAgeSnapshot
    from app.models.metrics import DailyMetrics

    today = date.today()
    week_ago = today - timedelta(days=7)

    try:
        user_uuid = uuid.UUID(athlete_user_id)
    except (ValueError, AttributeError):
        return {}

    # Readiness
    readiness_result = await db.execute(
        select(ReadinessScore)
        .where(ReadinessScore.user_id == user_uuid)
        .order_by(ReadinessScore.score_date.desc())
        .limit(1)
    )
    readiness_row = readiness_result.scalar_one_or_none()
    readiness_score = readiness_row.overall_readiness if readiness_row else None

    # Digital Twin (fatigue)
    twin_result = await db.execute(
        select(DigitalTwinSnapshot)
        .where(DigitalTwinSnapshot.user_id == user_uuid)
        .order_by(DigitalTwinSnapshot.snapshot_date.desc())
        .limit(1)
    )
    twin_snap = twin_result.scalar_one_or_none()
    fatigue_score = None
    if twin_snap and twin_snap.components:
        fatigue_comp = twin_snap.components.get("fatigue", {})
        fatigue_score = fatigue_comp.get("value") if isinstance(fatigue_comp, dict) else None

    # Motion intelligence
    motion_result = await db.execute(
        select(MotionIntelligenceSnapshot)
        .where(MotionIntelligenceSnapshot.user_id == user_uuid)
        .order_by(MotionIntelligenceSnapshot.snapshot_date.desc())
        .limit(1)
    )
    motion_snap = motion_result.scalar_one_or_none()
    movement_health_score = motion_snap.movement_health_score if motion_snap else None

    # Biological age
    bio_result = await db.execute(
        select(BiologicalAgeSnapshot)
        .where(BiologicalAgeSnapshot.user_id == user_uuid)
        .order_by(BiologicalAgeSnapshot.snapshot_date.desc())
        .limit(1)
    )
    bio_snap = bio_result.scalar_one_or_none()
    bio_age_delta = bio_snap.biological_age_delta if bio_snap else None

    # Recent workouts (ACWR + days since last)
    workout_result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_uuid, WorkoutSession.session_date >= week_ago)
        .order_by(WorkoutSession.session_date.desc())
    )
    workout_rows = workout_result.scalars().all()

    days_since_last = None
    training_load_week = None
    acwr = None

    if workout_rows:
        last_date = max(w.session_date for w in workout_rows)
        days_since_last = (today - last_date).days
        loads = [(w.duration_minutes or 45) * 7.0 for w in workout_rows]
        training_load_week = sum(loads)
        if loads:
            acwr = (sum(loads) / 7) / max(sum(loads) / len(loads), 1)
            acwr = round(min(3.0, max(0.1, acwr)), 2)

    # DailyMetrics (sleep, nutrition compliance)
    metrics_result = await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.user_id == user_uuid)
        .order_by(DailyMetrics.metrics_date.desc())
        .limit(3)
    )
    metrics_rows = metrics_result.scalars().all()

    sleep_quality = None
    nutrition_compliance = None
    if metrics_rows:
        sleep_mins = [m.sleep_duration_minutes for m in metrics_rows if m.sleep_duration_minutes]
        if sleep_mins:
            avg_sleep = sum(sleep_mins) / len(sleep_mins)
            sleep_quality = min(100, (avg_sleep / 480) * 100)
        protein_rows = [(m.protein_g, m.weight_kg) for m in metrics_rows if m.protein_g and m.weight_kg]
        if protein_rows:
            compliances = [min(100, (p / (w * 1.6)) * 100) for p, w in protein_rows]
            nutrition_compliance = sum(compliances) / len(compliances)

    return {
        "readiness_score": readiness_score,
        "fatigue_score": fatigue_score,
        "movement_health_score": movement_health_score,
        "biological_age_delta": bio_age_delta,
        "acwr": acwr,
        "training_load_this_week": training_load_week,
        "days_since_last_session": days_since_last,
        "sleep_quality": sleep_quality,
        "nutrition_compliance": nutrition_compliance,
    }


# ─── Coach Profile Endpoints ────────────────────────────────────────────────

@coach_platform_router.post("/coach/register", response_model=CoachProfileResponse, status_code=201)
async def register_coach(
    coach_data: CoachProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register current user as a coach."""
    existing = await _get_coach_db(db, current_user.id)
    if existing:
        raise HTTPException(status_code=409, detail="Vous êtes déjà enregistré comme coach.")

    coach_db = CoachProfileDB(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=coach_data.name,
        specializations=coach_data.specializations,
        certification=coach_data.certification,
        bio=coach_data.bio,
        max_athletes=coach_data.max_athletes,
        is_active=True,
    )
    db.add(coach_db)
    await db.commit()
    await db.refresh(coach_db)

    return CoachProfileResponse(
        id=str(coach_db.id),
        user_id=str(coach_db.user_id),
        name=coach_db.name,
        specializations=coach_db.specializations or [],
        certification=coach_db.certification,
        bio=coach_db.bio,
        max_athletes=coach_db.max_athletes,
        is_active=coach_db.is_active,
        athlete_count=0,
    )


@coach_platform_router.get("/coach/profile", response_model=CoachProfileResponse)
async def get_coach_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user coach profile."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=404, detail="Profil coach non trouvé. Enregistrez-vous d'abord.")

    athletes = await _get_athletes_for_coach(db, coach_db.id)
    return CoachProfileResponse(
        id=str(coach_db.id),
        user_id=str(coach_db.user_id),
        name=coach_db.name,
        specializations=coach_db.specializations or [],
        certification=coach_db.certification,
        bio=coach_db.bio,
        max_athletes=coach_db.max_athletes,
        is_active=coach_db.is_active,
        athlete_count=len(athletes),
    )


# ─── Athlete Management Endpoints ──────────────────────────────────────────

@coach_platform_router.get("/athletes", response_model=CoachAthletesOverviewResponse)
async def get_coach_athletes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overview of all athletes managed by this coach."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")
    return await _build_athletes_overview(db, coach_db)


@coach_platform_router.get("/dashboard", response_model=CoachAthletesOverviewResponse)
async def get_coach_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Coach dashboard aggregator.

    Returns complete view: coach ID, athlete count, athletes at risk,
    and per-athlete summaries with health metrics.
    Optimised for mobile first-load (single request).
    """
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")
    return await _build_athletes_overview(db, coach_db)


@coach_platform_router.post("/athletes", response_model=AthleteResponse, status_code=201)
async def add_athlete(
    athlete_data: AthleteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an athlete to the coach roster."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")

    try:
        athlete_user_uuid = uuid.UUID(athlete_data.user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="user_id invalide.")

    athlete_db = AthleteProfileDB(
        id=uuid.uuid4(),
        user_id=athlete_user_uuid,
        display_name=athlete_data.display_name,
        sport=athlete_data.sport,
        goal=athlete_data.goal,
        date_of_birth=athlete_data.date_of_birth,
        notes=athlete_data.notes,
        is_active=True,
    )
    db.add(athlete_db)

    link_db = CoachAthleteLinkDB(
        id=uuid.uuid4(),
        coach_id=coach_db.id,
        athlete_id=athlete_db.id,
        is_active=True,
        role="primary",
        linked_at=datetime.now(),
    )
    db.add(link_db)
    await db.commit()
    await db.refresh(athlete_db)

    return AthleteResponse(
        id=str(athlete_db.id),
        user_id=str(athlete_db.user_id),
        display_name=athlete_db.display_name,
        sport=athlete_db.sport,
        goal=athlete_db.goal,
        date_of_birth=athlete_db.date_of_birth.isoformat() if athlete_db.date_of_birth else None,
        notes=athlete_db.notes,
        is_active=athlete_db.is_active,
    )


@coach_platform_router.get("/athlete/{athlete_id}/dashboard", response_model=AthleteDashboardSummaryResponse)
async def get_athlete_dashboard(
    athlete_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed dashboard for a specific athlete."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")

    try:
        athlete_uuid = uuid.UUID(athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    athlete_result = await db.execute(
        select(AthleteProfileDB).where(AthleteProfileDB.id == athlete_uuid)
    )
    athlete_db = athlete_result.scalar_one_or_none()
    if not athlete_db:
        raise HTTPException(status_code=404, detail="Athlète non trouvé.")

    link_result = await db.execute(
        select(CoachAthleteLinkDB).where(
            CoachAthleteLinkDB.coach_id == coach_db.id,
            CoachAthleteLinkDB.athlete_id == athlete_uuid,
            CoachAthleteLinkDB.is_active.is_(True),
        )
    )
    if not link_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Vous n'avez pas accès à cet athlète.")

    metrics = await _load_athlete_metrics(db, str(athlete_db.user_id))
    injury_risk = None
    if metrics.get("acwr") is not None or metrics.get("fatigue_score") is not None:
        try:
            from app.domains.injury.service import compute_injury_prevention_analysis
            injury_result = compute_injury_prevention_analysis(
                acwr=metrics.get("acwr"), fatigue_score=metrics.get("fatigue_score"),
            )
            injury_risk = injury_result.injury_risk_score
        except Exception:
            pass

    summary = compute_athlete_dashboard_summary(
        athlete_id=athlete_id,
        athlete_name=athlete_db.display_name,
        injury_risk_score=injury_risk,
        **metrics,
    )
    return AthleteDashboardSummaryResponse(**summary.to_dict())


# ─── Training Programs ──────────────────────────────────────────────────────

@coach_platform_router.post("/programs", response_model=TrainingProgramResponse, status_code=201)
async def create_training_program(
    program_data: TrainingProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a training program."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")

    weeks_dicts = [w.model_dump() for w in program_data.weeks]

    program_db = TrainingProgramDB(
        id=uuid.uuid4(),
        coach_id=coach_db.id,
        athlete_id=None,
        name=program_data.name,
        description=program_data.description,
        duration_weeks=program_data.duration_weeks,
        sport_focus=program_data.sport_focus,
        difficulty=program_data.difficulty,
        weeks=weeks_dicts,
        is_template=program_data.is_template,
        is_active=True,
    )
    db.add(program_db)
    await db.commit()
    await db.refresh(program_db)

    return TrainingProgramResponse(
        id=str(program_db.id),
        coach_id=str(program_db.coach_id),
        name=program_db.name,
        description=program_db.description,
        duration_weeks=program_db.duration_weeks,
        sport_focus=program_db.sport_focus or "",
        difficulty=program_db.difficulty or "",
        is_template=program_db.is_template,
        weeks=program_db.weeks or [],
    )


@coach_platform_router.get("/programs", response_model=list[TrainingProgramResponse])
async def get_coach_programs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all training programs created by this coach."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")

    result = await db.execute(
        select(TrainingProgramDB).where(TrainingProgramDB.coach_id == coach_db.id)
    )
    programs = result.scalars().all()

    return [
        TrainingProgramResponse(
            id=str(p.id),
            coach_id=str(p.coach_id),
            name=p.name,
            description=p.description,
            duration_weeks=p.duration_weeks,
            sport_focus=p.sport_focus or "",
            difficulty=p.difficulty or "",
            is_template=p.is_template,
            weeks=p.weeks or [],
        )
        for p in programs
    ]


# ─── Athlete Notes ──────────────────────────────────────────────────────────

@coach_platform_router.post("/notes", response_model=AthleteNoteResponse, status_code=201)
async def add_athlete_note(
    note_data: AthleteNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a note for an athlete."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")

    try:
        athlete_uuid = uuid.UUID(note_data.athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    note_db = AthleteNoteDB(
        id=uuid.uuid4(),
        coach_id=coach_db.id,
        athlete_id=athlete_uuid,
        note_date=date.today(),
        content=note_data.content,
        category=note_data.category,
        is_private=note_data.is_private,
    )
    db.add(note_db)
    await db.commit()
    await db.refresh(note_db)

    return AthleteNoteResponse(
        id=str(note_db.id),
        coach_id=str(note_db.coach_id),
        athlete_id=str(note_db.athlete_id),
        note_date=note_db.note_date.isoformat(),
        content=note_db.content,
        category=note_db.category,
        is_private=note_db.is_private,
    )


@coach_platform_router.get("/athlete/{athlete_id}/notes", response_model=list[AthleteNoteResponse])
async def get_athlete_notes(
    athlete_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all notes for an athlete (from the requesting coach)."""
    coach_db = await _get_coach_db(db, current_user.id)
    if not coach_db:
        raise HTTPException(status_code=403, detail="Accès coach requis.")

    try:
        athlete_uuid = uuid.UUID(athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    result = await db.execute(
        select(AthleteNoteDB).where(
            AthleteNoteDB.coach_id == coach_db.id,
            AthleteNoteDB.athlete_id == athlete_uuid,
        ).order_by(AthleteNoteDB.note_date.desc())
    )
    notes = result.scalars().all()

    return [
        AthleteNoteResponse(
            id=str(n.id),
            coach_id=str(n.coach_id),
            athlete_id=str(n.athlete_id),
            note_date=n.note_date.isoformat(),
            content=n.content,
            category=n.category,
            is_private=n.is_private,
        )
        for n in notes
    ]
