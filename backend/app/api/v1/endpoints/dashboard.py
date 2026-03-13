"""
Endpoint GET /api/v1/dashboard/today
Renvoie l'instantané journalier complet de l'utilisateur connecté.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/today",
    response_model=DashboardResponse,
    summary="Dashboard journalier",
    description=(
        "Renvoie l'instantané complet de la journée : poids, hydratation, "
        "sommeil, activité, nutrition, score de récupération, alertes et "
        "recommandations. Tolérant aux données manquantes — chaque section "
        "renvoie None pour les champs non renseignés plutôt qu'une erreur."
    ),
)
async def get_dashboard_today(
    date: Optional[str] = Query(
        None,
        description="Date cible au format YYYY-MM-DD. Défaut = aujourd'hui.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """
    Construit et retourne le dashboard pour la date demandée.

    - Si `date` est absent, utilise la date du serveur (UTC).
    - Si la date est invalide (ex : 2025-02-30), retourne 422.
    - Le score de récupération V1 est calculé à la volée (non mis en cache).
    """
    target_date = None
    if date:
        try:
            from datetime import date as date_type
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Date invalide : '{date}'. Format attendu : YYYY-MM-DD",
            )

    return await build_dashboard(db, current_user, target_date)
