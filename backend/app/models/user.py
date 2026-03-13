import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Float, Integer, Text, ARRAY, Date, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    # ── Subscription plan ─────────────────────────────────────────────
    plan_code: Mapped[str] = mapped_column(String(20), nullable=False, server_default="free", index=True)
    plan_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    billing_provider: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    plan_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    plan_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False)
    body_metrics: Mapped[List["BodyMetric"]] = relationship("BodyMetric", back_populates="user")


class UserProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    birth_date: Mapped[Optional[datetime]] = mapped_column(Date)
    sex: Mapped[Optional[str]] = mapped_column(String(10))  # 'male', 'female', 'other'
    height_cm: Mapped[Optional[float]] = mapped_column(Float)

    # Objectifs
    goal_weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    primary_goal: Mapped[Optional[str]] = mapped_column(String(50))  # weight_loss, muscle_gain, maintenance, performance, longevity
    physical_constraints: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))

    # Niveau
    activity_level: Mapped[Optional[str]] = mapped_column(String(20))  # sedentary, light, moderate, active, very_active
    fitness_level: Mapped[Optional[str]] = mapped_column(String(20))   # beginner, intermediate, advanced, athlete

    # Alimentation
    dietary_regime: Mapped[Optional[str]] = mapped_column(String(50))
    food_allergies: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    food_intolerances: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    intermittent_fasting: Mapped[bool] = mapped_column(Boolean, default=False)
    fasting_protocol: Mapped[Optional[str]] = mapped_column(String(50))  # 16:8, 23:1, OMAD
    meals_per_day: Mapped[int] = mapped_column(Integer, default=3)

    # Préférences timing
    preferred_training_time: Mapped[Optional[str]] = mapped_column(String(20))
    usual_wake_time: Mapped[Optional[datetime]] = mapped_column(Time)
    usual_sleep_time: Mapped[Optional[datetime]] = mapped_column(Time)

    # Ressenti
    avg_energy_level: Mapped[Optional[int]] = mapped_column(Integer)
    perceived_sleep_quality: Mapped[Optional[int]] = mapped_column(Integer)

    # Preferences
    theme_preference: Mapped[str] = mapped_column(String(10), default="system", server_default="system")
    locale: Mapped[str] = mapped_column(String(10), default="fr", server_default="fr")
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Paris", server_default="Europe/Paris")

    # Équipement
    home_equipment: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    gym_access: Mapped[bool] = mapped_column(Boolean, default=False)
    gym_equipment: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))

    # Champs calculés (dénormalisés)
    bmi: Mapped[Optional[float]] = mapped_column(Float)
    bmr_kcal: Mapped[Optional[float]] = mapped_column(Float)
    tdee_kcal: Mapped[Optional[float]] = mapped_column(Float)
    target_calories_kcal: Mapped[Optional[float]] = mapped_column(Float)
    target_protein_g: Mapped[Optional[float]] = mapped_column(Float)
    target_hydration_ml: Mapped[Optional[float]] = mapped_column(Float)
    profile_completeness_score: Mapped[Optional[float]] = mapped_column(Float)

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="profile")


class BodyMetric(Base, UUIDMixin):
    __tablename__ = "body_metrics"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    body_fat_pct: Mapped[Optional[float]] = mapped_column(Float)
    muscle_mass_kg: Mapped[Optional[float]] = mapped_column(Float)
    bone_mass_kg: Mapped[Optional[float]] = mapped_column(Float)
    visceral_fat_index: Mapped[Optional[float]] = mapped_column(Float)
    water_pct: Mapped[Optional[float]] = mapped_column(Float)
    metabolic_age: Mapped[Optional[int]] = mapped_column(Integer)
    trunk_fat_pct: Mapped[Optional[float]] = mapped_column(Float)
    trunk_muscle_pct: Mapped[Optional[float]] = mapped_column(Float)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float)
    hip_cm: Mapped[Optional[float]] = mapped_column(Float)
    neck_cm: Mapped[Optional[float]] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    data_quality: Mapped[str] = mapped_column(String(20), default="exact")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="body_metrics")
