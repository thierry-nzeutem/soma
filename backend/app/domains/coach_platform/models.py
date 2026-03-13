"""
SOMA LOT 17 — Coach Platform DB Models.

Tables:
  - coach_profiles       (profil coach professionnel)
  - athlete_profiles     (profil athlète lié à un user SOMA)
  - coach_athlete_links  (liaison many-to-many coach ↔ athlète)
  - training_programs    (programmes d'entraînement hiérarchiques, weeks JSONB)
  - athlete_notes        (notes coach sur athlète)
  - athlete_alerts       (alertes automatisées santé pour le dashboard)

Pattern:
  - UUIDMixin for pk, TimestampMixin for created_at/updated_at
  - JSONB for hierarchical data (weeks, exercises)
  - UniqueConstraint where appropriate
"""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    String, Float, Integer, Boolean, Date, DateTime, Text,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, UUIDMixin, TimestampMixin


class CoachProfileDB(Base, UUIDMixin, TimestampMixin):
    """
    Professional coach account profile.
    One per SOMA user (unique user_id).
    """
    __tablename__ = "coach_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Stored as JSONB list[str]
    specializations: Mapped[Optional[list]] = mapped_column(JSONB)
    certification: Mapped[Optional[str]] = mapped_column(String(200))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    max_athletes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class AthleteProfileDB(Base, UUIDMixin, TimestampMixin):
    """
    Athlete profile linked to a SOMA user account.
    One per SOMA user (unique user_id).
    """
    __tablename__ = "athlete_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    sport: Mapped[Optional[str]] = mapped_column(String(100))
    goal: Mapped[Optional[str]] = mapped_column(String(200))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class CoachAthleteLinkDB(Base, UUIDMixin, TimestampMixin):
    """
    Many-to-many link between coach and athlete.
    UniqueConstraint ensures one active link per (coach, athlete) pair.
    """
    __tablename__ = "coach_athlete_links"

    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    athlete_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    role: Mapped[str] = mapped_column(String(50), nullable=False, server_default="primary")
    # primary | secondary | observer
    linked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("coach_id", "athlete_id", name="uq_coach_athlete_link"),
    )


class TrainingProgramDB(Base, UUIDMixin, TimestampMixin):
    """
    Hierarchical training program assigned by a coach to an athlete.
    Weeks and workouts stored as JSONB for flexibility.
    """
    __tablename__ = "training_programs"

    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    # athlete_id nullable → template programs (assigned to no one yet)
    athlete_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False, server_default="4")
    sport_focus: Mapped[Optional[str]] = mapped_column(String(100))
    difficulty: Mapped[Optional[str]] = mapped_column(String(50))
    # easy | medium | hard | elite
    # Weeks + workouts stored hierarchically as JSONB
    weeks: Mapped[Optional[list]] = mapped_column(JSONB)
    # list[{week_number, theme, target_volume, workouts[{day_of_week, name, ...}]}]
    is_template: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class AthleteNoteDB(Base, UUIDMixin, TimestampMixin):
    """
    Coach observation/note written about an athlete.
    """
    __tablename__ = "athlete_notes"

    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    athlete_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    note_date: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="general"
    )
    # general | nutrition | recovery | performance | injury | mental
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    __table_args__ = (
        Index("ix_athlete_notes_coach_athlete", "coach_id", "athlete_id"),
    )


class AthleteAlertDB(Base, UUIDMixin, TimestampMixin):
    """
    Automated health alert generated for the coach dashboard.
    Stores unresolved alerts; resolved_at tracks when coach dismissed them.
    """
    __tablename__ = "athlete_alerts"

    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    athlete_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    # injury_risk | overtraining | low_readiness | poor_recovery | inactivity
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    # critical | warning | info
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(Float)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_athlete_alerts_coach_athlete", "coach_id", "athlete_id"),
    )
