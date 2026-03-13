"""HRV Analytics – variabilite cardiaque et score de stress."""
from datetime import datetime, timezone, timedelta, date as date_type
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, and_
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.health import HealthSample

hrv_router = APIRouter(prefix="/hrv", tags=["HRV & Stress"])


class HRVDayPoint(BaseModel):
    date: str
    avg_hrv_ms: Optional[float] = None
    min_hrv_ms: Optional[float] = None
    max_hrv_ms: Optional[float] = None
    sample_count: int = 0


class HRVScoreResponse(BaseModel):
    date: str
    hrv_score: Optional[int] = None          # 0-100 normalise
    avg_hrv_ms: Optional[float] = None
    resting_hrv_ms: Optional[float] = None
    trend_7d: Optional[float] = None         # delta % vs moyenne 7 jours
    stress_score: Optional[int] = None       # 0-100 (inverse du score HRV)
    stress_level: str = "unknown"            # low / moderate / high / very_high
    recovery_indicator: str = "unknown"      # optimal / good / fair / poor
    baseline_7d_ms: Optional[float] = None
    history: List[HRVDayPoint] = []
    recommendation: Optional[str] = None


def _hrv_to_score(hrv_ms: float) -> int:
    """Normalise HRV ms en score 0-100. Reference: 20ms=0, 100ms=100."""
    clamped = max(20.0, min(100.0, hrv_ms))
    return round((clamped - 20) / 80 * 100)


def _score_to_stress(hrv_score: int) -> int:
    return 100 - hrv_score


def _stress_label(stress: int) -> str:
    if stress < 25:
        return "low"
    if stress < 50:
        return "moderate"
    if stress < 75:
        return "high"
    return "very_high"


def _recovery_label(hrv_score: int, trend: Optional[float]) -> str:
    if hrv_score >= 75:
        return "optimal"
    if hrv_score >= 55:
        return "good"
    if hrv_score >= 35:
        return "fair"
    return "poor"


def _recommendation(stress_level: str, trend: Optional[float]) -> str:
    if stress_level == "low":
        return "Votre variabilite cardiaque est excellente. Vous pouvez maintenir ou augmenter votre charge d'entrainement."
    if stress_level == "moderate":
        if trend is not None and trend < -10:
            return "Votre HRV est en baisse. Privilegiez une intensite moderee et renforcez votre sommeil."
        return "Votre systeme nerveux est equilibre. Continuez votre routine actuelle."
    if stress_level == "high":
        return "Votre HRV indique un stress physiologique eleve. Reduisez l'intensite et dormez au minimum 8h."
    return "Stress tres eleve detecte. Repos complet recommande. Consultez un medecin si cela persiste plus de 3 jours."


@hrv_router.get("/score", response_model=HRVScoreResponse)
async def get_hrv_score(
    date_str: Optional[str] = Query(None, description="YYYY-MM-DD, defaut aujourd'hui"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Score HRV journalier avec tendance 7 jours et indicateur de stress."""
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date_type.today()
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    window_start = day_start - timedelta(days=7)

    # Samples HRV des 7 derniers jours
    result = await db.execute(
        select(HealthSample)
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type == "hrv",
            HealthSample.recorded_at >= window_start,
            HealthSample.recorded_at < day_end,
        ))
        .order_by(HealthSample.recorded_at.asc())
    )
    samples = result.scalars().all()

    # Agreger par jour
    day_map: dict[str, list[float]] = {}
    for s in samples:
        d = s.recorded_at.date().isoformat()
        day_map.setdefault(d, []).append(s.value)

    history: List[HRVDayPoint] = []
    for d, vals in sorted(day_map.items()):
        history.append(HRVDayPoint(
            date=d,
            avg_hrv_ms=round(sum(vals) / len(vals), 1),
            min_hrv_ms=round(min(vals), 1),
            max_hrv_ms=round(max(vals), 1),
            sample_count=len(vals),
        ))

    # HRV du jour cible
    today_key = target_date.isoformat()
    today_vals = day_map.get(today_key, [])
    avg_today = (sum(today_vals) / len(today_vals)) if today_vals else None
    resting = min(today_vals) if today_vals else None  # min ~ resting HRV

    # Baseline 7j (hors aujourd'hui)
    past_vals = [v for d, vals in day_map.items() for v in vals if d != today_key]
    baseline = (sum(past_vals) / len(past_vals)) if past_vals else None

    # Calculs
    hrv_score = _hrv_to_score(avg_today) if avg_today else None
    stress_score = _score_to_stress(hrv_score) if hrv_score is not None else None
    stress_level = _stress_label(stress_score) if stress_score is not None else "unknown"

    trend_7d: Optional[float] = None
    if avg_today and baseline:
        trend_7d = round((avg_today - baseline) / baseline * 100, 1)

    recovery = _recovery_label(hrv_score or 0, trend_7d) if hrv_score is not None else "unknown"
    recommendation = _recommendation(stress_level, trend_7d)

    return HRVScoreResponse(
        date=today_key,
        hrv_score=hrv_score,
        avg_hrv_ms=round(avg_today, 1) if avg_today else None,
        resting_hrv_ms=round(resting, 1) if resting else None,
        trend_7d=trend_7d,
        stress_score=stress_score,
        stress_level=stress_level,
        recovery_indicator=recovery,
        baseline_7d_ms=round(baseline, 1) if baseline else None,
        history=history,
        recommendation=recommendation,
    )


@hrv_router.get("/history", response_model=List[HRVDayPoint])
async def get_hrv_history(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Historique HRV journalier sur N jours."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(HealthSample)
        .where(and_(
            HealthSample.user_id == current_user.id,
            HealthSample.sample_type == "hrv",
            HealthSample.recorded_at >= since,
        ))
        .order_by(HealthSample.recorded_at.asc())
    )
    samples = result.scalars().all()

    day_map: dict[str, list[float]] = {}
    for s in samples:
        d = s.recorded_at.date().isoformat()
        day_map.setdefault(d, []).append(s.value)

    return [
        HRVDayPoint(
            date=d,
            avg_hrv_ms=round(sum(v) / len(v), 1),
            min_hrv_ms=round(min(v), 1),
            max_hrv_ms=round(max(v), 1),
            sample_count=len(v),
        )
        for d, v in sorted(day_map.items())
    ]
