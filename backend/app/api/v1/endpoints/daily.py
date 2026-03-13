"""Endpoint Daily Briefing — LOT 18.

GET /daily/briefing : briefing matinal quotidien agrégé.

Agrège depuis 5 sources DB :
  - DailyMetrics (nutrition, hydratation, sommeil)
  - ReadinessScore (récupération)
  - DigitalTwinSnapshot (statut global)
  - DailyRecommendation (plan entraînement + coach tip)
  - Insight (top insight non lu)

Track l'événement analytics "morning_briefing_view" à chaque appel.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.core.entitlements import require_feature
from app.core.features import FeatureCode
from app.schemas.briefing import DailyBriefingResponse
from app.services.daily_briefing_service import compute_daily_briefing
from app.services.daily_metrics_service import lazy_ensure_today_metrics
from app.core.analytics import track_event

logger = logging.getLogger(__name__)

daily_router = APIRouter(prefix="/daily", tags=["Daily Briefing"])


@daily_router.get("/briefing", response_model=DailyBriefingResponse)
async def get_daily_briefing(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date du briefing (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.DAILY_BRIEFING)),
):
    """Briefing matinal quotidien SOMA.

    Retourne une agrégation des données de santé du jour :

    - **Récupération** : score 0-100, niveau, intensité recommandée
    - **Sommeil** : durée et qualité de la nuit dernière
    - **Entraînement** : suggestion du jour (type, intensité, durée)
    - **Nutrition** : objectifs caloriques et macros
    - **Hydratation** : objectif du jour en mL
    - **Jumeau numérique** : statut global et préoccupation principale
    - **Alertes** : 3 alertes prioritaires max
    - **Insight** : conseil santé non lu le plus récent
    - **Coach tip** : extrait du morning briefing IA

    Ce endpoint est optimisé pour être appelé dès l'ouverture de l'app.
    Aucune computation lourde : lecture DB uniquement.
    """
    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )

    # Garantit que les métriques du jour existent (calcul lazy si nécessaire)
    try:
        await lazy_ensure_today_metrics(db, current_user.id, target_date)
    except Exception:
        logger.debug("briefing: lazy_ensure_today_metrics failed (non-blocking)")

    # Agrège le briefing depuis les données DB
    briefing = await compute_daily_briefing(db, current_user.id, target_date)

    # Analytics fire-and-forget
    await track_event(db, current_user.id, "morning_briefing_view", {
        "date": target_date.isoformat(),
    })

    return DailyBriefingResponse(
        briefing_date=briefing.briefing_date,
        generated_at=briefing.generated_at,
        readiness_score=briefing.readiness_score,
        readiness_level=briefing.readiness_level,
        readiness_color=briefing.readiness_color,
        recommended_intensity=briefing.recommended_intensity,
        sleep_duration_h=briefing.sleep_duration_h,
        sleep_quality_label=briefing.sleep_quality_label,
        training_type=briefing.training_type,
        training_intensity=briefing.training_intensity,
        training_duration_min=briefing.training_duration_min,
        calorie_target=briefing.calorie_target,
        protein_target_g=briefing.protein_target_g,
        carb_target_g=briefing.carb_target_g,
        fat_target_g=briefing.fat_target_g,
        hydration_target_ml=briefing.hydration_target_ml,
        twin_status=briefing.twin_status,
        twin_primary_concern=briefing.twin_primary_concern,
        alerts=briefing.alerts,
        top_insight=briefing.top_insight,
        coach_tip=briefing.coach_tip,
    )
