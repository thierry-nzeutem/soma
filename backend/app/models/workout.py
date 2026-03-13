import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import ForeignKey, String, Boolean, DateTime, func, Float, Integer, Text, ARRAY, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, UUIDMixin

# Valeurs valides pour WorkoutSession.status
SESSION_STATUS_VALUES = ("planned", "in_progress", "completed", "skipped", "cancelled")


class ExerciseLibrary(Base, UUIDMixin):
    """Bibliothèque d'exercices — Module E."""
    __tablename__ = "exercise_library"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_fr: Mapped[Optional[str]] = mapped_column(String(200))
    slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(50))  # strength, cardio, mobility, balance, hiit
    subcategory: Mapped[Optional[str]] = mapped_column(String(50))
    primary_muscles: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    secondary_muscles: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))  # beginner, intermediate, advanced
    equipment_required: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    execution_location: Mapped[Optional[str]] = mapped_column(String(20))  # gym, home, outdoor, any
    description: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    breathing_cues: Mapped[Optional[str]] = mapped_column(Text)
    common_errors: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    image_urls: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    easier_variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    harder_variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    key_joint_angles: Mapped[Optional[dict]] = mapped_column(JSONB)
    cv_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    rep_detection_model: Mapped[Optional[str]] = mapped_column(String(50))
    contraindications: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    met_value: Mapped[Optional[float]] = mapped_column(Float)
    format_type: Mapped[Optional[str]] = mapped_column(String(20))  # reps | duration | distance
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkoutSession(Base, UUIDMixin):
    """Session d'entraînement — Module G."""
    __tablename__ = "workout_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    session_type: Mapped[Optional[str]] = mapped_column(String(50))
    # strength | cardio | hiit | mobility | walk | elliptical | yoga | swimming | bodyweight | mat

    # --- AJOUT LOT 1 : statut de la séance et soft delete ---
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned", server_default="planned")
    # planned | in_progress | completed | skipped | cancelled
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    location: Mapped[Optional[str]] = mapped_column(String(50))  # gym, home, outdoor

    # Volume (recalculé à chaque ajout de set)
    total_tonnage_kg: Mapped[Optional[float]] = mapped_column(Float)
    total_sets: Mapped[Optional[int]] = mapped_column(Integer)
    total_reps: Mapped[Optional[int]] = mapped_column(Integer)

    # Cardio
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    avg_heart_rate_bpm: Mapped[Optional[float]] = mapped_column(Float)
    max_heart_rate_bpm: Mapped[Optional[float]] = mapped_column(Float)
    calories_burned_kcal: Mapped[Optional[float]] = mapped_column(Float)

    # Charge d'entraînement
    internal_load_score: Mapped[Optional[float]] = mapped_column(Float)   # durée × RPE
    rpe_score: Mapped[Optional[float]] = mapped_column(Float)              # 1-10

    # Ressenti
    energy_before: Mapped[Optional[int]] = mapped_column(Integer)          # 1-10
    energy_after: Mapped[Optional[int]] = mapped_column(Integer)
    perceived_difficulty: Mapped[Optional[int]] = mapped_column(Integer)
    technical_score: Mapped[Optional[float]] = mapped_column(Float)        # score qualité technique (CV)

    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    exercises: Mapped[List["WorkoutExercise"]] = relationship(
        "WorkoutExercise",
        back_populates="session",
        order_by="WorkoutExercise.exercise_order",
        primaryjoin="and_(WorkoutExercise.session_id == WorkoutSession.id, WorkoutExercise.is_deleted == False)",
    )


class WorkoutExercise(Base, UUIDMixin):
    """Exercice dans une session d'entraînement."""
    __tablename__ = "workout_exercises"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    exercise_order: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    biomechanics_score: Mapped[Optional[float]] = mapped_column(Float)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    session: Mapped["WorkoutSession"] = relationship("WorkoutSession", back_populates="exercises", foreign_keys=[session_id])
    sets: Mapped[List["WorkoutSet"]] = relationship(
        "WorkoutSet",
        back_populates="exercise",
        order_by="WorkoutSet.set_number",
        primaryjoin="and_(WorkoutSet.workout_exercise_id == WorkoutExercise.id, WorkoutSet.is_deleted == False)",
    )


class WorkoutSet(Base, UUIDMixin):
    """Série dans un exercice."""
    __tablename__ = "workout_sets"

    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_target: Mapped[Optional[int]] = mapped_column(Integer)
    reps_actual: Mapped[Optional[int]] = mapped_column(Integer)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)   # Pour iso / cardio
    rest_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    tempo: Mapped[Optional[str]] = mapped_column(String(20))           # '3-1-2'
    time_under_tension_s: Mapped[Optional[float]] = mapped_column(Float)
    range_of_motion_pct: Mapped[Optional[float]] = mapped_column(Float)
    rpe_set: Mapped[Optional[float]] = mapped_column(Float)
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pr: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    data_source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | camera | estimated
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    exercise: Mapped["WorkoutExercise"] = relationship("WorkoutExercise", back_populates="sets", foreign_keys=[workout_exercise_id])
