"""
Modèle DailyMetrics — snapshot journalier agrégé (LOT 3).

Ce modèle centralise les métriques clés du jour pour :
  - Alimenter l'Insight Engine (détection patterns 7j)
  - Calculer le Longevity Score (régularité sur 30/90j)
  - Exposer un historique performant sans recalcul

Upsert quotidien par (user_id, metrics_date).
Les valeurs None signifient "donnée non disponible" (≠ 0).
"""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    ForeignKey, Boolean, Date, DateTime, Float, Integer, String,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class DailyMetrics(Base):
    """Snapshot journalier agrégé de toutes les métriques santé."""
    __tablename__ = "daily_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metrics_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # ── Corps ───────────────────────────────────────────────────────────────
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)

    # ── Nutrition ────────────────────────────────────────────────────────────
    calories_consumed: Mapped[Optional[float]] = mapped_column(Float)
    protein_g: Mapped[Optional[float]] = mapped_column(Float)
    carbs_g: Mapped[Optional[float]] = mapped_column(Float)
    fat_g: Mapped[Optional[float]] = mapped_column(Float)
    fiber_g: Mapped[Optional[float]] = mapped_column(Float)
    # Objectifs du jour (issus du profil ou du nutrition engine)
    calories_target: Mapped[Optional[float]] = mapped_column(Float)
    protein_target_g: Mapped[Optional[float]] = mapped_column(Float)
    meal_count: Mapped[Optional[int]] = mapped_column(Integer)

    # ── Hydratation ──────────────────────────────────────────────────────────
    hydration_ml: Mapped[Optional[int]] = mapped_column(Integer)
    hydration_target_ml: Mapped[Optional[int]] = mapped_column(Integer)

    # ── Activité ─────────────────────────────────────────────────────────────
    steps: Mapped[Optional[int]] = mapped_column(Integer)
    active_calories_kcal: Mapped[Optional[float]] = mapped_column(Float)
    distance_km: Mapped[Optional[float]] = mapped_column(Float)

    # ── Signaux physiologiques ───────────────────────────────────────────────
    resting_heart_rate_bpm: Mapped[Optional[float]] = mapped_column(Float)
    hrv_ms: Mapped[Optional[float]] = mapped_column(Float)

    # ── Sommeil ──────────────────────────────────────────────────────────────
    sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    sleep_score: Mapped[Optional[float]] = mapped_column(Float)
    sleep_quality_label: Mapped[Optional[str]] = mapped_column(String(20))

    # ── Entraînement ─────────────────────────────────────────────────────────
    workout_count: Mapped[int] = mapped_column(Integer, server_default="0")
    total_tonnage_kg: Mapped[Optional[float]] = mapped_column(Float)
    training_load: Mapped[Optional[float]] = mapped_column(Float)

    # ── Scores ───────────────────────────────────────────────────────────────
    readiness_score: Mapped[Optional[float]] = mapped_column(Float)
    longevity_score: Mapped[Optional[float]] = mapped_column(Float)

    # ── Méta ─────────────────────────────────────────────────────────────────
    # % de champs clés renseignés (poids, calories, sommeil, hydratation...)
    data_completeness_pct: Mapped[float] = mapped_column(Float, server_default="0.0")
    algorithm_version: Mapped[str] = mapped_column(String(10), server_default="v1.0", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "metrics_date", name="uq_daily_metrics_user_date"),
    )
