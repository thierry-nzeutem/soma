"""
SOMA — Scheduler Service (LOT 4 → LOT 11).

Pipeline quotidien autonome déclenché à 5h30 heure de Paris.
Calcule et persiste les métriques de santé pour tous les utilisateurs actifs.

Architecture :
  - APScheduler AsyncIOScheduler (in-process, async-native)
  - Pas de service externe requis (Celery optionnel pour multi-instance)
  - Chaque étape est isolée : une erreur ne bloque pas les étapes suivantes

Pipeline quotidien (par utilisateur) :
  1. compute_daily_metrics    — agrège toutes les sources du jour
  2. compute_readiness         — score de récupération matinal
  3. run_insights              — détection de patterns sur 7 jours
  4. generate_health_plan      — morning briefing (log seulement)
  5. compute_longevity         — score longévité sur 30j (log seulement)
  6. digital_twin              — LOT 11 : jumeau numérique V2 (persisté)
  7. biological_age            — LOT 11 : âge biologique (persisté)
  8. motion_intelligence       — LOT 11 : analyse biomécanique (persistée)
  9. adaptive_nutrition_log    — LOT 11 : plan nutritionnel adaptatif (log seulement)
"""
import uuid
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional, Tuple, Any, Coroutine

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user import User, UserProfile, BodyMetric
from app.models.metrics import DailyMetrics
from app.models.scores import ReadinessScore
from app.models.workout import WorkoutSession

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires internes
# ─────────────────────────────────────────────────────────────────────────────

