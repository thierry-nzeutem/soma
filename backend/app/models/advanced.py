"""
Advanced health engine models — LOT 11.

Tables:
  - digital_twin_snapshots      (Digital Twin V2)
  - biological_age_snapshots    (Biological Age Engine)
  - motion_intelligence_snapshots (Motion Intelligence)

Pattern:
  - JSONB for components/profiles (avoids excessive columns, flexible schema evolution)
  - UniqueConstraint(user_id, snapshot_date) — one snapshot per user per day
  - UUIDMixin for pk, TimestampMixin for created_at/updated_at
"""
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Integer, Boolean, Date, DateTime, func, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, UUIDMixin, TimestampMixin


class DigitalTwinSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Digital Twin V2 daily snapshot.
    Stores per-component scores as JSONB for full explainability.
    Each component dict: {value, status, confidence, explanation, variables_used[]}
    """
    __tablename__ = "digital_twin_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Per-component scores (JSONB — dict[str, TwinComponentDict])
    components: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Keys: energy_balance, glycogen, carb_availability, protein_status, hydration,
    #       fatigue, inflammation, sleep_debt, recovery_capacity, training_readiness,
    #       stress_load, metabolic_flexibility

    # Synthesis
    overall_status: Mapped[Optional[str]] = mapped_column(String(20))
    # fresh | good | moderate | tired | critical
    primary_concern: Mapped[Optional[str]] = mapped_column(Text)
    global_confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Risk flags
    plateau_risk: Mapped[Optional[bool]] = mapped_column(Boolean)
    under_recovery_risk: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Recommendations list (JSONB array of strings)
    recommendations: Mapped[Optional[list]] = mapped_column(JSONB)

    algorithm_version: Mapped[str] = mapped_column(String(10), server_default="v1.0", nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_digital_twin_user_date"),
    )


class BiologicalAgeSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Biological Age Engine daily snapshot.
    Stores computed biological age and contributing factors.
    """
    __tablename__ = "biological_age_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Core results
    chronological_age: Mapped[Optional[int]] = mapped_column(Integer)
    biological_age: Mapped[Optional[float]] = mapped_column(Float)
    biological_age_delta: Mapped[Optional[float]] = mapped_column(Float)
    # delta = bio - chrono (negative = younger than chronological age)
    longevity_risk_score: Mapped[Optional[float]] = mapped_column(Float)  # 100 - longevity_score

    # Components and levers (JSONB for extensibility)
    components: Mapped[Optional[list]] = mapped_column(JSONB)
    # list[{factor_name, score, weight, age_delta_years, explanation}]
    levers: Mapped[Optional[list]] = mapped_column(JSONB)
    # list[{lever_id, title, description, potential_years_gained, difficulty, timeframe}]

    # Trend
    trend_direction: Mapped[Optional[str]] = mapped_column(String(20))
    # improving | stable | declining

    # Confidence
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    algorithm_version: Mapped[str] = mapped_column(String(10), server_default="v1.0", nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_bio_age_user_date"),
    )


class MotionIntelligenceSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Motion Intelligence aggregated snapshot.
    Captures movement health metrics from recent VisionSessions.
    """
    __tablename__ = "motion_intelligence_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Global scores (0-100)
    movement_health_score: Mapped[Optional[float]] = mapped_column(Float)
    stability_score: Mapped[Optional[float]] = mapped_column(Float)
    mobility_score: Mapped[Optional[float]] = mapped_column(Float)
    asymmetry_score: Mapped[Optional[float]] = mapped_column(Float)
    # asymmetry: 0=symmetric, 100=severe asymmetry

    # Trend
    overall_quality_trend: Mapped[Optional[str]] = mapped_column(String(20))
    # improving | stable | declining
    consecutive_quality_sessions: Mapped[Optional[int]] = mapped_column(Integer)

    # Metadata
    sessions_analyzed: Mapped[Optional[int]] = mapped_column(Integer)
    days_analyzed: Mapped[Optional[int]] = mapped_column(Integer)

    # Per-exercise profiles (JSONB)
    exercise_profiles: Mapped[Optional[dict]] = mapped_column(JSONB)
    # dict[exercise_type, ExerciseMotionProfileDict]

    # Recommendations
    recommendations: Mapped[Optional[list]] = mapped_column(JSONB)  # list[str]
    risk_alerts: Mapped[Optional[list]] = mapped_column(JSONB)       # list[str]

    confidence: Mapped[Optional[float]] = mapped_column(Float)

    algorithm_version: Mapped[str] = mapped_column(String(10), server_default="v1.0", nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_motion_user_date"),
    )
