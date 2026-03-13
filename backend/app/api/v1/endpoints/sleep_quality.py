from datetime import datetime, timezone, timedelta, date as date_type
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.health import SleepSession, HealthSample

sleep_quality_router = APIRouter(prefix="/sleep", tags=["Sleep Quality"])


class SleepStagePoint(BaseModel):
    stage: str   # awake, light, deep, rem
    start_minute: int
    duration_minutes: int


class SleepSubScore(BaseModel):
    name: str
    score: float  # 0-100
    label: str    # poor, fair, good, excellent


class SleepQualityResponse(BaseModel):
    date: str
    overall_score: Optional[float] = None
    overall_label: Optional[str] = None
    duration_minutes: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    resting_hr_during_sleep: Optional[float] = None
    sub_scores: List[SleepSubScore] = []
    hypnogram: List[SleepStagePoint] = []


def _score_label(score: float) -> str:
    if score >= 85:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"


def _duration_score(minutes: Optional[int]) -> float:
    """7-9h = 100, hors plage = decroissant."""
    if not minutes:
        return 0.0
    hours = minutes / 60
    if 7 <= hours <= 9:
        return 100.0
    elif hours < 7:
        return max(0.0, round((hours / 7) * 100, 1))
    else:
        return max(0.0, round(max(0, (11 - hours) / 2) * 100, 1))


def _depth_score(deep_min: Optional[int], rem_min: Optional[int], total_min: Optional[int]) -> float:
    """Deep >= 20% + REM >= 20% of total = 100."""
    if not total_min or total_min == 0:
        return 0.0
    deep_pct = (deep_min or 0) / total_min
    rem_pct = (rem_min or 0) / total_min
    deep_score = min(1.0, deep_pct / 0.20)
    rem_score = min(1.0, rem_pct / 0.20)
    return round((deep_score * 0.5 + rem_score * 0.5) * 100, 1)


def _continuity_score(awake_min: Optional[int], total_min: Optional[int]) -> float:
    """Moins de reveils = mieux. awake < 5% = 100."""
    if not total_min or total_min == 0:
        return 50.0
    awake_pct = (awake_min or 0) / total_min
    if awake_pct <= 0.05:
        return 100.0
    elif awake_pct >= 0.30:
        return 0.0
    else:
        return round((1 - (awake_pct - 0.05) / 0.25) * 100, 1)

def _hr_score(resting_hr: Optional[float]) -> float:
    """Resting HR during sleep: < 50 excellent, > 80 poor."""
    if not resting_hr:
        return 50.0
    if resting_hr <= 50:
        return 100.0
    elif resting_hr >= 80:
        return 0.0
    else:
        return round((1 - (resting_hr - 50) / 30) * 100, 1)


@sleep_quality_router.get("/quality-score", response_model=SleepQualityResponse)
async def get_sleep_quality_score(
    date_str: Optional[str] = Query(None, description="YYYY-MM-DD, default last night"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Score qualite sommeil composite avec hypnogramme."""
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        # Nuit passee = hier soir / ce matin
        today = datetime.now(timezone.utc)
        target_date = (today - timedelta(days=1)).date()

    window_start = datetime(target_date.year, target_date.month, target_date.day, 18, 0, 0, tzinfo=timezone.utc)
    window_end = window_start + timedelta(hours=16)

    result = await db.execute(
        select(SleepSession)
        .where(and_(
            SleepSession.user_id == current_user.id,
            SleepSession.start_at >= window_start,
            SleepSession.start_at < window_end,
        ))
        .order_by(SleepSession.duration_minutes.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session:
        return SleepQualityResponse(date=str(target_date))

    # FC moyenne pendant le sommeil
    hr_result = await db.execute(
        select(HealthSample)
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type == "heart_rate",
            HealthSample.recorded_at >= session.start_at,
            HealthSample.recorded_at <= session.end_at,
        ))
    )
    hr_samples = hr_result.scalars().all()
    hr_vals = [s.value for s in hr_samples]
    resting_hr = round(sum(hr_vals) / len(hr_vals), 1) if hr_vals else None

    # Calculer sub-scores
    dur_score = _duration_score(session.duration_minutes)
    depth_score = _depth_score(session.deep_sleep_minutes, session.rem_sleep_minutes, session.duration_minutes)
    cont_score = _continuity_score(session.awake_minutes, session.duration_minutes)
    hr_s = _hr_score(resting_hr)

    # Score subjectif si disponible
    subj_score = (session.perceived_quality or 3) / 5 * 100 if session.perceived_quality else 50.0

    # Score global pondere
    overall = round(
        dur_score * 0.30 +
        depth_score * 0.25 +
        cont_score * 0.20 +
        hr_s * 0.15 +
        subj_score * 0.10,
        1,
    )

    sub_scores = [
        SleepSubScore(name="duration", score=dur_score, label=_score_label(dur_score)),
        SleepSubScore(name="depth", score=depth_score, label=_score_label(depth_score)),
        SleepSubScore(name="continuity", score=cont_score, label=_score_label(cont_score)),
        SleepSubScore(name="heart_rate", score=hr_s, label=_score_label(hr_s)),
        SleepSubScore(name="subjective", score=subj_score, label=_score_label(subj_score)),
    ]

    # Hypnogramme simplifie (si donnees disponibles)
    hypnogram: List[SleepStagePoint] = []
    total = session.duration_minutes or 0
    if total > 0:
        deep = session.deep_sleep_minutes or 0
        rem = session.rem_sleep_minutes or 0
        awake = session.awake_minutes if hasattr(session, "awake_minutes") and session.awake_minutes else 0
        light = max(0, total - deep - rem - awake)
        cursor = 0
        if awake > 0:
            hypnogram.append(SleepStagePoint(stage="awake", start_minute=cursor, duration_minutes=awake))
            cursor += awake
        if light > 0:
            hypnogram.append(SleepStagePoint(stage="light", start_minute=cursor, duration_minutes=light))
            cursor += light
        if deep > 0:
            hypnogram.append(SleepStagePoint(stage="deep", start_minute=cursor, duration_minutes=deep))
            cursor += deep
        if rem > 0:
            hypnogram.append(SleepStagePoint(stage="rem", start_minute=cursor, duration_minutes=rem))

    return SleepQualityResponse(
        date=str(target_date),
        overall_score=overall,
        overall_label=_score_label(overall),
        duration_minutes=session.duration_minutes,
        deep_sleep_minutes=session.deep_sleep_minutes,
        rem_sleep_minutes=session.rem_sleep_minutes,
        light_sleep_minutes=session.light_sleep_minutes if hasattr(session, "light_sleep_minutes") else None,
        awake_minutes=session.awake_minutes if hasattr(session, "awake_minutes") else None,
        resting_hr_during_sleep=resting_hr,
        sub_scores=sub_scores,
        hypnogram=hypnogram,
    )