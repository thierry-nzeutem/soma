"""
Service dashboard SOMA — agrège toutes les données du jour.

Architecture :
  - Chaque méthode est indépendante et tolérante aux données manquantes
  - Chaque None signifie "donnée inconnue" (≠ zéro)
  - Le score de récupération V1 est simplifié mais extensible
  - Les alertes sont générées à partir des écarts aux objectifs
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.user import User, UserProfile, BodyMetric
from app.models.health import HealthSample, SleepSession, HydrationLog
from app.models.workout import WorkoutSession
from app.models.nutrition import NutritionEntry
from app.schemas.dashboard import (
    DashboardResponse, WeightSummary, HydrationSummary, SleepSummary,
    ActivitySummary, NutritionSummary, RecoverySummary,
    DashboardAlert, DashboardRecommendation, DataSourceMeta,
)
from app.services.calculations import (
    calculate_bmi, calculate_hydration_target, calculate_training_load,
)

STEPS_DAILY_GOAL = 8_000
SLEEP_TARGET_HOURS = 8.0


# ── Helpers internes ───────────────────────────────────────────────────────────

def _day_bounds(target_date: date) -> Tuple[datetime, datetime]:
    """Renvoie (début_du_jour, fin_du_jour) en UTC pour une date."""
    start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


async def _get_profile(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserProfile]:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_health_sample(
    db: AsyncSession, user_id: uuid.UUID, sample_type: str,
    day_start: datetime, day_end: datetime,
    aggregation: str = "avg",  # avg | sum | last
) -> Optional[float]:
    """Récupère une métrique santé agrégée pour la journée."""
    q = select(HealthSample.value).where(
        and_(
            HealthSample.user_id == user_id,
            HealthSample.sample_type == sample_type,
            HealthSample.recorded_at >= day_start,
            HealthSample.recorded_at < day_end,
        )
    ).order_by(HealthSample.recorded_at.desc())

    result = await db.execute(q)
    values = [row[0] for row in result]

    if not values:
        return None
    if aggregation == "sum":
        return sum(values)
    if aggregation == "last":
        return values[0]
    return sum(values) / len(values)  # avg


# ── Weight ─────────────────────────────────────────────────────────────────────

async def build_weight_summary(
    db: AsyncSession, user_id: uuid.UUID, profile: Optional[UserProfile],
    today: date,
) -> WeightSummary:
    # Dernier poids toutes dates confondues
    last_result = await db.execute(
        select(BodyMetric)
        .where(and_(BodyMetric.user_id == user_id, BodyMetric.weight_kg.isnot(None)))
        .order_by(BodyMetric.measured_at.desc())
        .limit(1)
    )
    last_metric = last_result.scalar_one_or_none()

    current_kg = last_metric.weight_kg if last_metric else None
    measured_at = last_metric.measured_at if last_metric else None

    # Variation sur 7 jours
    delta_7d = None
    direction = None
    if current_kg:
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        old_result = await db.execute(
            select(BodyMetric.weight_kg)
            .where(and_(
                BodyMetric.user_id == user_id,
                BodyMetric.weight_kg.isnot(None),
                BodyMetric.measured_at >= week_ago,
            ))
            .order_by(BodyMetric.measured_at.asc())
            .limit(1)
        )
        old_kg = old_result.scalar_one_or_none()
        if old_kg and old_kg != current_kg:
            delta_7d = round(current_kg - old_kg, 2)
            direction = "decreasing" if delta_7d < -0.1 else ("increasing" if delta_7d > 0.1 else "stable")

    goal_kg = profile.goal_weight_kg if profile else None
    gap_to_goal = round(current_kg - goal_kg, 1) if (current_kg and goal_kg) else None

    bmi = None
    if current_kg and profile and profile.height_cm:
        bmi = round(calculate_bmi(current_kg, profile.height_cm), 1)

    return WeightSummary(
        current_kg=current_kg,
        measured_at=measured_at,
        delta_7d_kg=delta_7d,
        delta_direction=direction,
        goal_kg=goal_kg,
        gap_to_goal_kg=gap_to_goal,
        bmi_current=bmi,
    )


# ── Hydration ──────────────────────────────────────────────────────────────────

async def build_hydration_summary(
    db: AsyncSession, user_id: uuid.UUID, profile: Optional[UserProfile],
    day_start: datetime, day_end: datetime,
) -> HydrationSummary:
    result = await db.execute(
        select(HydrationLog)
        .where(and_(
            HydrationLog.user_id == user_id,
            HydrationLog.logged_at >= day_start,
            HydrationLog.logged_at < day_end,
        ))
    )
    logs = result.scalars().all()
    total_ml = sum(l.volume_ml for l in logs)

    # Objectif dynamique
    target_ml = 2500  # fallback
    if profile:
        if profile.target_hydration_ml:
            target_ml = int(profile.target_hydration_ml)
        else:
            # Recalcul depuis profil si pas encore dénormalisé
            last_weight_res = await db.execute(
                select(BodyMetric.weight_kg)
                .where(and_(BodyMetric.user_id == user_id, BodyMetric.weight_kg.isnot(None)))
                .order_by(BodyMetric.measured_at.desc())
                .limit(1)
            )
            w = last_weight_res.scalar_one_or_none() or 80.0
            target_ml = int(calculate_hydration_target(w, profile.activity_level or "moderate")[0])

    pct = round((total_ml / target_ml) * 100, 1) if target_ml else 0
    status = "optimal" if pct >= 100 else ("adequate" if pct >= 70 else "insufficient")

    return HydrationSummary(
        total_ml=total_ml,
        target_ml=target_ml,
        pct=pct,
        status=status,
        entries_count=len(logs),
    )


# ── Sleep ──────────────────────────────────────────────────────────────────────

async def build_sleep_summary(
    db: AsyncSession, user_id: uuid.UUID,
    today: date,
) -> SleepSummary:
    """Récupère la session de sommeil de la nuit précédente."""
    # La nuit précédente : hier 12h → aujourd'hui 12h (UTC)
    yesterday_noon = datetime(today.year, today.month, today.day, tzinfo=timezone.utc) - timedelta(hours=12)
    today_noon = yesterday_noon + timedelta(hours=24)

    result = await db.execute(
        select(SleepSession)
        .where(and_(
            SleepSession.user_id == user_id,
            SleepSession.start_at >= yesterday_noon,
            SleepSession.start_at < today_noon,
        ))
        .order_by(SleepSession.start_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session:
        return SleepSummary(
            duration_minutes=None, duration_hours=None,
            sleep_score=None, perceived_quality=None,
            deep_sleep_minutes=None, rem_sleep_minutes=None,
            avg_hrv_ms=None, debt_minutes=None,
            quality_label="unknown",
        )

    duration_h = round(session.duration_minutes / 60, 2) if session.duration_minutes else None
    target_minutes = int(SLEEP_TARGET_HOURS * 60)
    debt = (target_minutes - session.duration_minutes) if session.duration_minutes else None

    # Label de qualité
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
    if session.perceived_quality:
        # Override si qualité perçue disponible
        q = session.perceived_quality
        label = "excellent" if q >= 5 else ("good" if q >= 4 else ("fair" if q >= 3 else "poor"))

    return SleepSummary(
        duration_minutes=session.duration_minutes,
        duration_hours=duration_h,
        sleep_score=session.sleep_score,
        perceived_quality=session.perceived_quality,
        deep_sleep_minutes=session.deep_sleep_minutes,
        rem_sleep_minutes=session.rem_sleep_minutes,
        avg_hrv_ms=session.avg_hrv_ms,
        debt_minutes=debt,
        quality_label=label,
    )


# ── Activity ───────────────────────────────────────────────────────────────────

async def build_activity_summary(
    db: AsyncSession, user_id: uuid.UUID,
    day_start: datetime, day_end: datetime,
) -> ActivitySummary:
    """Agrège les données d'activité du jour depuis health_samples et workout_sessions."""
    steps = await _get_health_sample(db, user_id, "steps", day_start, day_end, "sum")
    active_cal = await _get_health_sample(db, user_id, "active_calories", day_start, day_end, "sum")
    distance = await _get_health_sample(db, user_id, "distance", day_start, day_end, "sum")
    stand = await _get_health_sample(db, user_id, "stand_hours", day_start, day_end, "sum")
    rhr = await _get_health_sample(db, user_id, "resting_heart_rate", day_start, day_end, "avg")
    hrv = await _get_health_sample(db, user_id, "hrv", day_start, day_end, "avg")
    vo2 = await _get_health_sample(db, user_id, "vo2_max", day_start, day_end, "last")

    steps_pct = round((steps / STEPS_DAILY_GOAL) * 100, 1) if steps else None

    # Séance du jour si elle existe
    workout_res = await db.execute(
        select(WorkoutSession)
        .where(and_(
            WorkoutSession.user_id == user_id,
            WorkoutSession.started_at >= day_start,
            WorkoutSession.started_at < day_end,
            WorkoutSession.is_deleted.is_(False),
        ))
        .order_by(WorkoutSession.started_at.desc())
        .limit(1)
    )
    workout = workout_res.scalar_one_or_none()
    workout_data = None
    if workout:
        workout_data = {
            "id": str(workout.id),
            "status": workout.status,
            "session_type": workout.session_type,
            "duration_minutes": workout.duration_minutes,
            "total_tonnage_kg": workout.total_tonnage_kg,
            "rpe_score": workout.rpe_score,
        }

    return ActivitySummary(
        steps=steps,
        steps_goal=STEPS_DAILY_GOAL,
        steps_pct=steps_pct,
        active_calories_kcal=active_cal,
        distance_km=distance,
        stand_hours=stand,
        resting_heart_rate_bpm=rhr,
        hrv_ms=hrv,
        vo2_max=vo2,
        today_workout=workout_data,
    )


