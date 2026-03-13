"""
Modèle SQLAlchemy VisionSession — LOT 7 Computer Vision.

Stocke les résumés de sessions d'analyse par vision par ordinateur :
  - Exercice effectué, nombre de répétitions, durée
  - Scores biomécaniques V1 (amplitude, stabilité, régularité)
  - Rattachement optionnel à une WorkoutSession
"""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Date, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VisionSession(Base):
    __tablename__ = "vision_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Exercice ───────────────────────────────────────────────────────────────
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Métriques de performance ───────────────────────────────────────────────
    rep_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── Scores biomécaniques [0-100] ───────────────────────────────────────────
    amplitude_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    regularity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Rattachement workout ───────────────────────────────────────────────────
    workout_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Métadonnées libres ─────────────────────────────────────────────────────
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ── Versioning ─────────────────────────────────────────────────────────────
    algorithm_version: Mapped[str] = mapped_column(
        String(10), nullable=False, default="v1.0"
    )

    # ── Temporel ───────────────────────────────────────────────────────────────
    session_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        server_default=text("CURRENT_DATE"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
