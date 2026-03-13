"""
Daily Metrics Service SOMA — LOT 3.

Agrège et persiste le snapshot journalier de toutes les métriques santé.
Ce snapshot alimente l'Insight Engine et le Longevity Engine.

Le calcul est déclenché :
  - Manuellement via GET /metrics/daily
  - Après chaque appel au dashboard (optionnel, lazy)
  - Quotidiennement par un scheduler (LOT 4+)
"""
import uuid
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.metrics import DailyMetrics
from app.models.user import UserProfile, BodyMetric
from app.models.health import HealthSample, SleepSession, HydrationLog
from app.models.workout import WorkoutSession
from app.models.nutrition import NutritionEntry
from app.models.scores import ReadinessScore
from app.schemas.metrics import DailyMetricsResponse, DailyMetricsHistoryResponse

logger = logging.getLogger(__name__)

# Nombre de champs clés pour calculer la complétude
KEY_FIELDS = [
    "weight_kg", "calories_consumed", "protein_g",
    "hydration_ml", "steps", "sleep_minutes", "readiness_score",
]
MIN_RECOMPUTE_INTERVAL_H = 2  # recalcul si snapshot > 2h


# ── Helpers DB ─────────────────────────────────────────────────────────────────

def _day_bounds(target_date: date):
    start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


async def _fetch_last_weight(db: AsyncSession, user_id: uuid.UUID, before: datetime) -> Optional[float]:
    res = await db.execute(
        select(BodyMetric.weight_kg)
        .where(and_(
            BodyMetric.user_id == user_id,
            BodyMetric.weight_kg.isnot(None),
            BodyMetric.measured_at < before,
        ))
        .order_by(BodyMetric.measured_at.desc()).limit(1)
    )
    return res.scalar_one_or_none()


async def _fetch_health_sample(
    db: AsyncSession, user_id: uuid.UUID, sample_type: str,
    day_start: datetime, day_end: datetime, agg: str = "avg",
) -> Optional[float]:
    res = await db.execute(
        select(HealthSample.value).where(and_(
            HealthSample.user_id == user_id,
            HealthSample.sample_type == sample_type,
            HealthSample.recorded_at >= day_start,
            HealthSample.recorded_at < day_end,
        ))
    )
    values = [row[0] for row in res if row[0] is not None]
    if not values:
        return None
    if agg == "sum":
        return sum(values)
    if agg == "last":
        return values[-1]
    return sum(values) / len(values)


async def _fetch_sleep(
    db: AsyncSession, user_id: uuid.UUID, today: date
) -> tuple[Optional[int], Optional[float], Optional[str]]:
    """Retourne (duration_minutes, sleep_score, quality_label) de la nuit précédente."""
    yesterday_noon = datetime(today.year, today.month, today.day, tzinfo=timezone.utc) - timedelta(hours=12)
    today_noon = yesterday_noon + timedelta(hours=24)
    res = await db.execute(
        select(SleepSession)
        .where(and_(
            SleepSession.user_id == user_id,
            SleepSession.start_at >= yesterday_noon,
            SleepSession.start_at < today_noon,
        ))
        .order_by(SleepSession.start_at.desc()).limit(1)
    )
    session = res.scalar_one_or_none()
    if not session:
        return None, None, None
    label = "unknown"
    if session.duration_minutes:
        if session.duration_minutes >= 480:
            label = "excellent"
        elif session.duration_minutes >= 420:
            label = "good"
        elif session.duration_minutes >= 360:
            label = "fair"
        else:
            label = "poor"
    return session.duration_minutes, session.sleep_score, label


async def _fetch_hydration(
    db: AsyncSession, user_id: uuid.UUID, day_start: datetime, day_end: datetime
) -> Optional[int]:
    res = await db.execute(
        select(func.sum(HydrationLog.volume_ml))
        .where(and_(
            HydrationLog.user_id == user_id,
            HydrationLog.logged_at >= day_start,
            HydrationLog.logged_at < day_end,
        ))
    )
    val = res.scalar_one_or_none()
    return int(val) if val else None


async def _fetch_workouts(
    db: AsyncSession, user_id: uuid.UUID, day_start: datetime, day_end: datetime
) -> tuple[int, Optional[float], Optional[float]]:
    """Retourne (workout_count, total_tonnage_kg, total_training_load)."""
    res = await db.execute(
        select(WorkoutSession)
        .where(and_(
            WorkoutSession.user_id == user_id,
            WorkoutSession.started_at >= day_start,
            WorkoutSession.started_at < day_end,
            WorkoutSession.is_deleted.is_(False),
        ))
    )
    workouts = res.scalars().all()
    count = len(workouts)
    tonnage = sum(w.total_tonnage_kg or 0 for w in workouts) or None
    load = sum(w.internal_load_score or 0 for w in workouts) or None
    return count, tonnage, load