# ── Nutrition ──────────────────────────────────────────────────────────────────

async def build_nutrition_summary(
    db: AsyncSession, user_id: uuid.UUID, profile: Optional[UserProfile],
    day_start: datetime, day_end: datetime,
    tdee_kcal: Optional[float],
) -> NutritionSummary:
    result = await db.execute(
        select(NutritionEntry)
        .where(and_(
            NutritionEntry.user_id == user_id,
            NutritionEntry.logged_at >= day_start,
            NutritionEntry.logged_at < day_end,
        ))
    )
    entries = result.scalars().all()

    if not entries:
        # Déterminer si l'utilisateur est en jeûne
        fasting = profile and profile.intermittent_fasting
        # Trouver le dernier repas (avant le jour courant)
        last_meal_res = await db.execute(
            select(NutritionEntry.logged_at)
            .where(and_(
                NutritionEntry.user_id == user_id,
                NutritionEntry.logged_at < day_start,
            ))
            .order_by(NutritionEntry.logged_at.desc())
            .limit(1)
        )
        last_meal_at = last_meal_res.scalar_one_or_none()
        fasting_hours = None
        if last_meal_at:
            now = datetime.now(timezone.utc)
            fasting_hours = round((now - last_meal_at).total_seconds() / 3600, 1)

        return NutritionSummary(
            calories_consumed=None,
            calories_target=profile.target_calories_kcal if profile else None,
            protein_g=None, protein_target_g=profile.target_protein_g if profile else None,
            carbs_g=None, fat_g=None, fiber_g=None,
            meal_count=0, fasting_active=bool(fasting),
            fasting_hours_elapsed=fasting_hours, energy_balance_kcal=None,
        )

    total_cal = sum(e.calories or 0 for e in entries)
    total_prot = sum(e.protein_g or 0 for e in entries)
    total_carbs = sum(e.carbs_g or 0 for e in entries)
    total_fat = sum(e.fat_g or 0 for e in entries)
    total_fiber = sum(e.fiber_g or 0 for e in entries)
    meal_count = len(set(e.meal_type for e in entries if e.meal_type))

    energy_balance = round(total_cal - tdee_kcal, 0) if (total_cal and tdee_kcal) else None

    return NutritionSummary(
        calories_consumed=round(total_cal, 1),
        calories_target=profile.target_calories_kcal if profile else None,
        protein_g=round(total_prot, 1),
        protein_target_g=profile.target_protein_g if profile else None,
        carbs_g=round(total_carbs, 1),
        fat_g=round(total_fat, 1),
        fiber_g=round(total_fiber, 1),
        meal_count=meal_count,
        fasting_active=False,
        fasting_hours_elapsed=None,
        energy_balance_kcal=energy_balance,
    )


