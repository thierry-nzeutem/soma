from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid


# --- Auth ---

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Profil ---

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=10, le=120)
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$")
    height_cm: Optional[float] = Field(None, ge=100, le=250)
    goal_weight_kg: Optional[float] = Field(None, ge=30, le=300)
    primary_goal: Optional[str] = Field(None, pattern="^(weight_loss|muscle_gain|maintenance|performance|longevity)$")
    activity_level: Optional[str] = Field(None, pattern="^(sedentary|light|moderate|active|very_active)$")
    fitness_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced|athlete)$")
    physical_constraints: Optional[List[str]] = None
    dietary_regime: Optional[str] = None
    food_allergies: Optional[List[str]] = None
    food_intolerances: Optional[List[str]] = None
    intermittent_fasting: Optional[bool] = None
    fasting_protocol: Optional[str] = None
    meals_per_day: Optional[int] = Field(None, ge=1, le=10)
    preferred_training_time: Optional[str] = None
    home_equipment: Optional[List[str]] = None
    gym_access: Optional[bool] = None
    gym_equipment: Optional[List[str]] = None
    avg_energy_level: Optional[int] = Field(None, ge=1, le=10)
    perceived_sleep_quality: Optional[int] = Field(None, ge=1, le=10)

    # Preferences
    theme_preference: Optional[str] = Field(None, pattern="^(light|dark|system)$")
    locale: Optional[str] = Field(None, pattern="^(fr|en)$")
    timezone: Optional[str] = Field(None, max_length=50)


class ComputedMetrics(BaseModel):
    bmi: Optional[float]
    bmr_kcal: Optional[float]
    tdee_kcal: Optional[float]
    target_calories_kcal: Optional[float]
    target_protein_g: Optional[float]
    protein_min_g: Optional[float] = None
    protein_max_g: Optional[float] = None
    target_hydration_ml: Optional[float]


class ProfileResponse(BaseModel):
    id: uuid.UUID
    first_name: Optional[str]
    age: Optional[int]
    sex: Optional[str]
    height_cm: Optional[float]
    goal_weight_kg: Optional[float]
    primary_goal: Optional[str]
    activity_level: Optional[str]
    fitness_level: Optional[str]
    dietary_regime: Optional[str]
    intermittent_fasting: bool
    fasting_protocol: Optional[str]
    meals_per_day: int
    home_equipment: Optional[List[str]]
    gym_access: bool
    avg_energy_level: Optional[int]
    perceived_sleep_quality: Optional[int]
    computed: Optional[ComputedMetrics]
    profile_completeness_score: Optional[float]

    # Preferences
    theme_preference: str = "system"
    locale: str = "fr"
    timezone: str = "Europe/Paris"

    model_config = ConfigDict(from_attributes=True)


# --- Métriques corporelles ---

class BodyMetricCreate(BaseModel):
    weight_kg: Optional[float] = Field(None, ge=20, le=500)
    body_fat_pct: Optional[float] = Field(None, ge=1, le=70)
    muscle_mass_kg: Optional[float] = Field(None, ge=10, le=200)
    bone_mass_kg: Optional[float] = Field(None, ge=0.5, le=10)
    visceral_fat_index: Optional[float] = Field(None, ge=1, le=59)
    water_pct: Optional[float] = Field(None, ge=20, le=80)
    metabolic_age: Optional[int] = Field(None, ge=10, le=120)
    trunk_fat_pct: Optional[float] = Field(None, ge=1, le=70)
    trunk_muscle_pct: Optional[float] = Field(None, ge=1, le=70)
    waist_cm: Optional[float] = Field(None, ge=40, le=200)
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class BodyMetricResponse(BaseModel):
    id: uuid.UUID
    measured_at: datetime
    weight_kg: Optional[float]
    body_fat_pct: Optional[float]
    muscle_mass_kg: Optional[float]
    bone_mass_kg: Optional[float] = None
    visceral_fat_index: Optional[float] = None
    water_pct: Optional[float] = None
    metabolic_age: Optional[int] = None
    trunk_fat_pct: Optional[float] = None
    trunk_muscle_pct: Optional[float] = None
    waist_cm: Optional[float]
    notes: Optional[str] = None
    source: str
    data_quality: str

    model_config = ConfigDict(from_attributes=True)


class BodyMetricsTrend(BaseModel):
    entries: List[BodyMetricResponse]
    trend: Optional[dict] = None  # {weight_slope_kg_per_week, direction}
    current_bmi: Optional[float]
