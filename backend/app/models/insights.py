"""
Modèle Insight — insights détectés automatiquement (LOT 3).

L'Insight Engine analyse les DailyMetrics sur 7 jours glissants
et génère des insights quand des patterns sont détectés :
  - Déficit protéique persistant
  - Déficit calorique excessif
  - Manque d'activité
  - Fatigue cumulée
  - Dette de sommeil
  - Déshydratation chronique
  - Risque de surentraînement

Un insight est unique par (user_id, insight_date, category, title).
Il expire après 7 jours par défaut si non acquitté.
"""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    ForeignKey, Boolean, Date, DateTime, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class Insight(Base):
    """Insight santé détecté automatiquement pour un utilisateur."""
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    insight_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # ── Classification ────────────────────────────────────────────────────────
    # nutrition | sleep | activity | recovery | training | hydration | weight
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # info | warning | critical
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # ── Contenu ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Action recommandée (courte phrase)
    action: Mapped[Optional[str]] = mapped_column(String(500))
    # Données brutes ayant déclenché l'insight (pour affichage dans l'UI)
    data_evidence: Mapped[Optional[dict]] = mapped_column(JSONB)

    # ── Statut ────────────────────────────────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    # Les insights expirent après 7 jours (configurable)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        # Un seul insight par catégorie × titre × jour pour éviter les doublons
        UniqueConstraint("user_id", "insight_date", "category", "title",
                         name="uq_insight_user_date_category_title"),
    )