# ── Recovery (Score V1 simplifié) ──────────────────────────────────────────────

def compute_recovery_score_v1(
    sleep: SleepSummary,
    hrv_ms: Optional[float],
    resting_hr: Optional[float],
    last_workout_load: Optional[float],
) -> RecoverySummary:
    """
    Score de récupération V1 — simplifié mais extensible.

    Composants (poids ajustés selon disponibilité) :
    - Sommeil: 40% (durée + qualité)
    - HRV: 20% (si disponible)
    - FC repos: 20% (si disponible)
    - Charge entraînement: 20%

    Niveau de confiance proportionnel aux données disponibles.
    """
    scores = {}
    weights = {}

    # ── Sommeil (40%) ─────────────────────────────────────────────────────────
    if sleep.duration_minutes is not None:
        # 480 min = score 100, 300 min = score 0, extrapolation linéaire
        duration_score = max(0, min(100, (sleep.duration_minutes - 300) / (480 - 300) * 100))
        quality_bonus = 0
        if sleep.perceived_quality:
            quality_bonus = (sleep.perceived_quality - 3) * 10  # -20 à +20
        scores["sleep"] = min(100, max(0, duration_score + quality_bonus))
        weights["sleep"] = 0.40

    # ── HRV (20%) ─────────────────────────────────────────────────────────────
    if hrv_ms is not None:
        # Référence générique : HRV > 60ms = excellent, < 20ms = mauvais
        hrv_score = max(0, min(100, (hrv_ms - 20) / (60 - 20) * 100))
        scores["hrv"] = hrv_score
        weights["hrv"] = 0.20

    # ── FC repos (20%) ────────────────────────────────────────────────────────
    if resting_hr is not None:
        # 45 bpm = score 100, 80 bpm = score 0
        hr_score = max(0, min(100, (80 - resting_hr) / (80 - 45) * 100))
        scores["resting_hr"] = hr_score
        weights["resting_hr"] = 0.20

    # ── Charge entraînement (20%) ─────────────────────────────────────────────
    if last_workout_load is not None:
        # Charge 0 → score 100, charge 400+ → score 50, charge 800+ → score 10
        if last_workout_load < 200:
            load_score = 90
        elif last_workout_load < 400:
            load_score = 75
        elif last_workout_load < 600:
            load_score = 55
        else:
            load_score = 35
        scores["training_load"] = load_score
        weights["training_load"] = 0.20

    # ── Calcul pondéré ────────────────────────────────────────────────────────
    if not scores:
        return RecoverySummary(
            readiness_score=None,
            recovery_score=None,
            sleep_contribution=None,
            hrv_contribution=None,
            training_load_contribution=None,
            recommended_intensity="moderate",
            confidence=0.0,
            reasoning="Données insuffisantes pour calculer le score de récupération.",
        )

    total_weight = sum(weights.values())
    weighted_score = sum(scores[k] * weights[k] for k in scores) / total_weight
    overall = round(weighted_score, 1)
    confidence = round(total_weight, 2)  # max 1.0 si toutes les données disponibles

    # Intensité recommandée
    if overall >= 80:
        intensity = "push"
        reasoning = f"Excellente récupération ({overall}/100). Séance intensive recommandée."
    elif overall >= 65:
        intensity = "normal"
        reasoning = f"Bonne récupération ({overall}/100). Séance normale recommandée."
    elif overall >= 50:
        intensity = "moderate"
        reasoning = f"Récupération correcte ({overall}/100). Intensité modérée conseillée."
    elif overall >= 35:
        intensity = "light"
        reasoning = f"Récupération insuffisante ({overall}/100). Séance légère ou mobilité."
    else:
        intensity = "rest"
        reasoning = f"Récupération très basse ({overall}/100). Repos recommandé."

    return RecoverySummary(
        readiness_score=overall,
        recovery_score=scores.get("sleep"),
        sleep_contribution=scores.get("sleep"),
        hrv_contribution=scores.get("hrv"),
        training_load_contribution=scores.get("training_load"),
        recommended_intensity=intensity,
        confidence=confidence,
        reasoning=reasoning,
    )


