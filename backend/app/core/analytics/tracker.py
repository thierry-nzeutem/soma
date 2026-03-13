"""Analytics tracker — LOT 18.

Responsabilité unique : persister les événements produit de manière
fire-and-forget (jamais bloquant, silencieux en cas d'erreur).

Utilisation :
    from app.core.analytics import track_event
    await track_event(db, user.id, "morning_briefing_view", {"date": "2026-03-08"})
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEventDB

logger = logging.getLogger(__name__)

# Noms d'événements reconnus (extensible)
EVENTS = {
    "app_open",
    "morning_briefing_view",
    "journal_entry",
    "coach_question",
    "workout_logged",
    "nutrition_logged",
    "insight_viewed",
    "onboarding_complete",
    "quick_advice_requested",
    "biomarker_viewed",
    "twin_viewed",
    "biological_age_viewed",
}


async def track_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    event_name: str,
    properties: Optional[dict] = None,
) -> None:
    """Persiste un événement analytics.

    Fire-and-forget : jamais bloquant, silencieux en cas d'erreur DB.
    L'appelant n'a PAS besoin de gérer le résultat ou les exceptions.

    Args:
        db: Session SQLAlchemy async (ne fait PAS de flush global).
        user_id: UUID de l'utilisateur.
        event_name: Nom de l'événement (idéalement dans EVENTS).
        properties: Dictionnaire optionnel de propriétés additionnelles.
    """
    try:
        event = AnalyticsEventDB(
            user_id=user_id,
            event_name=event_name[:100],  # tronqué à 100 chars
            properties=properties or None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        # Silencieux — ne pas propager l'erreur analytics au flow principal
        logger.debug("analytics track_event failed (silent)", event=event_name, error=str(exc))
