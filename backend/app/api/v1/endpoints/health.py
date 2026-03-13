from datetime import datetime, date, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.health import HealthDataSource, HealthImportJob, HealthSample, SleepSession, HydrationLog
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/health", tags=["Health Data"])


class HealthSyncRequest(BaseModel):
    source: str  # apple_health, google_health, garmin
    data: Dict[str, Any]  # données brutes selon format source


class HealthSyncResponse(BaseModel):
    job_id: str
    status: str
    message: str


class HealthSummaryResponse(BaseModel):
    date: str
    steps: Optional[float] = None
    distance_km: Optional[float] = None
    active_calories_kcal: Optional[float] = None
    resting_heart_rate_bpm: Optional[float] = None
    avg_heart_rate_bpm: Optional[float] = None
    hrv_ms: Optional[float] = None
    vo2_max: Optional[float] = None
    spo2_pct: Optional[float] = None
    stand_hours: Optional[float] = None
    body_temperature_c: Optional[float] = None


class SleepLogRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    perceived_quality: Optional[int] = None  # 1-5
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    notes: Optional[str] = None


class HydrationLogRequest(BaseModel):
    volume_ml: int
    logged_at: Optional[datetime] = None
    beverage_type: str = "water"
    notes: Optional[str] = None


class HydrationDaySummary(BaseModel):
    date: str
    total_ml: int
    target_ml: int
    pct: float
    entries: List[dict]
    status: str  # insufficient, adequate, optimal