# ── Alertes ────────────────────────────────────────────────────────────────────

def generate_alerts(
    hydration: HydrationSummary,
    sleep: SleepSummary,
    nutrition: NutritionSummary,
    activity: ActivitySummary,
    recovery: RecoverySummary,
) -> List[DashboardAlert]:
    alerts = []

    # Hydratation
    if hydration.pct < 50:
        alerts.append(DashboardAlert(
            type="hydration", severity="warning",
            message=f"Hydratation très basse : {hydration.total_ml}ml / {hydration.target_ml}ml",
            action="Boire au moins 500ml maintenant",
        ))
    elif hydration.pct < 70:
        alerts.append(DashboardAlert(
            type="hydration", severity="info",
            message=f"Hydratation insuffisante : {hydration.pct}% de l'objectif",
            action="Penser à boire",
        ))

    # Sommeil
    if sleep.quality_label == "poor":
        alerts.append(DashboardAlert(
            type="sleep", severity="warning",
            message="Nuit trop courte détectée — récupération compromise",
            action="Prévoir une sieste courte ou séance légère",
        ))
    if sleep.debt_minutes and sleep.debt_minutes > 90:
        alerts.append(DashboardAlert(
            type="sleep", severity="info",
            message=f"Dette de sommeil : {sleep.debt_minutes} minutes",
            action="Coucher plus tôt ce soir",
        ))

    # Récupération
    if recovery.readiness_score is not None and recovery.readiness_score < 40:
        alerts.append(DashboardAlert(
            type="recovery", severity="warning",
            message=f"Score de récupération bas : {recovery.readiness_score}/100",
            action="Éviter toute séance intense aujourd'hui",
        ))

    # Nutrition (seulement si données disponibles)
    if nutrition.calories_consumed is not None and nutrition.calories_target:
        ratio = nutrition.calories_consumed / nutrition.calories_target
        if ratio < 0.5 and not nutrition.fasting_active:
            alerts.append(DashboardAlert(
                type="nutrition", severity="info",
                message=f"Apport calorique très bas : {nutrition.calories_consumed:.0f} / {nutrition.calories_target:.0f} kcal",
                action="Préparer un repas riche en protéines",
            ))

    return alerts


