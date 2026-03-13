from datetime import datetime, timezone, timedelta, date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, and_
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserProfile
from app.models.health import HealthSample
from app.models.metrics import DailyMetrics
from app.services.calculations import calculate_bmr_mifflin

activity_router = APIRouter(prefix="/activity", tags=["Activity"])
PERIOD_DAYS = {"day": 1, "week": 7, "month": 30}

class HourlyStep(BaseModel):
    hour: int
    steps: int

class HRZone(BaseModel):
    label: str
    bpm_min: int
    bpm_max: Optional[int] = None
    minutes: int = 0

class ActivityDayResponse(BaseModel):
    date: str
    steps: int = 0
    steps_goal: int = 10000
    steps_pct: float = 0.0
    distance_km: Optional[float] = None
    active_calories_kcal: Optional[float] = None
    bmr_kcal: Optional[float] = None
    total_calories_kcal: Optional[float] = None
    active_minutes: Optional[int] = None
    avg_hr_bpm: Optional[float] = None
    max_hr_bpm: Optional[float] = None
    resting_hr_bpm: Optional[float] = None
    hourly_steps: List[HourlyStep] = []

class ActivityPeriodPoint(BaseModel):
    date: str
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    active_calories_kcal: Optional[float] = None
    total_calories_kcal: Optional[float] = None

class ActivityPeriodResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    days: int
    total_steps: int = 0
    avg_steps: float = 0.0
    total_distance_km: float = 0.0
    avg_active_calories: float = 0.0
    steps_goal_days: int = 0
    data_points: List[ActivityPeriodPoint] = []

@activity_router.get("/day", response_model=ActivityDayResponse)
async def get_activity_day(
    date_str: Optional[str] = Query(None, alias="date", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now(timezone.utc).date()
    day_start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    profile = (await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))).scalar_one_or_none()
    dm = (await db.execute(
        select(DailyMetrics).where(
            DailyMetrics.user_id == current_user.id,
            DailyMetrics.metrics_date == target,
        )
    )).scalar_one_or_none()
    bmr = None
    if profile and profile.height_cm and profile.age and profile.sex:
        weight_sample = (await db.execute(
            select(HealthSample.value)
            .where(HealthSample.user_id == current_user.id, HealthSample.sample_type == "weight")
            .order_by(HealthSample.recorded_at.desc()).limit(1)
        )).scalar_one_or_none()
        w = weight_sample or 75.0
        bmr = round(calculate_bmr_mifflin(w, profile.height_cm, profile.age, profile.sex), 0)
    steps = dm.steps or 0 if dm else 0
    active_cal = dm.active_calories_kcal if dm else None
    total_cal = round(bmr + (active_cal or 0), 0) if bmr else None
    hr_result = await db.execute(
        select(sqlfunc.avg(HealthSample.value), sqlfunc.max(HealthSample.value))
        .where(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type == "heart_rate",
            HealthSample.recorded_at >= day_start,
            HealthSample.recorded_at < day_end,
        )
    )
    hr_row = hr_result.one_or_none()
    avg_hr = round(hr_row[0], 1) if hr_row and hr_row[0] else None
    max_hr = round(hr_row[1], 0) if hr_row and hr_row[1] else None
    rhr_res = await db.execute(
        select(HealthSample.value)
        .where(HealthSample.user_id == current_user.id, HealthSample.sample_type == "resting_heart_rate")
        .order_by(HealthSample.recorded_at.desc()).limit(1)
    )
    rhr = rhr_res.scalar_one_or_none()
    hourly = []
    hr_samples = await db.execute(
        select(HealthSample)
        .where(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type == "steps",
            HealthSample.recorded_at >= day_start,
            HealthSample.recorded_at < day_end,
        )
        .order_by(HealthSample.recorded_at.asc())
    )
    step_buckets = {}
    for s in hr_samples.scalars().all():
        h = s.recorded_at.hour
        step_buckets[h] = step_buckets.get(h, 0) + int(s.value)
    hourly = [HourlyStep(hour=h, steps=v) for h, v in sorted(step_buckets.items())]
    return ActivityDayResponse(
        date=target.isoformat(), steps=steps, steps_goal=10000,
        steps_pct=round(steps / 10000 * 100, 1),
        distance_km=dm.distance_km if dm else None,
        active_calories_kcal=active_cal, bmr_kcal=bmr,
        total_calories_kcal=total_cal,
        active_minutes=None,
        avg_hr_bpm=avg_hr, max_hr_bpm=max_hr, resting_hr_bpm=rhr,
        hourly_steps=hourly,
    )

@activity_router.get("/period", response_model=ActivityPeriodResponse)
async def get_activity_period(
    period: str = Query("week", pattern="^(week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    days_n = PERIOD_DAYS[period]
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days_n)
    profile = (await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))).scalar_one_or_none()
    result = await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.user_id == current_user.id, DailyMetrics.metrics_date >= since.date())
        .order_by(DailyMetrics.metrics_date.asc())
    )
    rows = result.scalars().all()
    pts = []
    total_steps = 0
    total_dist = 0.0
    total_acal = 0.0
    goal_days = 0
    bmr = None
    if profile and profile.height_cm and profile.age and profile.sex:
        bmr = round(calculate_bmr_mifflin(75, profile.height_cm, profile.age, profile.sex), 0)
    for r in rows:
        s = r.steps or 0
        ac = r.active_calories_kcal or 0
        tc = round((bmr or 0) + ac, 0) if bmr else None
        total_steps += s
        total_dist += r.distance_km or 0
        total_acal += ac
        if s >= 10000: goal_days += 1
        pts.append(ActivityPeriodPoint(
            date=r.metrics_date.isoformat(), steps=s,
            distance_km=r.distance_km, active_calories_kcal=r.active_calories_kcal,
            total_calories_kcal=tc,
        ))
    n = max(len(rows), 1)
    return ActivityPeriodResponse(
        period=period, start_date=since.strftime("%Y-%m-%d"), end_date=now.strftime("%Y-%m-%d"),
        days=len(rows), total_steps=total_steps, avg_steps=round(total_steps / n, 0),
        total_distance_km=round(total_dist, 2), avg_active_calories=round(total_acal / n, 1),
        steps_goal_days=goal_days, data_points=pts,
    )
