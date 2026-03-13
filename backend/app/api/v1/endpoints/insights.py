"""
Endpoints Insights SOMA — LOT 3.

Périmètre :
  - Liste des insights détectés automatiquement (filtrables)
  - Déclenchement manuel de l'Insight Engine
  - Marquage lu / acquitté
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.core.entitlements import require_feature
from app.core.features import FeatureCode
from app.schemas.insights import InsightListResponse, InsightResponse
from app.services import insight_service


insights_router = APIRouter(prefix="/insights", tags=["Insights"])

VALID_CATEGORIES = frozenset(
    {"nutrition", "sleep", "activity", "recovery", "training", "hydration", "weight"}
)
VALID_SEVERITIES = frozenset({"info", "warning", "critical"})


@insights_router.get("", response_model=InsightListResponse)
async def list_insights(
    days: int = Query(
        30, ge=1, le=90,
        description="Fenêtre temporelle (1-90 jours). Défaut : 30.",
    ),
    category: Optional[str] = Query(
        None,
        description=(
            "Filtrer par catégorie : nutrition | sleep | activity | recovery | "
            "training | hydration | weight"
        ),
    ),
    severity: Optional[str] = Query(
        None,
        description="Filtrer par sévérité : info | warning | critical",
    ),
    include_dismissed: bool = Query(
        False,
        description="Inclure les insights acquittés. Défaut : false.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste des insights de santé détectés automatiquement.

    Les insights sont générés lors de :
    - `POST /insights/run` (déclenchement manuel)
    - `GET /metrics/daily` (déclenchement automatique, à venir LOT 4)

    **Filtres disponibles :**
    - `category` : nutrition, sleep, activity, recovery, training, hydration, weight
    - `severity` : info, warning, critical
    - `include_dismissed` : inclure les insights acquittés

    **Résumé retourné :**
    - `unread_count` : insights non lus
    - `critical_count` : alertes critiques actives
    - `by_category` : répartition par catégorie
    - `by_severity` : répartition par sévérité
    """
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Catégorie invalide. Valeurs acceptées : {', '.join(sorted(VALID_CATEGORIES))}",
        )
    if severity and severity not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Sévérité invalide. Valeurs acceptées : {', '.join(sorted(VALID_SEVERITIES))}",
        )

    insights = await insight_service.get_insights(
        db=db,
        user_id=current_user.id,
        days=days,
        include_dismissed=include_dismissed,
        category=category,
        severity=severity,
    )
    return insight_service.build_insight_list_response(insights)


@insights_router.post("/run", response_model=InsightListResponse)
async def run_insight_engine_endpoint(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date d'analyse (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.ADVANCED_INSIGHTS)),
):
    """
    Déclenche l'Insight Engine et persiste les insights détectés.

    **Pré-requis** : Des DailyMetrics doivent exister pour les 7 derniers jours.
    Appelez `GET /metrics/daily` au préalable pour s'assurer que les données sont calculées.

    **Règles détectées :**
    1. Apport protéique insuffisant (< 60% cible, 3+ jours / 7)
    2. Déficit calorique excessif (< 60% cible, 2+ jours avec données)
    3. Sédentarité prolongée (< 4000 pas, 5+ jours / 7)
    4. Fatigue cumulée (readiness < 50, 3+ jours avec données)
    5. Dette de sommeil (< 6h, 3+ nuits / 7)
    6. Déshydratation chronique (< 60% cible, 4+ jours / 7)
    7. Risque de sur-entraînement (ACWR > 1.5 — charge aiguë/chronique)

    Les insights sont persistés en base (upsert). Retourne tous les insights
    détectés pour cette date d'analyse.
    """
    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )

    persisted = await insight_service.run_and_persist_insights(db, current_user.id, target_date)
    await db.commit()
    return insight_service.build_insight_list_response(persisted)


@insights_router.patch("/{insight_id}/read", response_model=InsightResponse)
async def mark_insight_read(
    insight_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marque un insight comme lu.

    L'insight reste visible dans la liste. Seul `is_read` passe à `true`.
    """
    try:
        iid = uuid.UUID(insight_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID d'insight invalide (format UUID requis)",
        )

    insight = await insight_service.mark_read(db, iid, current_user.id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight introuvable ou n'appartient pas à cet utilisateur",
        )
    await db.commit()
    return InsightResponse.model_validate(insight)


@insights_router.patch("/{insight_id}/dismiss", response_model=InsightResponse)
async def dismiss_insight(
    insight_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Acquitte un insight (marque lu + acquitté).

    Un insight acquitté n'apparaît plus dans la liste par défaut.
    Il reste accessible via `GET /insights?include_dismissed=true`.

    Utilisez cette action quand l'utilisateur a pris connaissance de l'insight
    et décide de ne plus en tenir compte.
    """
    try:
        iid = uuid.UUID(insight_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID d'insight invalide (format UUID requis)",
        )

    insight = await insight_service.mark_dismissed(db, iid, current_user.id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight introuvable ou n'appartient pas à cet utilisateur",
        )
    await db.commit()
    return InsightResponse.model_validate(insight)