# ── Recommandations ────────────────────────────────────────────────────────────

def generate_recommendations(
    profile: Optional[UserProfile],
    hydration: HydrationSummary,
    sleep: SleepSummary,
    activity: ActivitySummary,
    recovery: RecoverySummary,
    nutrition: NutritionSummary,
) -> List[DashboardRecommendation]:
    recs = []
    priority = 1

    # Séance du jour
    if not activity.today_workout:
        intensity = recovery.recommended_intensity
        if intensity in ("normal", "push"):
            recs.append(DashboardRecommendation(
                category="workout", priority=priority,
                text=f"Forme correcte — bon moment pour une séance de {profile.primary_goal or 'renforcement'} si prévu.",
            ))
        elif intensity == "light":
            recs.append(DashboardRecommendation(
                category="workout", priority=priority,
                text="Préférer une séance légère (marche, mobilité ou gainage doux).",
            ))
        elif intensity == "rest":
            recs.append(DashboardRecommendation(
                category="recovery", priority=priority,
                text="Journée de repos conseillée — étirements doux si besoin.",
            ))
        priority += 1

    # Protéines
    if nutrition.protein_g is not None and nutrition.protein_target_g:
        if nutrition.protein_g < nutrition.protein_target_g * 0.6:
            recs.append(DashboardRecommendation(
                category="nutrition", priority=priority,
                text=f"Apport protéique insuffisant ({nutrition.protein_g:.0f}g / {nutrition.protein_target_g:.0f}g). Prioriser protéines au prochain repas.",
            ))
            priority += 1

    # Hydratation
    if hydration.pct < 70:
        recs.append(DashboardRecommendation(
            category="hydration", priority=priority,
            text=f"Boire {hydration.target_ml - hydration.total_ml}ml supplémentaires pour atteindre l'objectif.",
        ))
        priority += 1

    # Pas
    if activity.steps is not None and activity.steps_pct and activity.steps_pct < 50:
        recs.append(DashboardRecommendation(
            category="workout", priority=priority,
            text=f"Seulement {int(activity.steps)} pas — prévoir 15min de marche.",
        ))
        priority += 1

    return sorted(recs, key=lambda r: r.priority)


