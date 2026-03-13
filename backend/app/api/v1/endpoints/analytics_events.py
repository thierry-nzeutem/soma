"""Endpoint Analytics Events — LOT 18.

POST /analytics/event : enregistre un événement produit côté client.

Ce endpoint est fire-and-forget : toujours 201, même si le DB est down.
Utilisé par l'app mobile pour tracker les événements utilisateur.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.core.analytics import track_event

logger = logging.getLogger(__name__)

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Schémas ───────────────────────────────────────────────────────────────────

class TrackEventRequest(BaseModel):
    """Requête de tracking d'un événement produit."""
    event_name: str = Field(
        ...,
        max_length=100,
        description="Nom de l'événement (ex: 'morning_briefing_view').",
        examples=["morning_briefing_view"],
    )
    properties: Optional[dict] = Field(
        None,
        description="Propriétés additionnelles (JSON libre, nullable).",
    )


class TrackEventResponse(BaseModel):
    """Réponse de confirmation (toujours 'tracked')."""
    status: str = "tracked"


# ── POST /analytics/event ─────────────────────────────────────────────────────

@analytics_router.post(
    "/event",
    response_model=TrackEventResponse,
    status_code=201,
    summary="Tracker un événement produit",
)
async def track_user_event(
    body: TrackEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enregistre un événement produit utilisateur.

    Fire-and-forget : retourne toujours 201, même en cas d'erreur DB.
    L'app mobile utilise ce endpoint pour les analytics (DAU, rétention, funnel).

    Exemples d'événements reconnus :
      - `app_open`, `morning_briefing_view`, `journal_entry`
      - `coach_question`, `workout_logged`, `nutrition_logged`
      - `insight_viewed`, `onboarding_complete`, `quick_advice_requested`
      - `biomarker_viewed`, `twin_viewed`, `biological_age_viewed`
    """
    await track_event(db, current_user.id, body.event_name, body.properties)
    return TrackEventResponse(status="tracked")
