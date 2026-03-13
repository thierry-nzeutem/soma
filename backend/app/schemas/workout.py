"""Schémas Pydantic pour le module workout (sessions, exercices, séries)."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import uuid

from app.models.workout import SESSION_STATUS_VALUES


# ── Exercise Library ───────────────────────────────────────────────────────────

class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    name_fr: Optional[str]
    slug: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    primary_muscles: Optional[List[str]]
    secondary_muscles: Optional[List[str]]
    difficulty_level: Optional[str]
    equipment_required: Optional[List[str]]
    execution_location: Optional[str]
    description: Optional[str]
    met_value: Optional[float]
    format_type: Optional[str]
    cv_supported: bool


class ExerciseListResponse(BaseModel):
    exercises: List[ExerciseResponse]
    total: int


# ── Workout Sets ───────────────────────────────────────────────────────────────

class SetCreate(BaseModel):
    set_number: int = Field(..., ge=1)
    reps_target: Optional[int] = Field(None, ge=0)
    reps_actual: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    duration_seconds: Optional[int] = Field(None, ge=0)
    rest_seconds: Optional[int] = Field(None, ge=0)
    tempo: Optional[str] = None           # ex: '3-1-2'
    rpe_set: Optional[float] = Field(None, ge=1, le=10)
    is_warmup: bool = False
    data_source: str = Field("manual", pattern="^(manual|camera|estimated)$")
    notes: Optional[str] = None


class SetUpdate(BaseModel):
    reps_actual: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    duration_seconds: Optional[int] = Field(None, ge=0)
    rest_seconds: Optional[int] = Field(None, ge=0)
    rpe_set: Optional[float] = Field(None, ge=1, le=10)
    is_warmup: Optional[bool] = None
    is_pr: Optional[bool] = None
    range_of_motion_pct: Optional[float] = Field(None, ge=0, le=100)
    time_under_tension_s: Optional[float] = Field(None, ge=0)
    data_source: Optional[str] = None


class SetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    set_number: int
    reps_target: Optional[int]
    reps_actual: Optional[int]
    weight_kg: Optional[float]
    duration_seconds: Optional[int]
    rest_seconds: Optional[int]
    tempo: Optional[str]
    rpe_set: Optional[float]
    is_warmup: bool
    is_pr: bool
    data_source: str
    # Métriques avancées
    time_under_tension_s: Optional[float]
    range_of_motion_pct: Optional[float]
    created_at: datetime

    @property
    def tonnage_kg(self) -> Optional[float]:
        """Contribution au tonnage de cette série."""
        if self.reps_actual and self.weight_kg:
            return self.reps_actual * self.weight_kg
        return None


# ── Workout Exercises ──────────────────────────────────────────────────────────

class ExerciseEntryCreate(BaseModel):
    exercise_id: Optional[uuid.UUID] = None  # Peut être libre (exercice custom)
    exercise_order: int = Field(1, ge=1)
    notes: Optional[str] = None


class ExerciseEntryUpdate(BaseModel):
    exercise_order: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
    biomechanics_score: Optional[float] = Field(None, ge=0, le=100)


class ExerciseEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    exercise_id: Optional[uuid.UUID]
    exercise_order: int
    notes: Optional[str]
    biomechanics_score: Optional[float]
    sets: List[SetResponse]
    created_at: datetime

    # Champs calculés (non stockés, calculés à la volée)
    total_sets: Optional[int] = None
    total_reps: Optional[int] = None
    tonnage_kg: Optional[float] = None

    def model_post_init(self, __context) -> None:
        active_sets = [s for s in self.sets if not getattr(s, 'is_deleted', False)]
        self.total_sets = len(active_sets)
        self.total_reps = sum(s.reps_actual or 0 for s in active_sets)
        self.tonnage_kg = sum(
            (s.reps_actual or 0) * (s.weight_kg or 0)
            for s in active_sets
            if s.reps_actual and s.weight_kg
        ) or None


# ── Workout Sessions ───────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    started_at: Optional[datetime] = None   # défaut = now()
    session_type: str = Field(..., min_length=1)
    # strength|cardio|hiit|mobility|walk|elliptical|yoga|swimming|bodyweight|mat
    location: Optional[str] = Field(None, pattern="^(gym|home|outdoor|other)$")
    status: str = Field("in_progress", pattern="^(planned|in_progress|completed|skipped|cancelled)$")
    notes: Optional[str] = None
    energy_before: Optional[int] = Field(None, ge=1, le=10)


class SessionUpdate(BaseModel):
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    session_type: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(planned|in_progress|completed|skipped|cancelled)$")
    location: Optional[str] = None
    notes: Optional[str] = None
    rpe_score: Optional[float] = Field(None, ge=1, le=10)
    energy_before: Optional[int] = Field(None, ge=1, le=10)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    perceived_difficulty: Optional[int] = Field(None, ge=1, le=10)
    distance_km: Optional[float] = Field(None, ge=0)
    avg_heart_rate_bpm: Optional[float] = Field(None, ge=30, le=250)
    max_heart_rate_bpm: Optional[float] = Field(None, ge=30, le=250)
    calories_burned_kcal: Optional[float] = Field(None, ge=0)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    session_type: Optional[str]
    status: str
    location: Optional[str]
    # Résumé volume
    total_tonnage_kg: Optional[float]
    total_sets: Optional[int]
    total_reps: Optional[int]
    # Cardio
    distance_km: Optional[float]
    avg_heart_rate_bpm: Optional[float]
    max_heart_rate_bpm: Optional[float]
    calories_burned_kcal: Optional[float]
    # Charge
    internal_load_score: Optional[float]
    rpe_score: Optional[float]
    # Ressenti
    energy_before: Optional[int]
    energy_after: Optional[int]
    perceived_difficulty: Optional[int]
    technical_score: Optional[float]
    notes: Optional[str]
    is_completed: bool
    created_at: datetime


class SessionDetailResponse(SessionResponse):
    """Session avec exercices et séries imbriqués."""
    exercises: List[ExerciseEntryResponse] = []


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
    page: int
    per_page: int


# ── Session Summary ────────────────────────────────────────────────────────────

class MuscleGroupVolume(BaseModel):
    muscle_group: str
    total_sets: int
    total_reps: int
    tonnage_kg: float


class SessionSummary(BaseModel):
    session_id: uuid.UUID
    date: str
    duration_minutes: Optional[int]
    session_type: Optional[str]
    status: str
    # Volume global
    total_exercises: int
    total_sets: int
    total_reps: int
    total_tonnage_kg: float
    avg_rpe: Optional[float]
    # Cardio
    distance_km: Optional[float]
    calories_burned_kcal: Optional[float]
    # Charge d'entraînement
    internal_load_score: Optional[float]  # durée × RPE
    # Volume par groupe musculaire
    volume_by_muscle_group: List[MuscleGroupVolume]
    # PRs
    personal_records: List[dict]
    # Résumé textuel
    summary_text: str
