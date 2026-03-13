"""
Endpoints scores SOMA — LOT 2 + LOT 3.

Périmètre :
  - Lecture du ReadinessScore du jour (calculé et persisté par le dashboard)
  - Historique sur N jours
  - Score de longévité multi-dimensionnel (LOT 3)
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.user import User, UserProfile
from app.models.user import BodyMetric
from app.core.deps import get_current_user
from app.schemas.scores import ReadinessScoreResponse, ReadinessScoreHistoryResponse
from app.schemas.insights import LongevityScoreResponse
from app.services.readiness_service import (
    get_readiness_score,
    get_readiness_history,
)
from app.services.longevity_engine import compute_longevity_score
from app.services.daily_metrics_service import get_metrics_history, lazy_ensure_today_metrics


scores_router = APIRouter(prefix="/scores", tags=["Recovery Scores"])


@scores_router.get("/readiness/today", response_model=ReadinessScoreResponse)
async def get_readiness_today(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date cible (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Récupère le score de récupération du jour.

    Le score est calculé et persisté lors de l'appel à `GET /dashboard/today`.
    Si aucun score n'a encore été calculé pour cette date, retourne 404.

    **Conseil** : Appeler `/dashboard/today` en premier pour s'assurer que le score est calculé.
    """
    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )

    score = await get_readiness_score(db, current_user.id, target_date)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Aucun score de récupération trouvé pour le {target_date}. "
                "Appelez /dashboard/today pour déclencher le calcul."
            ),
        )
    return ReadinessScoreResponse.model_validate(score)


@scores_router.get("/readiness/history", response_model=ReadinessScoreHistoryResponse)
async def get_readiness_history_endpoint(
    days: int = Query(
        30, ge=1, le=365,
        description="Nombre de jours d'historique (1-365). Défaut : 30.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Historique des scores de récupération sur N jours.

    Retourne les scores en ordre décroissant (le plus récent en premier).
    Seuls les jours avec un score calculé sont retournés (`days_available` ≤ `days_requested`).
    """
    return await get_readiness_history(db, current_user.id, days)


# ── Score de Longévité (LOT 3) ─────────────────────────────────────────────────

@scores_router.get("/longevity", response_model=LongevityScoreResponse)
async def get_longevity_score(
    days: int = Query(
        30, ge=7, le=90,
        description="Fenêtre d'analyse en jours (7-90). Défaut : 30.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Score de longévité multi-dimensionnel (0-100).

    Évalue 7 composantes de la santé à long terme sur les `days` derniers jours :
    - **Cardio** (20%) : pas, HRV, calories actives, fréquence d'activité
    - **Force** (20%) : tonnage moyen, fréquence entraînements
    - **Sommeil** (15%) : durée et qualité
    - **Nutrition** (15%) : conformité calorique et protéique, régularité
    - **Poids/IMC** (15%) : IMC et tendance selon l'objectif
    - **Composition corporelle** (optionnel +10%) : % de graisse si disponible
    - **Régularité** (15%) : % de jours avec données

    **Âge biologique estimé** : basé sur l'écart au score optimal (75/100).
    Chaque 5 points de score = ±1 an d'âge biologique estimé.

    **Leviers d'amélioration** : composantes avec score < 70, triées par priorité.

    Nécessite des DailyMetrics sur la période (appeler `GET /metrics/daily` régulièrement).
    """
    today = datetime.now(timezone.utc).date()

    # Profil utilisateur
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()

    # Fallback LOT 4 : lazy compute si daily_metrics du jour absentes.
    # Assure qu'au moins le snapshot du jour est disponible dans l'historique.
    await lazy_ensure_today_metrics(db, current_user.id, today)

    # Historique métriques
    history = await get_metrics_history(db, current_user.id, days)
    records = history.history  # List[DailyMetricsResponse]

    if not records:
        # Pas de données : score minimal avec confiance 0
        result = compute_longevity_score(
            actual_age=profile.age if profile else None,
        )
    else:
        # Agrégation des métriques
        avg_steps = history.avg_steps
        avg_sleep_h = history.avg_sleep_hours
        weight_trend = history.weight_trend_kg
        workout_freq_pct = history.workout_frequency_pct

        # HRV et calories actives moyens
        hrv_vals = [r.hrv_ms for r in records if r.hrv_ms is not None]
        avg_hrv = sum(hrv_vals) / len(hrv_vals) if hrv_vals else None

        active_cal_vals = [r.active_calories_kcal for r in records if r.active_calories_kcal is not None]
        avg_active_cal = sum(active_cal_vals) / len(active_cal_vals) if active_cal_vals else None

        # Tonnage et séances
        tonnage_vals = [r.total_tonnage_kg for r in records if r.total_tonnage_kg is not None]
        workout_counts = [r.workout_count for r in records if r.workout_count > 0]
        avg_tonnage = (
            sum(tonnage_vals) / len(tonnage_vals) if tonnage_vals else None
        )
        total_workouts = sum(r.workout_count for r in records)

        # Sommeil qualité (via sleep_score)
        sleep_q_vals = [r.sleep_score for r in records if r.sleep_score is not None]
        avg_sleep_quality = sum(sleep_q_vals) / len(sleep_q_vals) if sleep_q_vals else None

        # Nutrition : conformité calorique et protéique
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

        # Poids et IMC
        bmi = profile.bmi if profile else None
        goal = profile.primary_goal if profile else None

        # Composition corporelle (dernière mesure)
        body_fat_pct: Optional[float] = None
        bm_res = await db.execute(
            select(BodyMetric.body_fat_pct)
            .where(and_(
                BodyMetric.user_id == current_user.id,
                BodyMetric.body_fat_pct.isnot(None),
            ))
            .order_by(BodyMetric.measured_at.desc())
            .limit(1)
        )
        body_fat_pct = bm_res.scalar_one_or_none()

        # Régularité du suivi
        tracking_pct = (
            (history.days_available / max(1, days)) * 100
        )

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
            bmi=bmi,
            weight_trend_kg_30d=weight_trend,
            goal=goal,
            body_fat_pct=body_fat_pct,
            sex=profile.sex if profile else None,
            tracking_days_pct=tracking_pct,
        )

    return LongevityScoreResponse(
        user_id=current_user.id,
        score_date=today,
        cardio_score=result.cardio_score,
        strength_score=result.strength_score,
        sleep_score=result.sleep_score,
        nutrition_score=result.nutrition_score,
        weight_score=result.weight_score,
        body_comp_score=result.body_comp_score,
        consistency_score=result.consistency_score,
        longevity_score=result.longevity_score,
        biological_age_estimate=result.biological_age_estimate,
        top_improvement_levers=result.top_improvement_levers,
        algorithm_version="v1.0",
        created_at=datetime.now(timezone.utc),
    )
