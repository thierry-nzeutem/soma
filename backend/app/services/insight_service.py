"""
Insight Service SOMA — LOT 3.

Couche DB pour le modèle Insight :
  - Lecture des insights persistés (filtrage par catégorie, sévérité, période)
  - Exécution de l'Insight Engine + persistance (upsert par contrainte unique)
  - Marquage lu / acquitté
"""
import uuid
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.insights import Insight
from app.models.metrics import DailyMetrics
from app.services.insight_engine import run_insight_engine
from app.schemas.insights import InsightListResponse, InsightResponse

logger = logging.getLogger(__name__)

INSIGHT_EXPIRY_DAYS = 7  # Les insights expirent après 7 jours par défaut


# ── Lecture ─────────────────────────────────────────────────────────────────────

async def get_insights(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 30,
    include_dismissed: bool = False,
    category: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[Insight]:
    """Récupère les insights d'un utilisateur selon les filtres."""
    cutoff = date.today() - timedelta(days=days)
    conditions = [
        Insight.user_id == user_id,
        Insight.insight_date >= cutoff,
    ]
    if not include_dismissed:
        conditions.append(Insight.is_dismissed.is_(False))
    if category:
        conditions.append(Insight.category == category)
    if severity:
        conditions.append(Insight.severity == severity)

    res = await db.execute(
        select(Insight)
        .where(and_(*conditions))
        .order_by(Insight.detected_at.desc())
    )
    return res.scalars().all()


# ── Exécution moteur ────────────────────────────────────────────────────────────

async def run_and_persist_insights(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> List[Insight]:
    """
    Exécute l'Insight Engine sur les 7 derniers DailyMetrics et persiste les résultats.

    Upsert : si un insight (user, date, catégorie, titre) existe déjà,
    le message et les données probantes sont mis à jour.
    Les insights expirent après INSIGHT_EXPIRY_DAYS jours.
    """
    cutoff_7d = target_date - timedelta(days=7)
    cutoff_28d = target_date - timedelta(days=28)

    # Métriques 7 jours (fenêtre courte)
    res_7d = await db.execute(
        select(DailyMetrics)
        .where(and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.metrics_date >= cutoff_7d,
            DailyMetrics.metrics_date <= target_date,
        ))
        .order_by(DailyMetrics.metrics_date.desc())
    )
    metrics_7d = res_7d.scalars().all()

    if not metrics_7d:
        logger.info("run_and_persist_insights — aucune métrique 7j pour user=%s", user_id)
        return []

    # Métriques 28 jours (charge chronique pour ACWR)
    res_28d = await db.execute(
        select(DailyMetrics)
        .where(and_(
            DailyMetrics.user_id == user_id,
            DailyMetrics.metrics_date >= cutoff_28d,
            DailyMetrics.metrics_date <= target_date,
        ))
    )
    metrics_28d = res_28d.scalars().all()
    load_28d_total = sum((m.training_load or 0) for m in metrics_28d)
    training_load_28d = load_28d_total if load_28d_total > 0 else None

    # Exécution du moteur (fonctions pures)
    detected = run_insight_engine(metrics_7d, training_load_28d)

    expires_at = datetime.now(timezone.utc) + timedelta(days=INSIGHT_EXPIRY_DAYS)
    persisted: List[Insight] = []

    for d in detected:
        # Upsert par contrainte unique (user_id, insight_date, category, title)
        existing_res = await db.execute(
            select(Insight).where(and_(
                Insight.user_id == user_id,
                Insight.insight_date == target_date,
                Insight.category == d.category,
                Insight.title == d.title,
            ))
        )
        existing = existing_res.scalar_one_or_none()

        if existing:
            existing.message = d.message
            existing.data_evidence = d.data_evidence
            existing.action = d.action
            existing.expires_at = expires_at
            persisted.append(existing)
        else:
            insight = Insight(
                user_id=user_id,
                insight_date=target_date,
                category=d.category,
                severity=d.severity,
                title=d.title,
                message=d.message,
                action=d.action,
                data_evidence=d.data_evidence,
                expires_at=expires_at,
            )
            db.add(insight)
            persisted.append(insight)

    await db.flush()
    logger.info(
        "Insight Engine — user=%s date=%s détectés=%d persistés=%d",
        user_id, target_date, len(detected), len(persisted),
    )
    return persisted


# ── Mutations ───────────────────────────────────────────────────────────────────

async def mark_read(
    db: AsyncSession,
    insight_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[Insight]:
    """Marque un insight comme lu."""
    res = await db.execute(
        select(Insight).where(and_(Insight.id == insight_id, Insight.user_id == user_id))
    )
    insight = res.scalar_one_or_none()
    if insight:
        insight.is_read = True
    return insight


async def mark_dismissed(
    db: AsyncSession,
    insight_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[Insight]:
    """Acquitte un insight (et le marque comme lu)."""
    res = await db.execute(
        select(Insight).where(and_(Insight.id == insight_id, Insight.user_id == user_id))
    )
    insight = res.scalar_one_or_none()
    if insight:
        insight.is_dismissed = True
        insight.is_read = True
    return insight


# ── Builder réponse ─────────────────────────────────────────────────────────────

def build_insight_list_response(insights: List[Insight]) -> InsightListResponse:
    """Construit la réponse de liste d'insights avec métadonnées agrégées."""
    responses = [InsightResponse.model_validate(i) for i in insights]
    unread_count = sum(1 for i in insights if not i.is_read)
    critical_count = sum(1 for i in insights if i.severity == "critical")
    by_category = dict(Counter(i.category for i in insights))
    by_severity = dict(Counter(i.severity for i in insights))

    return InsightListResponse(
        insights=responses,
        total=len(insights),
        unread_count=unread_count,
        critical_count=critical_count,
        by_category=by_category,
        by_severity=by_severity,
    )
