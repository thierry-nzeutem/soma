"""Analytics event model — LOT 18.

Table analytics_events :
  - Stocke les événements produit utilisateur.
  - Fire-and-forget, pas de foreign key stricte sur user_id (graceful).
  - JSONB pour les propriétés (schéma flexible).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, UUIDMixin


class AnalyticsEventDB(Base, UUIDMixin):
    """Événement produit persisté pour analytics usage."""

    __tablename__ = "analytics_events"

    # Identifiant utilisateur (pas de FK stricte pour ne pas bloquer si user supprimé)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Nom de l'événement (ex: "morning_briefing_view", "coach_question")
    event_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Propriétés additionnelles (JSON libre, nullable)
    properties: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Horodatage (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_analytics_events_user_created", "user_id", "created_at"),
    )
