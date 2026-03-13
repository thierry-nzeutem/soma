"""
Endpoints DailyMetrics SOMA — LOT 3.

Périmètre :
  - Snapshot journalier agrégé de toutes les métriques santé
  - Historique des snapshots avec tendances

Le calcul est déclenché automatiquement (lazy) à chaque appel GET /metrics/daily.
Un cache de 2h évite les recalculs inutiles (contournable via force_recompute=true).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserProfile
from app.core.deps import get_current_user
from app.schemas.metrics import DailyMetricsResponse, DailyMetricsHistoryResponse
from app.services.daily_metrics_service import (
    compute_and_persist_daily_metrics,
    get_metrics_history,
)


metrics_router = APIRouter(prefix="/metrics", tags=["Daily Metrics"])


@metrics_router.get("/daily", response_model=DailyMetricsResponse)
async def get_daily_metrics(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date cible (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    force_recompute: bool = Query(
        False,
        description="Forcer le recalcul même si un snapshot récent (< 2h) existe.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Snapshot journalier agrégé de toutes les métriques santé.

    Agrège automatiquement depuis toutes les sources :
    - **Corps** : dernier poids disponible
    - **Nutrition** : calories, macros, repas du journal
    - **Hydratation** : total du jour
    - **Activité** : pas, calories actives, distance
    - **Physiologie** : HRV, FC de repos
    - **Sommeil** : durée, score, qualité
    - **Entraînement** : séances, tonnage, charge
    - **Scores** : readiness, complétude des données

    Le snapshot est mis en cache 2h. Utilisez `force_recompute=true` pour forcer
    un recalcul immédiat (utile après saisie de nouvelles données).
    """
    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )

    # Récupère le profil pour les objectifs nutritionnels
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()

    snapshot = await compute_and_persist_daily_metrics(
        db=db,
        user_id=current_user.id,
        target_date=target_date,
        profile=profile,
        force_recompute=force_recompute,
    )
    await db.commit()
    return DailyMetricsResponse.model_validate(snapshot)


@metrics_router.get("/history", response_model=DailyMetricsHistoryResponse)
async def get_metrics_history_endpoint(
    days: int = Query(
        30, ge=1, le=365,
        description="Nombre de jours d'historique (1-365). Défaut : 30.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Historique des snapshots journaliers sur N jours.

    Retourne les snapshots en ordre décroissant (le plus récent en premier)
    avec les tendances calculées sur la période :
    - Readiness moyen, heures de sommeil moyennes
    - Calories moyennes, pas moyens, protéines moyennes
    - Tendance poids (delta début → fin de période en kg)
    - Fréquence entraînements (% de jours avec au moins une séance)

    Seuls les jours avec un snapshot calculé sont inclus (`days_available` ≤ `days_requested`).
    """
    return await get_metrics_history(db, current_user.id, days)