async def _fetch_nutrition(
    db: AsyncSession, user_id: uuid.UUID, day_start: datetime, day_end: datetime
) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[int]]:
    """Retourne (cal, protein, carbs, fat, fiber, meal_count)."""
    res = await db.execute(
        select(NutritionEntry)
        .where(and_(
            NutritionEntry.user_id == user_id,
            NutritionEntry.logged_at >= day_start,
            NutritionEntry.logged_at < day_end,
            NutritionEntry.is_deleted.is_(False),
        ))
    )
    entries = res.scalars().all()
    if not entries:
        return None, None, None, None, None, None
    cal = sum(e.calories or 0 for e in entries)
    prot = sum(e.protein_g or 0 for e in entries)
    carbs = sum(e.carbs_g or 0 for e in entries)
    fat = sum(e.fat_g or 0 for e in entries)
    fiber = sum(e.fiber_g or 0 for e in entries)
    meal_count = len(set(e.meal_type for e in entries if e.meal_type))
    return (
        round(cal, 1) if cal else None,
        round(prot, 1) if prot else None,
        round(carbs, 1) if carbs else None,
        round(fat, 1) if fat else None,
        round(fiber, 1) if fiber else None,
        meal_count or len(entries),
    )


async def _fetch_readiness(
    db: AsyncSession, user_id: uuid.UUID, target_date: date
) -> Optional[float]:
    res = await db.execute(
        select(ReadinessScore.overall_readiness)
        .where(and_(
            ReadinessScore.user_id == user_id,
            ReadinessScore.score_date == target_date,
        ))
    )
    return res.scalar_one_or_none()


def _compute_completeness(snapshot: DailyMetrics) -> float:
    """Calcule le % de champs clés renseignés."""
    total = len(KEY_FIELDS)
    filled = sum(1 for f in KEY_FIELDS if getattr(snapshot, f, None) is not None)
    return round((filled / total) * 100, 1)


# ── Service principal ──────────────────────────────────────────────────────────

async def get_daily_metrics(
    db: AsyncSession, user_id: uuid.UUID, target_date: date
) -> Optional[DailyMetrics]:
    res = await db.execute(
        select(DailyMetrics).where(and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.metrics_date == target_date,
        ))
    )
    return res.scalar_one_or_none()


async def compute_and_persist_daily_metrics(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
    profile: Optional[UserProfile] = None,
    force_recompute: bool = False,
) -> DailyMetrics:
    """
    Calcule et persiste le snapshot journalier.

    Upsert : si un snapshot récent (< 2h) existe déjà, on le retourne tel quel.
    Sinon, on agrège toutes les sources et on l'upsert.
    """
    existing = await get_daily_metrics(db, user_id, target_date)
    if existing and not force_recompute:
        freshness = datetime.now(timezone.utc) - existing.updated_at.replace(tzinfo=timezone.utc)
        if freshness < timedelta(hours=MIN_RECOMPUTE_INTERVAL_H):
            return existing

    day_start, day_end = _day_bounds(target_date)

    # Collecte de toutes les sources
    weight = await _fetch_last_weight(db, user_id, day_end)
    steps = await _fetch_health_sample(db, user_id, "steps", day_start, day_end, "sum")
    active_cal = await _fetch_health_sample(db, user_id, "active_calories", day_start, day_end, "sum")
    distance = await _fetch_health_sample(db, user_id, "distance", day_start, day_end, "sum")
    rhr = await _fetch_health_sample(db, user_id, "resting_heart_rate", day_start, day_end, "avg")
    hrv = await _fetch_health_sample(db, user_id, "hrv", day_start, day_end, "avg")
    sleep_min, sleep_score, sleep_label = await _fetch_sleep(db, user_id, target_date)
    hydration = await _fetch_hydration(db, user_id, day_start, day_end)
    workout_count, tonnage, training_load = await _fetch_workouts(db, user_id, day_start, day_end)
    cal, prot, carbs, fat, fiber, meal_count = await _fetch_nutrition(db, user_id, day_start, day_end)
    readiness = await _fetch_readiness(db, user_id, target_date)

    # Objectifs du profil
    cal_target = profile.target_calories_kcal if profile else None
    prot_target = profile.target_protein_g if profile else None
    hydration_target = int(profile.target_hydration_ml) if (profile and profile.target_hydration_ml) else 2500

    # Upsert
    if existing:
        snapshot = existing
    else:
        snapshot = DailyMetrics(user_id=user_id, metrics_date=target_date)
        db.add(snapshot)

    snapshot.weight_kg = weight
    snapshot.calories_consumed = cal
    snapshot.protein_g = prot
    snapshot.carbs_g = carbs
    snapshot.fat_g = fat
    snapshot.fiber_g = fiber
    snapshot.calories_target = cal_target
    snapshot.protein_target_g = prot_target
    snapshot.meal_count = meal_count
    snapshot.hydration_ml = hydration
    snapshot.hydration_target_ml = hydration_target
    snapshot.steps = int(steps) if steps else None
    snapshot.active_calories_kcal = active_cal
    snapshot.distance_km = distance
    snapshot.resting_heart_rate_bpm = rhr
    snapshot.hrv_ms = hrv
    snapshot.sleep_minutes = sleep_min
    snapshot.sleep_score = sleep_score
    snapshot.sleep_quality_label = sleep_label
    snapshot.workout_count = workout_count
    snapshot.total_tonnage_kg = tonnage
    snapshot.training_load = training_load
    snapshot.readiness_score = readiness
    snapshot.data_completeness_pct = _compute_completeness(snapshot)
    snapshot.algorithm_version = "v1.0"

    await db.flush()
    await db.refresh(snapshot)
    logger.info("DailyMetrics upsert — user=%s date=%s completeness=%.1f%%",
                user_id, target_date, snapshot.data_completeness_pct)
    return snapshot