@router.post("/sync", response_model=HealthSyncResponse, status_code=202)
async def sync_health_data(
    request: HealthSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Démarre un job d'import de données santé en arrière-plan."""
    # Créer ou récupérer la source
    source_result = await db.execute(
        select(HealthDataSource).where(
            and_(HealthDataSource.user_id == current_user.id, HealthDataSource.source_type == request.source)
        )
    )
    source = source_result.scalar_one_or_none()

    if not source:
        source = HealthDataSource(user_id=current_user.id, source_type=request.source, source_name=request.source)
        db.add(source)
        await db.flush()

    # Créer le job
    job = HealthImportJob(
        user_id=current_user.id,
        source_id=source.id,
        job_type="incremental",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Démarrer traitement en background
    background_tasks.add_task(_process_health_sync, str(job.id), request.source, request.data, str(current_user.id))

    return HealthSyncResponse(
        job_id=str(job.id),
        status="pending",
        message="Sync started",
    )


async def _process_health_sync(job_id: str, source: str, data: dict, user_id: str):
    """Process health sync en background — logique simplifiée pour MVP."""
    # TODO: implémenter parseurs spécifiques par source
    # Pour l'instant, on accepte le format générique: {sample_type: [{value, unit, recorded_at}, ...]}
    pass


@router.get("/sync/{job_id}")
async def get_sync_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthImportJob).where(
            and_(HealthImportJob.id == job_id, HealthImportJob.user_id == current_user.id)
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": str(job.id),
        "status": job.status,
        "records_imported": job.records_imported,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error": job.error_message,
    }


@router.post("/samples")
async def add_health_samples(
    samples: List[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ajout manuel ou programmatique de données santé."""
    added = 0
    skipped = 0

    for s in samples:
        try:
            # Parse recorded_at string to datetime
            raw_ts = s["recorded_at"]
            if isinstance(raw_ts, str):
                recorded_at = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            else:
                recorded_at = raw_ts

            sample = HealthSample(
                user_id=current_user.id,
                sample_type=s["sample_type"],
                value=float(s["value"]),
                unit=s["unit"],
                recorded_at=recorded_at,
                source=s.get("source", "manual"),
                data_quality=s.get("data_quality", "exact"),
                external_id=s.get("external_id"),
            )
            db.add(sample)
            added += 1
        except Exception:
            skipped += 1

    await db.commit()
    return {"added": added, "skipped": skipped}


@router.get("/summary", response_model=HealthSummaryResponse)
async def get_health_summary(
    date_str: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Résumé des métriques santé pour une journée."""
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Récupérer toutes les métriques du jour
    result = await db.execute(
        select(HealthSample.sample_type, func.avg(HealthSample.value).label("avg_val"), func.sum(HealthSample.value).label("sum_val"))
        .where(
            and_(
                HealthSample.user_id == current_user.id,
                HealthSample.recorded_at >= day_start,
                HealthSample.recorded_at < day_end,
            )
        )
        .group_by(HealthSample.sample_type)
    )

    metrics = {row.sample_type: {"avg": row.avg_val, "sum": row.sum_val} for row in result}

    return HealthSummaryResponse(
        date=str(target_date),
        steps=metrics.get("steps", {}).get("sum"),
        distance_km=metrics.get("distance", {}).get("sum"),
        active_calories_kcal=metrics.get("active_calories", {}).get("sum"),
        resting_heart_rate_bpm=metrics.get("resting_heart_rate", {}).get("avg"),
        avg_heart_rate_bpm=metrics.get("heart_rate", {}).get("avg"),
        hrv_ms=metrics.get("hrv", {}).get("avg"),
        vo2_max=metrics.get("vo2_max", {}).get("avg"),
        spo2_pct=metrics.get("spo2", {}).get("avg"),
        stand_hours=metrics.get("stand_hours", {}).get("sum"),
        body_temperature_c=metrics.get("body_temperature", {}).get("avg"),
    )


# --- Sleep ---

sleep_router = APIRouter(prefix="/sleep", tags=["Sleep"])


@sleep_router.post("", status_code=201)
async def log_sleep(
    data: SleepLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    duration = int((data.end_at - data.start_at).total_seconds() / 60)
    session = SleepSession(
        user_id=current_user.id,
        start_at=data.start_at,
        end_at=data.end_at,
        duration_minutes=duration,
        deep_sleep_minutes=data.deep_sleep_minutes,
        rem_sleep_minutes=data.rem_sleep_minutes,
        perceived_quality=data.perceived_quality,
        notes=data.notes,
        source="manual",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": str(session.id), "duration_minutes": duration}


@sleep_router.get("")
async def get_sleep_history(
    days: int = 14,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(SleepSession)
        .where(and_(SleepSession.user_id == current_user.id, SleepSession.start_at >= since))
        .order_by(SleepSession.start_at.desc())
    )
    sessions = result.scalars().all()

    data = [
        {
            "id": str(s.id),
            "start_at": s.start_at,
            "end_at": s.end_at,
            "duration_minutes": s.duration_minutes,
            "deep_sleep_minutes": s.deep_sleep_minutes,
            "rem_sleep_minutes": s.rem_sleep_minutes,
            "perceived_quality": s.perceived_quality,
        }
        for s in sessions
    ]
    return {"sessions": data, "count": len(data)}


@sleep_router.get("/analysis")
async def get_sleep_analysis(
    days: int = 14,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyse complete du sommeil : architecture + consistance + problemes."""
    from app.services.sleep_analysis_service import (
        compute_sleep_architecture_score,
        compute_sleep_consistency_score,
        detect_sleep_problems,
        architecture_to_dict,
        consistency_to_dict,
        problem_to_dict,
    )

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(SleepSession)
        .where(and_(SleepSession.user_id == current_user.id, SleepSession.start_at >= since))
        .order_by(SleepSession.start_at.desc())
    )
    sessions = result.scalars().all()

    if not sessions:
        return {"architecture": None, "consistency": None, "problems": []}

    # Architecture — based on most recent session
    latest = sessions[0]
    architecture = compute_sleep_architecture_score(
        duration_minutes=latest.duration_minutes,
        deep_sleep_minutes=latest.deep_sleep_minutes,
        rem_sleep_minutes=latest.rem_sleep_minutes,
        light_sleep_minutes=latest.light_sleep_minutes,
        awake_minutes=latest.awake_minutes,
    )

    # Consistency — based on all sessions
    session_dicts = [
        {
            "start_at": s.start_at,
            "end_at": s.end_at,
            "duration_minutes": s.duration_minutes,
            "perceived_quality": s.perceived_quality,
            "deep_sleep_minutes": s.deep_sleep_minutes,
            "awake_minutes": s.awake_minutes,
        }
        for s in sessions
    ]
    consistency = compute_sleep_consistency_score(session_dicts)

    # Problems — based on all sessions
    problems = detect_sleep_problems(session_dicts)

    return {
        "architecture": architecture_to_dict(architecture),
        "consistency": consistency_to_dict(consistency),
        "problems": [problem_to_dict(p) for p in problems],
    }


# --- Hydration ---

hydration_router = APIRouter(prefix="/hydration", tags=["Hydration"])


@hydration_router.post("/log", status_code=201)
async def log_hydration(
    data: HydrationLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = HydrationLog(
        user_id=current_user.id,
        logged_at=data.logged_at or datetime.now(timezone.utc),
        volume_ml=data.volume_ml,
        beverage_type=data.beverage_type,
        notes=data.notes,
    )
    db.add(log)
    await db.commit()
    return {"volume_ml": data.volume_ml, "message": f"+{data.volume_ml}ml logged"}


@hydration_router.get("/today", response_model=HydrationDaySummary)
async def get_hydration_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import UserProfile
    from app.services.calculations import calculate_hydration_target

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(HydrationLog)
        .where(and_(
            HydrationLog.user_id == current_user.id,
            HydrationLog.logged_at >= today_start,
            HydrationLog.logged_at < today_end,
        ))
        .order_by(HydrationLog.logged_at)
    )
    logs = result.scalars().all()
    total_ml = sum(l.volume_ml for l in logs)

    # Objectif depuis profil
    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = profile_result.scalar_one_or_none()

    # Poids par défaut si profil incomplet
    default_weight = 80.0
    target_ml = int(calculate_hydration_target(default_weight, "moderate")[0])

    if profile and profile.target_hydration_ml:
        target_ml = int(profile.target_hydration_ml)

    pct = round((total_ml / target_ml) * 100, 1) if target_ml > 0 else 0

    if pct >= 100:
        status = "optimal"
    elif pct >= 70:
        status = "adequate"
    else:
        status = "insufficient"

    return HydrationDaySummary(
        date=str(today_start.date()),
        total_ml=total_ml,
        target_ml=target_ml,
        pct=pct,
        entries=[{"id": str(l.id), "volume_ml": l.volume_ml, "beverage_type": l.beverage_type, "logged_at": l.logged_at} for l in logs],
        status=status,
    )
