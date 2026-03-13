"""Modèle SQLAlchemy api_metrics — LOT 19.

Table api_metrics :
  - Enregistre les performances de chaque requête API.
  - Remplie par MetricsMiddleware (buffer in-memory → flush périodique).
  - Pas de FK stricte (graceful — même pattern que analytics_events).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, UUIDMixin


class ApiMetricDB(Base, UUIDMixin):
    """Enregistrement d'une requête API avec son temps de réponse."""

    __tablename__ = "api_metrics"

    # Path de l'endpoint (ex: /api/v1/daily/briefing)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Méthode HTTP (GET, POST, PATCH, DELETE)
    method: Mapped[str] = mapped_column(String(10), nullable=False)

    # Temps de réponse en millisecondes
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Code de statut HTTP
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Horodatage UTC
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
