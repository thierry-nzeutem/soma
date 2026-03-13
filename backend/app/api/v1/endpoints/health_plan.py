"""
Endpoint Plan Santé Journalier SOMA — LOT 3 / Morning Briefing IA LOT 9.

GET /health/plan/today : génère le "morning briefing" du jour.

LOT 9 : génère un morning_briefing texte via Claude Coach (mode mock en dev).
  - Le texte est stocké dans DailyRecommendation.morning_briefing
  - Le briefing IA est retourné dans la réponse (champ morning_briefing)

Agrège :
  - Score de récupération (ReadinessScore)
  - Métriques du jour (DailyMetrics)
  - Profil utilisateur (objectifs, préférences)
  - Dernière séance d'entraînement
  - Cibles nutritionnelles calculées
  - État métabolique (MetabolicTwin LOT 9)
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.user import User, UserProfile
from app.models.metrics import DailyMetrics
from app.models.scores import ReadinessScore, DailyRecommendation
from app.models.workout import WorkoutSession
from app.core.deps import get_current_user
from app.schemas.insights import DailyHealthPlanResponse
from app.services.nutrition_engine import compute_nutrition_targets
from app.services.health_plan_service import generate_daily_health_plan
from app.services.daily_metrics_service import lazy_ensure_today_metrics
from app.services.context_builder import build_coach_context
from app.services.claude_client import generate_coach_reply

logger = logging.getLogger(__name__)

HEALTH_PLAN_CACHE_HOURS = 6


health_plan_router = APIRouter(prefix="/health", tags=["Health Plan"])


@health_plan_router.get("/plan/today", response_model=DailyHealthPlanResponse)
async def get_daily_health_plan(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date du plan (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Plan santé journalier personnalisé ("morning briefing").

    Agrège toutes les sources de données pour produire un plan d'action concret :

    - **Séance recommandée** : type, intensité, durée selon la récupération
    - **Objectifs nutritionnels** : calories, protéines, glucides, lipides, fibres, hydratation
    - **Contexte récupération** : niveau (excellent / good / fair / poor) et intensité recommandée
    - **Alertes prioritaires** (≤ 3) : issues du dashboard
    - **Conseils du jour** (2-4) : actions concrètes et prioritaires
    - **Fenêtre alimentaire** : horaires si jeûne intermittent actif
    - **Focus nutritionnel** : un nutriment à surveiller particulièrement

    **Conseil** : Appeler `GET /metrics/daily` et `GET /dashboard/today` avant ce endpoint
    pour s'assurer que les scores de récupération et métriques sont à jour.
    """
    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )
    target_date_str = target_date.isoformat()

    # ── Profil utilisateur ─────────────────────────────────────────────────────
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()

    # ── Fallback LOT 4 : lazy compute si daily_metrics absentes ───────────────
    # Garantit que les métriques du jour existent avant de lire les données.
    # Si le scheduler a déjà tourné à 5h30, ce call est quasi-immédiat (cache 2h).
    await lazy_ensure_today_metrics(db, current_user.id, target_date, profile=profile)

    # ── Score de récupération ──────────────────────────────────────────────────
    readiness_res = await db.execute(
        select(ReadinessScore).where(and_(
            ReadinessScore.user_id == current_user.id,
            ReadinessScore.score_date == target_date,
        ))
    )
    readiness = readiness_res.scalar_one_or_none()
    readiness_score = readiness.overall_readiness if readiness else None
    recommended_intensity = (
        (readiness.recommended_intensity if readiness else None) or "moderate"
    )

    # ── Métriques du jour ──────────────────────────────────────────────────────
    metrics_res = await db.execute(
        select(DailyMetrics).where(and_(
            DailyMetrics.user_id == current_user.id,
            DailyMetrics.metrics_date == target_date,
        ))
    )
    metrics = metrics_res.scalar_one_or_none()

    hydration_pct: Optional[float] = None
    sleep_quality_label: Optional[str] = None
    protein_pct: Optional[float] = None
    calorie_pct: Optional[float] = None
    has_workout_today = False

    if metrics:
        if (
            metrics.hydration_ml is not None
            and metrics.hydration_target_ml
            and metrics.hydration_target_ml > 0
        ):
            hydration_pct = metrics.hydration_ml / metrics.hydration_target_ml

        sleep_quality_label = metrics.sleep_quality_label

        if (
            metrics.protein_g is not None
            and metrics.protein_target_g
            and metrics.protein_target_g > 0
        ):
            protein_pct = metrics.protein_g / metrics.protein_target_g

        if (
            metrics.calories_consumed is not None
            and metrics.calories_target
            and metrics.calories_target > 0
        ):
            calorie_pct = metrics.calories_consumed / metrics.calories_target

        has_workout_today = (metrics.workout_count or 0) > 0

    # ── Dernière séance pour le bonus calories ─────────────────────────────────
    workout_type_today: Optional[str] = None
    workout_duration_today: Optional[float] = None

    if has_workout_today:
        w_res = await db.execute(
            select(WorkoutSession)
            .where(and_(
                WorkoutSession.user_id == current_user.id,
                WorkoutSession.is_deleted.is_(False),
            ))
            .order_by(WorkoutSession.started_at.desc())
            .limit(1)
        )
        last_workout = w_res.scalar_one_or_none()
        if last_workout:
            workout_type_today = getattr(last_workout, "workout_type", None)
            workout_duration_today = getattr(last_workout, "duration_minutes", None)

    # ── Cibles nutritionnelles personnalisées ──────────────────────────────────
    usual_wake_str: Optional[str] = None
    if profile and profile.usual_wake_time:
        try:
            usual_wake_str = str(profile.usual_wake_time)[:5]
        except Exception:
            pass

    nutrition_targets = compute_nutrition_targets(
        age=profile.age if profile else None,
        sex=profile.sex if profile else None,
        height_cm=profile.height_cm if profile else None,
        weight_kg=None,  # Pris depuis la dernière mesure via DailyMetrics
        body_fat_pct=None,
        activity_level=profile.activity_level if profile else None,
        fitness_level=profile.fitness_level if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        dietary_regime=profile.dietary_regime if profile else None,
        intermittent_fasting=profile.intermittent_fasting if profile else False,
        fasting_protocol=profile.fasting_protocol if profile else None,
        usual_wake_time=usual_wake_str,
        workout_type=workout_type_today,
        workout_duration_minutes=workout_duration_today,
    )

    # ── Cache DailyRecommendation (6h) ────────────────────────────────────────
    cached_rec_res = await db.execute(
        select(DailyRecommendation).where(and_(
            DailyRecommendation.user_id == current_user.id,
            DailyRecommendation.recommendation_date == target_date,
        ))
    )
    cached_rec = cached_rec_res.scalar_one_or_none()

    if cached_rec and cached_rec.daily_plan:
        age = datetime.now(timezone.utc) - cached_rec.generated_at.replace(tzinfo=timezone.utc)
        if age < timedelta(hours=HEALTH_PLAN_CACHE_HOURS):
            plan_dict = cached_rec.daily_plan
            return DailyHealthPlanResponse(
                date=plan_dict.get("date", target_date_str),
                generated_at=cached_rec.generated_at,
                from_cache=True,
                workout_recommendation=plan_dict.get("workout_recommendation", {}),
                protein_target_g=plan_dict.get("protein_target_g", 0),
                calorie_target=plan_dict.get("calorie_target", 0),
                hydration_target_ml=plan_dict.get("hydration_target_ml", 0),
                steps_goal=plan_dict.get("steps_goal", 8000),
                sleep_target_hours=plan_dict.get("sleep_target_hours", 8.0),
                readiness_level=plan_dict.get("readiness_level", "fair"),
                recommended_intensity=plan_dict.get("recommended_intensity", "moderate"),
                alerts=plan_dict.get("alerts", []),
                daily_tips=plan_dict.get("daily_tips", []),
                eating_window=plan_dict.get("eating_window"),
                nutrition_focus=plan_dict.get("nutrition_focus"),
            )

    # ── Génération du plan ─────────────────────────────────────────────────────
    plan = generate_daily_health_plan(
        target_date_str=target_date_str,
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

    # ── Morning Briefing IA (LOT 9) ────────────────────────────────────────────
    # Génère un texte de briefing personnalisé via Claude Coach.
    # En mode mock (développement), réponse simulée instantanée.
    morning_briefing_text: Optional[str] = None
    try:
        coach_ctx = await build_coach_context(
            db, current_user.id, profile, target_date
        )
        morning_question = (
            f"Génère mon morning briefing pour le {target_date_str}. "
            "Analyse mon état du jour en 3-4 points clés et donne-moi "
            "les 2-3 actions prioritaires pour optimiser ma journée."
        )
        morning_briefing_text = await generate_coach_reply(
            question=morning_question,
            context_text=coach_ctx.to_prompt_text(),
        )
    except Exception as exc:
        logger.warning("Morning briefing IA non généré : %s", exc)

    # ── Persistance dans DailyRecommendation ──────────────────────────────────
    plan_dict = {
        "date": plan.date,
        "workout_recommendation": plan.workout_recommendation,
        "protein_target_g": plan.protein_target_g,
        "calorie_target": plan.calorie_target,
        "hydration_target_ml": plan.hydration_target_ml,
        "steps_goal": plan.steps_goal,
        "sleep_target_hours": plan.sleep_target_hours,
        "readiness_level": plan.readiness_level,
        "recommended_intensity": plan.recommended_intensity,
        "alerts": plan.alerts,
        "daily_tips": plan.daily_tips,
        "eating_window": plan.eating_window,
        "nutrition_focus": plan.nutrition_focus,
    }
    now = datetime.now(timezone.utc)
    if cached_rec:
        cached_rec.daily_plan = plan_dict
        cached_rec.workout_recommendation = plan.workout_recommendation
        cached_rec.hydration_target_ml = int(plan.hydration_target_ml)
        cached_rec.alerts = {"items": plan.alerts}
        cached_rec.generated_at = now
        if morning_briefing_text:
            cached_rec.morning_briefing = morning_briefing_text
    else:
        rec = DailyRecommendation(
            user_id=current_user.id,
            recommendation_date=target_date,
            daily_plan=plan_dict,
            workout_recommendation=plan.workout_recommendation,
            hydration_target_ml=int(plan.hydration_target_ml),
            alerts={"items": plan.alerts},
            generated_at=now,
            morning_briefing=morning_briefing_text,
        )
        db.add(rec)
    await db.flush()

    return DailyHealthPlanResponse(
        date=plan.date,
        generated_at=now,
        from_cache=False,
        workout_recommendation=plan.workout_recommendation,
        protein_target_g=plan.protein_target_g,
        calorie_target=plan.calorie_target,
        hydration_target_ml=plan.hydration_target_ml,
        steps_goal=plan.steps_goal,
        sleep_target_hours=plan.sleep_target_hours,
        readiness_level=plan.readiness_level,
        recommended_intensity=plan.recommended_intensity,
        alerts=plan.alerts,
        daily_tips=plan.daily_tips,
        eating_window=plan.eating_window,
        nutrition_focus=plan.nutrition_focus,
    )
