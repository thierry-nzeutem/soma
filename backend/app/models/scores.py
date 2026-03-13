import uuid
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy import ForeignKey, String, DateTime, func, Float, Integer, Text, ARRAY, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, UUIDMixin


class MetabolicStateSnapshot(Base, UUIDMixin):
    """Jumeau métabolique numérique - Module O"""
    __tablename__ = "metabolic_state_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Métabolisme
    estimated_bmr_kcal: Mapped[Optional[float]] = mapped_column(Float)
    estimated_tdee_kcal: Mapped[Optional[float]] = mapped_column(Float)

    # Glycogène (estimation)
    estimated_glycogen_g: Mapped[Optional[float]] = mapped_column(Float)
    glycogen_status: Mapped[Optional[str]] = mapped_column(String(20))  # depleted, low, normal, high

    # État
    fatigue_score: Mapped[Optional[float]] = mapped_column(Float)      # 0-100
    recovery_score: Mapped[Optional[float]] = mapped_column(Float)     # 0-100
    readiness_score: Mapped[Optional[float]] = mapped_column(Float)    # 0-100
    training_load_7d: Mapped[Optional[float]] = mapped_column(Float)
    training_load_28d: Mapped[Optional[float]] = mapped_column(Float)
    energy_availability_kcal: Mapped[Optional[float]] = mapped_column(Float)

    # Estimations avancées (Module T)
    estimated_glucose_mg_dl: Mapped[Optional[float]] = mapped_column(Float)
    estimated_cortisol_level: Mapped[Optional[float]] = mapped_column(Float)   # relatif 0-100
    estimated_neural_fatigue: Mapped[Optional[float]] = mapped_column(Float)   # 0-100
    injury_risk_score: Mapped[Optional[float]] = mapped_column(Float)           # 0-100
    hormonal_balance_signal: Mapped[Optional[str]] = mapped_column(String(20))
    # optimal, stress, underrecovery, underfed

    # Méta
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    variables_used: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    sleep_quality_input: Mapped[Optional[float]] = mapped_column(Float)
    hrv_input: Mapped[Optional[float]] = mapped_column(Float)
    resting_hr_input: Mapped[Optional[float]] = mapped_column(Float)
    training_load_input: Mapped[Optional[float]] = mapped_column(Float)
    nutrition_input: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_metabolic_user_date"),
    )


class ReadinessScore(Base, UUIDMixin):
    """Score de forme et récupération journalier"""
    __tablename__ = "readiness_scores"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)

    sleep_score: Mapped[Optional[float]] = mapped_column(Float)
    recovery_score: Mapped[Optional[float]] = mapped_column(Float)
    training_load_score: Mapped[Optional[float]] = mapped_column(Float)
    hrv_score: Mapped[Optional[float]] = mapped_column(Float)
    nutrition_score: Mapped[Optional[float]] = mapped_column(Float)
    hydration_score: Mapped[Optional[float]] = mapped_column(Float)
    overall_readiness: Mapped[Optional[float]] = mapped_column(Float)

    recommended_intensity: Mapped[Optional[str]] = mapped_column(String(20))
    # rest, light, moderate, normal, push

    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    variables_used: Mapped[Optional[dict]] = mapped_column(JSONB)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)

    algorithm_version: Mapped[str] = mapped_column(String(10), server_default="v1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "score_date", name="uq_readiness_user_date"),
    )


class LongevityScore(Base, UUIDMixin):
    """Score de longévité multi-dimensionnel - Module Q"""
    __tablename__ = "longevity_scores"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)

    cardio_score: Mapped[Optional[float]] = mapped_column(Float)
    strength_score: Mapped[Optional[float]] = mapped_column(Float)
    sleep_score: Mapped[Optional[float]] = mapped_column(Float)
    nutrition_score: Mapped[Optional[float]] = mapped_column(Float)
    weight_score: Mapped[Optional[float]] = mapped_column(Float)
    body_comp_score: Mapped[Optional[float]] = mapped_column(Float)
    consistency_score: Mapped[Optional[float]] = mapped_column(Float)

    longevity_score: Mapped[Optional[float]] = mapped_column(Float)       # 0-100
    biological_age_estimate: Mapped[Optional[float]] = mapped_column(Float)
    trend_30d: Mapped[Optional[float]] = mapped_column(Float)
    trend_90d: Mapped[Optional[float]] = mapped_column(Float)
    top_improvement_levers: Mapped[Optional[dict]] = mapped_column(JSONB)

    algorithm_version: Mapped[str] = mapped_column(String(10), server_default="v1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "score_date", name="uq_longevity_user_date"),
    )


class DailyRecommendation(Base, UUIDMixin):
    """Recommandations IA journalières - Module R"""
    __tablename__ = "daily_recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_date: Mapped[date] = mapped_column(Date, nullable=False)

    morning_briefing: Mapped[Optional[str]] = mapped_column(Text)
    daily_plan: Mapped[Optional[dict]] = mapped_column(JSONB)
    workout_recommendation: Mapped[Optional[dict]] = mapped_column(JSONB)
    nutrition_strategy: Mapped[Optional[dict]] = mapped_column(JSONB)
    hydration_target_ml: Mapped[Optional[int]] = mapped_column(Integer)
    alerts: Mapped[Optional[dict]] = mapped_column(JSONB)
    evening_summary: Mapped[Optional[str]] = mapped_column(Text)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    reasoning: Mapped[Optional[dict]] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "recommendation_date", name="uq_daily_rec_user_date"),
    )
