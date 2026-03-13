from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.health import HealthSample, SleepSession

heart_rate_router = APIRouter(prefix="/heart-rate", tags=["Heart Rate"])

class HREvent(BaseModel):
    type: str
    value: float
    recorded_at: datetime
    source: Optional[str] = None

class HRAnalyticsResponse(BaseModel):
    date: str
    avg_awake_bpm: Optional[float] = None
    avg_sleep_bpm: Optional[float] = None
    resting_hr_bpm: Optional[float] = None
    max_bpm: Optional[float] = None
    min_bpm: Optional[float] = None
    high_resting_events: List[HREvent] = []
    low_resting_events: List[HREvent] = []
    other_sources: List[HREvent] = []

class HRTimelinePoint(BaseModel):
    hour: int
    avg_bpm: Optional[float] = None
    min_bpm: Optional[float] = None
    max_bpm: Optional[float] = None

class HRTimelineResponse(BaseModel):
    date: str
    points: List[HRTimelinePoint]
    avg_awake_bpm: Optional[float] = None
    avg_sleep_bpm: Optional[float] = None

class HRHistoryEntry(BaseModel):
    measured_at: datetime
    value: float
    sample_type: str

class HRAllDataResponse(BaseModel):
    total: int
    limit: int
    offset: int
    entries: List[HRHistoryEntry]

from sqlalchemy import and_, cast, Integer as SAInteger
from datetime import date as date_type


@heart_rate_router.get("/analytics", response_model=HRAnalyticsResponse)
async def get_hr_analytics(
    date_str: Optional[str] = Query(None, description="YYYY-MM-DD, default today"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyse FC : awake/sleep split, resting HR, events notables."""
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date_type.today()
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Récupérer sessions de sommeil du jour pour déterminer fenêtres sleep/awake
    sleep_result = await db.execute(
        select(SleepSession)
        .where(and_(
            SleepSession.user_id == current_user.id,
            SleepSession.start_at >= day_start - timedelta(hours=12),
            SleepSession.end_at <= day_end + timedelta(hours=12),
        ))
    )
    sleep_sessions = sleep_result.scalars().all()

    # Récupérer tous les samples FC du jour
    hr_result = await db.execute(
        select(HealthSample)
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type.in_(["heart_rate", "resting_heart_rate"]),
            HealthSample.recorded_at >= day_start,
            HealthSample.recorded_at < day_end,
        ))
        .order_by(HealthSample.recorded_at)
    )
    hr_samples = hr_result.scalars().all()

    if not hr_samples:
        return HRAnalyticsResponse(date=str(target_date))

    def is_during_sleep(ts: datetime) -> bool:
        for s in sleep_sessions:
            if s.start_at <= ts <= s.end_at:
                return True
        return False

    awake_vals, sleep_vals, resting_vals = [], [], []
    all_vals = []
    for sample in hr_samples:
        v = sample.value
        all_vals.append(v)
        if sample.sample_type == "resting_heart_rate":
            resting_vals.append(v)
        elif is_during_sleep(sample.recorded_at):
            sleep_vals.append(v)
        else:
            awake_vals.append(v)

    rhr = resting_vals[0] if resting_vals else (min(awake_vals) if awake_vals else None)
    avg_awake = round(sum(awake_vals) / len(awake_vals), 1) if awake_vals else None
    avg_sleep = round(sum(sleep_vals) / len(sleep_vals), 1) if sleep_vals else None

    # Événements notables : resting HR > 100 ou < 40
    high_events = [
        HREvent(type="high_resting", value=s.value, recorded_at=s.recorded_at, source=s.source)
        for s in hr_samples if s.sample_type == "resting_heart_rate" and s.value > 100
    ]
    low_events = [
        HREvent(type="low_resting", value=s.value, recorded_at=s.recorded_at, source=s.source)
        for s in hr_samples if s.sample_type == "resting_heart_rate" and s.value < 40
    ]

    return HRAnalyticsResponse(
        date=str(target_date),
        avg_awake_bpm=avg_awake,
        avg_sleep_bpm=avg_sleep,
        resting_hr_bpm=round(rhr, 1) if rhr else None,
        max_bpm=max(all_vals) if all_vals else None,
        min_bpm=min(all_vals) if all_vals else None,
        high_resting_events=high_events,
        low_resting_events=low_events,
    )

@heart_rate_router.get("/timeline", response_model=HRTimelineResponse)
async def get_hr_timeline(
    date_str: Optional[str] = Query(None, description="YYYY-MM-DD, default today"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Timeline FC horaire + split awake/sleep pour graphique intrajournalier."""
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date_type.today()
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    sleep_result = await db.execute(
        select(SleepSession)
        .where(and_(
            SleepSession.user_id == current_user.id,
            SleepSession.start_at >= day_start - timedelta(hours=12),
            SleepSession.end_at <= day_end + timedelta(hours=12),
        ))
    )
    sleep_sessions = sleep_result.scalars().all()

    hr_result = await db.execute(
        select(HealthSample)
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type == "heart_rate",
            HealthSample.recorded_at >= day_start,
            HealthSample.recorded_at < day_end,
        ))
        .order_by(HealthSample.recorded_at)
    )
    hr_samples = hr_result.scalars().all()

    # Agréger par heure
    hourly: dict = {h: [] for h in range(24)}
    for s in hr_samples:
        hourly[s.recorded_at.hour].append(s.value)

    points = []
    for h in range(24):
        vals = hourly[h]
        if vals:
            points.append(HRTimelinePoint(
                hour=h,
                avg_bpm=round(sum(vals) / len(vals), 1),
                min_bpm=min(vals),
                max_bpm=max(vals),
            ))
        else:
            points.append(HRTimelinePoint(hour=h))

    def is_during_sleep(ts: datetime) -> bool:
        for s in sleep_sessions:
            if s.start_at <= ts <= s.end_at:
                return True
        return False

    awake_vals = [s.value for s in hr_samples if not is_during_sleep(s.recorded_at)]
    sleep_vals = [s.value for s in hr_samples if is_during_sleep(s.recorded_at)]

    return HRTimelineResponse(
        date=str(target_date),
        points=points,
        avg_awake_bpm=round(sum(awake_vals)/len(awake_vals), 1) if awake_vals else None,
        avg_sleep_bpm=round(sum(sleep_vals)/len(sleep_vals), 1) if sleep_vals else None,
    )


@heart_rate_router.get("/all-data", response_model=HRAllDataResponse)
async def get_hr_all_data(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Historique pagine de tous les samples FC."""
    total_result = await db.execute(
        select(sqlfunc.count(HealthSample.id))
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type.in_(["heart_rate", "resting_heart_rate"]),
        ))
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(HealthSample)
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type.in_(["heart_rate", "resting_heart_rate"]),
        ))
        .order_by(HealthSample.recorded_at.desc())
        .limit(limit).offset(offset)
    )
    samples = result.scalars().all()

    return HRAllDataResponse(
        total=total,
        limit=limit,
        offset=offset,
        entries=[HRHistoryEntry(measured_at=s.recorded_at, value=s.value, sample_type=s.sample_type) for s in samples],
    )