async def _run_step(
    name: str,
    coro: Coroutine[Any, Any, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Exécute une coroutine en isolant les exceptions.

    Retourne :
        (True, None)          si succès
        (False, message)      si exception (loggée mais non propagée)
    """
    try:
        await coro
        logger.info(f"Pipeline step OK", step=name)
        return True, None
    except Exception as exc:
        msg = str(exc)
        logger.error(
            "Pipeline step FAILED",
            step=name,
            error=msg,
            exc_info=True,
        )
        return False, msg


async def _fetch_profile(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[UserProfile]:
    """Récupère le profil utilisateur."""
    res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    return res.scalar_one_or_none()


async def _fetch_readiness(
    db: AsyncSession, user_id: uuid.UUID, target_date: date
) -> Optional[ReadinessScore]:
    """Récupère le ReadinessScore du jour (si déjà calculé)."""
    res = await db.execute(
        select(ReadinessScore).where(and_(
            ReadinessScore.user_id == user_id,
            ReadinessScore.score_date == target_date,
        ))
    )
    return res.scalar_one_or_none()


async def _fetch_daily_metrics(
    db: AsyncSession, user_id: uuid.UUID, target_date: date
) -> Optional[DailyMetrics]:
    """Récupère le snapshot DailyMetrics du jour (si déjà calculé)."""
    res = await db.execute(
        select(DailyMetrics).where(and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.metrics_date == target_date,
        ))
    )
    return res.scalar_one_or_none()


# ─────────────────────────────────────────────────────────────────────────────
# Étapes du pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def _step1_daily_metrics(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
    profile: Optional[UserProfile],
) -> Optional[DailyMetrics]:
    """
    Étape 1 : Calcule et persiste le snapshot DailyMetrics du jour.
    force_recompute=True pour obtenir des données fraîches à 5h30.
    """
    from app.services.daily_metrics_service import compute_and_persist_daily_metrics
    dm = await compute_and_persist_daily_metrics(
        db=db,
        user_id=user_id,
        target_date=target_date,
        profile=profile,
        force_recompute=True,
    )
    logger.info(
        "Daily metrics computed",
        user_id=str(user_id),
        date=str(target_date),
        completeness=dm.data_completeness_pct if dm else None,
    )
    return dm


async def _step2_readiness(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
    daily_metrics: Optional[DailyMetrics],
) -> Optional[ReadinessScore]:
    """
    Étape 2 : Calcule et persiste le score de récupération matinal.

    Utilise build_sleep_summary depuis dashboard_service (réutilisation).
    Extrait HRV, FC repos et charge depuis les DailyMetrics de l'étape 1.
    """
    from app.services.dashboard_service import build_sleep_summary
    from app.services.readiness_service import compute_and_persist_readiness

    # SleepSummary depuis la session sommeil de la nuit précédente
    sleep = await build_sleep_summary(db, user_id, target_date)

    # HRV, FC repos et charge depuis le snapshot du jour (ou None si step 1 a échoué)
    hrv_ms: Optional[float] = daily_metrics.hrv_ms if daily_metrics else None
    resting_hr: Optional[float] = (
        daily_metrics.resting_heart_rate_bpm if daily_metrics else None
    )
    last_workout_load: Optional[float] = (
        daily_metrics.training_load if daily_metrics else None
    )

    readiness = await compute_and_persist_readiness(
        db=db,
        user_id=user_id,
        score_date=target_date,
        sleep=sleep,
        hrv_ms=hrv_ms,
        resting_hr=resting_hr,
        last_workout_load=last_workout_load,
        force_recompute=True,
    )
    logger.info(
        "Readiness computed",
        user_id=str(user_id),
        score=readiness.overall_readiness if readiness else None,
        intensity=readiness.recommended_intensity if readiness else None,
    )
    return readiness


async def _step3_insights(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> int:
    """
    Étape 3 : Détecte et persiste les insights sur la fenêtre 7 jours.
    Retourne le nombre d'insights générés.
    """
    from app.services.insight_service import run_and_persist_insights
    insights = await run_and_persist_insights(db, user_id, target_date)
    count = len(insights)
    critical = sum(1 for i in insights if i.severity == "critical")
    logger.info(
        "Insights generated",
        user_id=str(user_id),
        total=count,
        critical=critical,
    )
    return count


async def _step4_health_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
    profile: Optional[UserProfile],
) -> str:
    """
    Étape 4 : Génère le plan santé journalier (morning briefing).
    Pas de persistance — log seulement. Disponible on-demand via GET /health/plan/today.
    """
    from app.services.nutrition_engine import compute_nutrition_targets
    from app.services.health_plan_service import generate_daily_health_plan

    # Score de récupération (vient d'être calculé à step 2)
    readiness = await _fetch_readiness(db, user_id, target_date)
    readiness_score = readiness.overall_readiness if readiness else None
    recommended_intensity = (
        (readiness.recommended_intensity if readiness else None) or "moderate"
    )

    # DailyMetrics (viennent d'être calculées à step 1)
    metrics = await _fetch_daily_metrics(db, user_id, target_date)
    hydration_pct: Optional[float] = None
    sleep_quality_label: Optional[str] = None
    protein_pct: Optional[float] = None
    calorie_pct: Optional[float] = None
    has_workout_today = False

    if metrics:
        if metrics.hydration_ml and metrics.hydration_target_ml and metrics.hydration_target_ml > 0:
            hydration_pct = metrics.hydration_ml / metrics.hydration_target_ml
        sleep_quality_label = metrics.sleep_quality_label
        if metrics.protein_g and metrics.protein_target_g and metrics.protein_target_g > 0:
            protein_pct = metrics.protein_g / metrics.protein_target_g
        if metrics.calories_consumed and metrics.calories_target and metrics.calories_target > 0:
            calorie_pct = metrics.calories_consumed / metrics.calories_target
        has_workout_today = (metrics.workout_count or 0) > 0

    # Heure de réveil habituelle
    usual_wake_str: Optional[str] = None
    if profile and profile.usual_wake_time:
        try:
            usual_wake_str = str(profile.usual_wake_time)[:5]
        except Exception:
            pass

    # Cibles nutritionnelles
    nutrition_targets = compute_nutrition_targets(
        age=profile.age if profile else None,
        sex=profile.sex if profile else None,
        height_cm=profile.height_cm if profile else None,
        weight_kg=None,
        body_fat_pct=None,
        activity_level=profile.activity_level if profile else None,
        fitness_level=profile.fitness_level if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        dietary_regime=profile.dietary_regime if profile else None,
        intermittent_fasting=profile.intermittent_fasting if profile else False,
        fasting_protocol=profile.fasting_protocol if profile else None,
        usual_wake_time=usual_wake_str,
        workout_type=None,
        workout_duration_minutes=None,
    )

    plan = generate_daily_health_plan(
        target_date_str=target_date.isoformat(),
        readiness_score=readiness_score,
        recommended_intensity=recommended_intensity,
        nutrition_targets=nutrition_targets,
        primary_goal=profile.primary_goal if profile else None,
        fitness_level=profile.fitness_level if profile else None,
        home_equipment=profile.home_equipment if profile else None,
        gym_access=profile.gym_access if profile else False,
        intermittent_fasting=profile.intermittent_fasting if profile else False,
        fasting_protocol=profile.fasting_protocol if profile else None,
        usual_wake_time=usual_wake_str,
        has_workout_today=has_workout_today,
        hydration_pct=hydration_pct,
        sleep_quality_label=sleep_quality_label,
        protein_pct=protein_pct,
        calorie_pct=calorie_pct,
    )

    summary = (
        f"readiness={plan.readiness_level}, "
        f"intensity={plan.recommended_intensity}, "
        f"workout={plan.workout_recommendation.get('type') if plan.workout_recommendation else 'N/A'}, "
        f"tips={len(plan.daily_tips)}"
    )
    logger.info("Health plan generated", user_id=str(user_id), summary=summary)
    return summary


async def _step5_longevity(
    db: AsyncSession,
    user_id: uuid.UUID,
    profile: Optional[UserProfile],
) -> Optional[float]:
    """
    Étape 5 : Calcule le score de longévité sur 30 jours.
    Pas de persistance — log seulement. Disponible on-demand via GET /scores/longevity.
    """
    from app.services.longevity_engine import compute_longevity_score
    from app.services.daily_metrics_service import get_metrics_history

    history = await get_metrics_history(db, user_id, days=30)
    records = history.history

    if not records:
        result = compute_longevity_score(
            actual_age=profile.age if profile else None,
        )
    else:
        avg_steps = history.avg_steps
        avg_sleep_h = history.avg_sleep_hours
        weight_trend = history.weight_trend_kg
        workout_freq_pct = history.workout_frequency_pct

        hrv_vals = [r.hrv_ms for r in records if r.hrv_ms is not None]
        avg_hrv = sum(hrv_vals) / len(hrv_vals) if hrv_vals else None

        active_cal_vals = [r.active_calories_kcal for r in records if r.active_calories_kcal is not None]
        avg_active_cal = sum(active_cal_vals) / len(active_cal_vals) if active_cal_vals else None

        tonnage_vals = [r.total_tonnage_kg for r in records if r.total_tonnage_kg is not None]
        avg_tonnage = sum(tonnage_vals) / len(tonnage_vals) if tonnage_vals else None
        total_workouts = sum(r.workout_count for r in records)

        sleep_q_vals = [r.sleep_score for r in records if r.sleep_score is not None]
        avg_sleep_quality = sum(sleep_q_vals) / len(sleep_q_vals) if sleep_q_vals else None

        cal_records = [
            r for r in records
            if r.calories_consumed is not None and r.calories_target and r.calories_target > 0
        ]
        avg_cal_pct = (
            sum(r.calories_consumed / r.calories_target for r in cal_records) / len(cal_records)
            if cal_records else None
        )

        prot_records = [
            r for r in records
            if r.protein_g is not None and r.protein_target_g and r.protein_target_g > 0
        ]
        avg_prot_pct = (
            sum(r.protein_g / r.protein_target_g for r in prot_records) / len(prot_records)
            if prot_records else None
        )

        meal_tracking_days = sum(1 for r in records if (r.meal_count or 0) > 0)
        meal_tracking_pct = (meal_tracking_days / max(1, len(records))) * 100
        tracking_pct = (history.days_available / max(1, 30)) * 100

        # Composition corporelle depuis dernière mesure
        bm_res = await db.execute(
            select(BodyMetric.body_fat_pct)
            .where(and_(
                BodyMetric.user_id == user_id,
                BodyMetric.body_fat_pct.isnot(None),
            ))
            .order_by(BodyMetric.measured_at.desc())
            .limit(1)
        )
        body_fat_pct = bm_res.scalar_one_or_none()

        result = compute_longevity_score(
            actual_age=profile.age if profile else None,
            avg_steps=float(avg_steps) if avg_steps else None,
            avg_hrv_ms=avg_hrv,
            avg_active_calories=avg_active_cal,
            workout_frequency_pct=workout_freq_pct,
            avg_tonnage_per_session=avg_tonnage,
            workout_count_30d=total_workouts,
            avg_sleep_hours=avg_sleep_h,
            avg_sleep_quality_score=avg_sleep_quality,
            avg_calories_pct_target=avg_cal_pct,
            avg_protein_pct_target=avg_prot_pct,
            meal_tracking_pct=meal_tracking_pct,
            bmi=profile.bmi if profile else None,
            weight_trend_kg_30d=weight_trend,
            goal=profile.primary_goal if profile else None,
            body_fat_pct=body_fat_pct,
            sex=profile.sex if profile else None,
            tracking_days_pct=tracking_pct,
        )

    logger.info(
        "Longevity score computed",
        user_id=str(user_id),
        score=result.longevity_score,
        biological_age=result.biological_age_estimate,
        confidence=result.confidence,
    )
    return result.longevity_score


# ─────────────────────────────────────────────────────────────────────────────
# LOT 11 Pipeline steps (6-9)
# ─────────────────────────────────────────────────────────────────────────────

async def _step6_digital_twin(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> None:
    """
    Étape 6 (LOT 11) : Calcule et persiste le Jumeau Numérique V2.
    """
    from app.domains.twin.endpoints import _load_twin_inputs
    from app.domains.twin.service import compute_digital_twin_state, save_digital_twin

    inputs = await _load_twin_inputs(db, user_id, target_date)
    state = compute_digital_twin_state(**inputs)
    await save_digital_twin(db, user_id, state)

    logger.info(
        "Digital Twin computed",
        user_id=str(user_id),
        overall_status=state.overall_status,
        confidence=state.global_confidence,
    )


async def _step7_biological_age(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> None:
    """
    Étape 7 (LOT 11) : Calcule et persiste l'âge biologique.
    """
    from app.domains.biological_age.endpoints import _load_bio_age_inputs
    from app.domains.biological_age.service import compute_biological_age, save_biological_age

    inputs = await _load_bio_age_inputs(db, user_id, target_date)
    result = compute_biological_age(**inputs)
    await save_biological_age(db, user_id, result, target_date)

    logger.info(
        "Biological Age computed",
        user_id=str(user_id),
        biological_age=result.biological_age,
        delta=result.biological_age_delta,
        trend=result.trend_direction,
    )


async def _step8_motion_intelligence(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> None:
    """
    Étape 8 (LOT 11) : Calcule et persiste l'analyse Motion Intelligence (30j).
    """
    from datetime import timedelta
    from app.domains.motion.endpoints import _load_vision_sessions
    from app.domains.motion.service import compute_motion_intelligence, save_motion_intelligence

    since = target_date - timedelta(days=30)
    sessions = await _load_vision_sessions(db, user_id, since)
    result = compute_motion_intelligence(sessions, analysis_date=target_date, days_analyzed=30)
    await save_motion_intelligence(db, user_id, result)

    logger.info(
        "Motion Intelligence computed",
        user_id=str(user_id),
        sessions=result.sessions_analyzed,
        movement_health=result.movement_health_score,
        confidence=result.confidence,
    )


async def _step9_adaptive_nutrition_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> None:
    """
    Étape 9 (LOT 11) : Calcule le plan nutritionnel adaptatif du jour — log seulement.
    """
    from app.domains.adaptive_nutrition.endpoints import _load_adaptive_inputs
    from app.domains.adaptive_nutrition.service import compute_adaptive_plan, build_adaptive_nutrition_summary

    inputs = await _load_adaptive_inputs(db, user_id, target_date)
    plan = compute_adaptive_plan(**inputs)
    summary = build_adaptive_nutrition_summary(plan)

    logger.info(
        "Adaptive Nutrition plan computed",
        user_id=str(user_id),
        day_type=plan.day_type.value,
        summary=summary,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrateur principal
# ─────────────────────────────────────────────────────────────────────────────

async def run_daily_pipeline_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> dict:
    """
    Exécute le pipeline complet pour un utilisateur donné.

    Chaque étape est isolée : une erreur est loggée mais ne bloque pas la suite.

    Retourne un dict {step_name: "ok" | "error: message"} pour reporting.
    """
    report: dict = {}
    profile = await _fetch_profile(db, user_id)

    # Step 1 — Daily Metrics
    daily_metrics: Optional[DailyMetrics] = None
    ok, err = await _run_step(
        "daily_metrics",
        _step1_daily_metrics(db, user_id, target_date, profile),
    )
    report["daily_metrics"] = "ok" if ok else f"error: {err}"
    if ok:
        daily_metrics = await _fetch_daily_metrics(db, user_id, target_date)

    # Step 2 — Readiness
    ok, err = await _run_step(
        "readiness",
        _step2_readiness(db, user_id, target_date, daily_metrics),
    )
    report["readiness"] = "ok" if ok else f"error: {err}"

    # Step 3 — Insights
    ok, err = await _run_step(
        "insights",
        _step3_insights(db, user_id, target_date),
    )
    report["insights"] = "ok" if ok else f"error: {err}"

    # Step 4 — Health Plan (log seulement)
    ok, err = await _run_step(
        "health_plan",
        _step4_health_plan(db, user_id, target_date, profile),
    )
    report["health_plan"] = "ok" if ok else f"error: {err}"

    # Step 5 — Longevity (log seulement)
    ok, err = await _run_step(
        "longevity",
        _step5_longevity(db, user_id, profile),
    )
    report["longevity"] = "ok" if ok else f"error: {err}"

    # ── LOT 11 steps ──────────────────────────────────────────────────────────

    # Step 6 — Digital Twin V2 (persist)
    ok, err = await _run_step(
        "digital_twin",
        _step6_digital_twin(db, user_id, target_date),
    )
    report["digital_twin"] = "ok" if ok else f"error: {err}"

    # Step 7 — Biological Age (persist)
    ok, err = await _run_step(
        "biological_age",
        _step7_biological_age(db, user_id, target_date),
    )
    report["biological_age"] = "ok" if ok else f"error: {err}"

    # Step 8 — Motion Intelligence (persist)
    ok, err = await _run_step(
        "motion_intelligence",
        _step8_motion_intelligence(db, user_id, target_date),
    )
    report["motion_intelligence"] = "ok" if ok else f"error: {err}"

    # Step 9 — Adaptive Nutrition (log only)
    ok, err = await _run_step(
        "adaptive_nutrition",
        _step9_adaptive_nutrition_log(db, user_id, target_date),
    )
    report["adaptive_nutrition"] = "ok" if ok else f"error: {err}"

    return report


async def run_daily_pipeline_all_users(target_date: date) -> None:
    """
    Lance le pipeline pour tous les utilisateurs actifs.
    Crée une session DB standalone (hors contexte FastAPI).
    Commit après chaque utilisateur pour isoler les transactions.
    """
    from app.db.session import _get_session_factory

    session_factory = _get_session_factory()
    total = 0
    errors_by_step: dict = {
        "daily_metrics": 0, "readiness": 0,
        "insights": 0, "health_plan": 0, "longevity": 0,
        "digital_twin": 0, "biological_age": 0,
        "motion_intelligence": 0, "adaptive_nutrition": 0,
    }

    async with session_factory() as db:
        # Récupère tous les utilisateurs actifs
        users_res = await db.execute(
            select(User).where(User.is_active.is_(True))
        )
        users = users_res.scalars().all()
        total = len(users)
        logger.info("Pipeline: users to process", count=total, date=str(target_date))

        for user in users:
            try:
                report = await run_daily_pipeline_for_user(db, user.id, target_date)
                await db.commit()

                for step, result in report.items():
                    if result.startswith("error:"):
                        errors_by_step[step] = errors_by_step.get(step, 0) + 1

                logger.info(
                    "User pipeline done",
                    user_id=str(user.id),
                    report=report,
                )
            except Exception as exc:
                await db.rollback()
                logger.error(
                    "User pipeline fatal error",
                    user_id=str(user.id),
                    error=str(exc),
                    exc_info=True,
                )

    logger.info(
        "Daily pipeline complete",
        date=str(target_date),
        users_processed=total,
        errors_by_step=errors_by_step,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cron job entry point
# ─────────────────────────────────────────────────────────────────────────────

async def daily_pipeline_job() -> None:
    """
    Point d'entrée APScheduler. Déclenché à 5h30 heure de Paris.
    """
    target_date = datetime.now(timezone.utc).date()
    logger.info("SOMA daily pipeline starting", date=str(target_date))
    await run_daily_pipeline_all_users(target_date)


# ─────────────────────────────────────────────────────────────────────────────
# Factory scheduler
# ─────────────────────────────────────────────────────────────────────────────

def create_scheduler() -> AsyncIOScheduler:
    """
    Crée et configure l'AsyncIOScheduler SOMA.

    Le scheduler n'est PAS démarré ici — c'est le lifespan FastAPI (main.py)
    qui appelle scheduler.start() au démarrage et scheduler.shutdown() à l'arrêt.

    Cron : chaque jour à 5h30 heure Europe/Paris.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Paris")
    scheduler.add_job(
        daily_pipeline_job,
        CronTrigger(hour=5, minute=30, timezone="Europe/Paris"),
        id="soma_daily_pipeline",
        name="SOMA Daily Health Pipeline",
        replace_existing=True,
        misfire_grace_time=3600,  # Tolère jusqu'à 1h de retard (ex: redémarrage serveur)
    )
    return scheduler