# ── Dashboard principal ────────────────────────────────────────────────────────

async def build_dashboard(
    db: AsyncSession,
    user: User,
    target_date: Optional[date] = None,
) -> DashboardResponse:
    """Point d'entrée principal du service dashboard."""
    today = target_date or date.today()
    day_start, day_end = _day_bounds(today)

    # Profil
    profile = await _get_profile(db, user.id)

    # Charge de la séance précédente (pour score récupération)
    yesterday_start = day_start - timedelta(days=1)
    prev_workout_res = await db.execute(
        select(WorkoutSession.internal_load_score)
        .where(and_(
            WorkoutSession.user_id == user.id,
            WorkoutSession.started_at >= yesterday_start,
            WorkoutSession.started_at < day_start,
            WorkoutSession.is_deleted.is_(False),
            WorkoutSession.status == "completed",
        ))
        .order_by(WorkoutSession.started_at.desc())
        .limit(1)
    )
    last_workout_load = prev_workout_res.scalar_one_or_none()

    # Données HRV et FC repos du jour
    hrv = await _get_health_sample(db, user.id, "hrv", day_start, day_end, "avg")
    rhr = await _get_health_sample(db, user.id, "resting_heart_rate", day_start, day_end, "avg")

    # Build de chaque section en parallèle (logique)
    body = await build_weight_summary(db, user.id, profile, today)
    hydration = await build_hydration_summary(db, user.id, profile, day_start, day_end)
    sleep = await build_sleep_summary(db, user.id, today)
    activity = await build_activity_summary(db, user.id, day_start, day_end)

    tdee = profile.tdee_kcal if profile else None
    nutrition = await build_nutrition_summary(db, user.id, profile, day_start, day_end, tdee)

    # Persistance du score de récupération (LOT 2)
    # Import lazy pour éviter la dépendance circulaire
    # (readiness_service importe compute_recovery_score_v1 depuis ce module)
    try:
        from app.services.readiness_service import compute_and_persist_readiness
        readiness_model = await compute_and_persist_readiness(
            db=db,
            user_id=user.id,
            score_date=today,
            sleep=sleep,
            hrv_ms=hrv,
            resting_hr=rhr,
            last_workout_load=last_workout_load,
        )
        recovery = RecoverySummary(
            readiness_score=readiness_model.overall_readiness,
            recovery_score=readiness_model.recovery_score,
            sleep_contribution=readiness_model.sleep_score,
            hrv_contribution=readiness_model.hrv_score,
            training_load_contribution=readiness_model.training_load_score,
            recommended_intensity=readiness_model.recommended_intensity or "moderate",
            confidence=readiness_model.confidence_score or 0.0,
            reasoning=readiness_model.reasoning or "Score de récupération calculé.",
        )
    except Exception:
        # Fallback : calcul à la volée si la persistance échoue
        recovery = compute_recovery_score_v1(sleep, hrv, rhr, last_workout_load)

    # Alertes + recommandations
    alerts = generate_alerts(hydration, sleep, nutrition, activity, recovery)
    recommendations = generate_recommendations(profile, hydration, sleep, activity, recovery, nutrition)

    # Méta
    meta = DataSourceMeta(
        has_weight=body.current_kg is not None,
        has_sleep=sleep.duration_minutes is not None,
        has_hrv=hrv is not None,
        has_steps=activity.steps is not None,
        has_nutrition=nutrition.calories_consumed is not None,
        has_workout_today=activity.today_workout is not None,
        data_freshness_hours=None,
        profile_completeness_pct=profile.profile_completeness_score if profile else 0.0,
    )

    return DashboardResponse(
        date=str(today),
        body=body,
        hydration=hydration,
        sleep=sleep,
        activity=activity,
        nutrition=nutrition,
        recovery=recovery,
        alerts=alerts,
        recommendations=recommendations,
        metadata=meta,
        generated_at=datetime.now(timezone.utc),
    )