async def get_metrics_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 30,
) -> DailyMetricsHistoryResponse:
    """Récupère l'historique des DailyMetrics sur N jours."""
    cutoff = date.today() - timedelta(days=days)
    res = await db.execute(
        select(DailyMetrics)
        .where(and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.metrics_date >= cutoff,
        ))
        .order_by(DailyMetrics.metrics_date.desc())
    )
    records = res.scalars().all()

    history = [DailyMetricsResponse.model_validate(r) for r in records]

    # Tendances
    if not records:
        return DailyMetricsHistoryResponse(
            history=[],
            days_requested=days,
            days_available=0,
        )

    readiness_vals = [r.readiness_score for r in records if r.readiness_score]
    sleep_vals = [r.sleep_minutes for r in records if r.sleep_minutes]
    cal_vals = [r.calories_consumed for r in records if r.calories_consumed]
    step_vals = [r.steps for r in records if r.steps]
    prot_vals = [r.protein_g for r in records if r.protein_g]
    weight_vals = [r.weight_kg for r in records if r.weight_kg]
    workout_days = sum(1 for r in records if r.workout_count > 0)

    def avg(lst): return round(sum(lst) / len(lst), 1) if lst else None

    return DailyMetricsHistoryResponse(
        history=history,
        days_requested=days,
        days_available=len(records),
        date_from=records[-1].metrics_date if records else None,
        date_to=records[0].metrics_date if records else None,
        avg_readiness=avg(readiness_vals),
        avg_sleep_hours=round(avg(sleep_vals) / 60, 2) if avg(sleep_vals) else None,
        avg_calories=avg(cal_vals),
        avg_steps=int(avg(step_vals)) if avg(step_vals) else None,
        avg_protein_g=avg(prot_vals),
        weight_trend_kg=round(weight_vals[0] - weight_vals[-1], 2) if len(weight_vals) >= 2 else None,
        workout_frequency_pct=round((workout_days / max(1, len(records))) * 100, 1),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fallback lazy computation (LOT 4)
# ─────────────────────────────────────────────────────────────────────────────

async def lazy_ensure_today_metrics(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
    profile: Optional[UserProfile] = None,
) -> Optional[DailyMetrics]:
    """
    Fallback LOT 4 : déclenche le calcul si daily_metrics du jour sont absentes.

    Utilisé par les endpoints /health/plan/today et /scores/longevity pour garantir
    que les métriques du jour existent avant de lire les données.

    compute_and_persist_daily_metrics possède son propre cache 2h :
    si les données sont fraîches, ce call est quasi-immédiat (pas de double calcul).

    Retourne None en cas d'échec (log seulement, pas de propagation).
    """
    try:
        return await compute_and_persist_daily_metrics(
            db=db,
            user_id=user_id,
            target_date=target_date,
            profile=profile,
            force_recompute=False,  # Cache 2h — pas de recalcul si données fraîches
        )
    except Exception as exc:
        logger.warning(
            "lazy_ensure_today_metrics failed — will proceed with stale/missing data."
            " user_id=%s date=%s error=%s",
            user_id, target_date, exc,
        )
        return None
