import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import ForeignKey, String, Boolean, DateTime, func, Float, Integer, Text, ARRAY, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, TimestampMixin, UUIDMixin


class HealthDataSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "health_data_sources"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # apple_health, google_health, garmin
    source_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    permissions_granted: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)


class HealthImportJob(Base, UUIDMixin):
    __tablename__ = "health_import_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    job_type: Mapped[str] = mapped_column(String(50))  # full_sync, incremental
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, success, failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    records_imported: Mapped[Optional[int]] = mapped_column(Integer)
    records_skipped: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HealthSample(Base, UUIDMixin):
    """Données de santé agrégées (pas, FC, HRV, VO2max, etc.)"""
    __tablename__ = "health_samples"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sample_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # steps, heart_rate, hrv, spo2, active_calories, resting_heart_rate,
    # vo2_max, stand_hours, respiratory_rate, body_temperature, distance
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    # count, bpm, ms, pct, kcal, ml/kg/min, °C, km, hours
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50))
    data_quality: Mapped[str] = mapped_column(String(20), default="exact")
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "sample_type", "recorded_at", "source", name="uq_health_samples_dedup"),
    )


class SleepSession(Base, UUIDMixin):
    __tablename__ = "sleep_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    deep_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    rem_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    light_sleep_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    awake_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    avg_heart_rate_bpm: Mapped[Optional[float]] = mapped_column(Float)
    avg_hrv_ms: Mapped[Optional[float]] = mapped_column(Float)
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[Optional[str]] = mapped_column(String(50))
    data_quality: Mapped[str] = mapped_column(String(20), default="exact")
    perceived_quality: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HydrationLog(Base, UUIDMixin):
    __tablename__ = "hydration_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    beverage_type: Mapped[str] = mapped_column(String(50), default="water")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
