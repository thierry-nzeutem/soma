"""SOMA LOT 14 — Coach Platform Pydantic schemas."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class CoachProfileCreate(BaseModel):
    name: str
    specializations: list[str] = Field(default_factory=list)
    certification: Optional[str] = None
    bio: Optional[str] = None
    max_athletes: int = Field(default=50, ge=1, le=500)


class CoachProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    specializations: list[str]
    certification: Optional[str]
    bio: Optional[str]
    max_athletes: int
    is_active: bool
    athlete_count: int = 0


class AthleteCreate(BaseModel):
    user_id: str
    display_name: str
    sport: Optional[str] = None
    goal: Optional[str] = None
    date_of_birth: Optional[date] = None
    notes: Optional[str] = None


class AthleteResponse(BaseModel):
    id: str
    user_id: str
    display_name: str
    sport: Optional[str]
    goal: Optional[str]
    date_of_birth: Optional[str]
    notes: Optional[str]
    is_active: bool


class AthleteDashboardSummaryResponse(BaseModel):
    athlete_id: str
    athlete_name: str
    snapshot_date: str
    readiness_score: Optional[float]
    fatigue_score: Optional[float]
    injury_risk_score: Optional[float]
    biological_age_delta: Optional[float]
    movement_health_score: Optional[float]
    nutrition_compliance: Optional[float]
    sleep_quality: Optional[float]
    training_load_this_week: Optional[float]
    acwr: Optional[float]
    days_since_last_session: Optional[int]
    active_alerts: list[str]
    risk_level: str = Field(description="green|yellow|orange|red")


class ProgramWorkoutCreate(BaseModel):
    day_of_week: int = Field(ge=1, le=7)
    name: str
    workout_type: str
    duration_minutes: int = Field(ge=5, le=300)
    intensity: str
    exercises: list[dict] = Field(default_factory=list)
    notes: Optional[str] = None


class ProgramWeekCreate(BaseModel):
    week_number: int = Field(ge=1)
    theme: str
    target_volume: str
    workouts: list[ProgramWorkoutCreate] = Field(default_factory=list)


class TrainingProgramCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_weeks: int = Field(ge=1, le=52)
    sport_focus: str
    difficulty: str
    is_template: bool = False
    weeks: list[ProgramWeekCreate] = Field(default_factory=list)


class TrainingProgramResponse(BaseModel):
    id: str
    coach_id: str
    name: str
    description: Optional[str]
    duration_weeks: int
    sport_focus: str
    difficulty: str
    is_template: bool
    weeks: list[dict]


class AthleteNoteCreate(BaseModel):
    athlete_id: str
    content: str
    category: str = "general"
    is_private: bool = True


class AthleteNoteResponse(BaseModel):
    id: str
    coach_id: str
    athlete_id: str
    note_date: str
    content: str
    category: str
    is_private: bool


class AthleteAlertResponse(BaseModel):
    id: str
    athlete_id: str
    alert_type: str
    severity: str
    message: str
    generated_at: str
    is_acknowledged: bool
    metric_value: Optional[float]
    threshold_value: Optional[float]


class CoachAthletesOverviewResponse(BaseModel):
    coach_id: str
    total_athletes: int
    athletes_at_risk: int
    athletes_summary: list[AthleteDashboardSummaryResponse]
