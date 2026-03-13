"""Schémas Pydantic v2 — DailyMetrics (LOT 3)."""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
import uuid


class DailyMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    metrics_date: date

    # Corps
    weight_kg: Optional[float] = None

    # Nutrition
    calories_consumed: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    calories_target: Optional[float] = None
    protein_target_g: Optional[float] = None
    meal_count: Optional[int] = None

    # Hydratation
    hydration_ml: Optional[int] = None
    hydration_target_ml: Optional[int] = None

    # Activité
    steps: Optional[int] = None
    active_calories_kcal: Optional[float] = None
    distance_km: Optional[float] = None

    # Signaux physiologiques
    resting_heart_rate_bpm: Optional[float] = None
    hrv_ms: Optional[float] = None

    # Sommeil
    sleep_minutes: Optional[int] = None
    sleep_score: Optional[float] = None
    sleep_quality_label: Optional[str] = None

    # Entraînement
    workout_count: int = 0
    total_tonnage_kg: Optional[float] = None
    training_load: Optional[float] = None

    # Scores
    readiness_score: Optional[float] = None
    longevity_score: Optional[float] = None

    # Méta
    data_completeness_pct: float = 0.0
    algorithm_version: str = "v1.0"
    created_at: datetime
    updated_at: datetime


class DailyMetricsHistoryResponse(BaseModel):
    """Historique des métriques sur N jours."""
    history: List[DailyMetricsResponse]
    days_requested: int
    days_available: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    # Tendances calculées sur la période
    avg_readiness: Optional[float] = None
    avg_sleep_hours: Optional[float] = None
    avg_calories: Optional[float] = None
    avg_steps: Optional[int] = None
    avg_protein_g: Optional[float] = None
    weight_trend_kg: Optional[float] = None   # delta début → fin de période
    workout_frequency_pct: Optional[float] = None  # % jours avec séance


class NutritionTargetsResponse(BaseModel):
    """Réponse du Nutrition Engine — besoins personnalisés du jour."""

    # Cibles du jour
    calories_target: float
    protein_target_g: float
    carbs_target_g: float
    fat_target_g: float
    fiber_target_g: float
    hydration_target_ml: float

    # Répartition macros (%)
    protein_pct: float     # % de l'énergie totale en protéines
    carbs_pct: float
    fat_pct: float

    # Contexte
    base_tdee_kcal: float
    workout_bonus_kcal: float      # calories supplémentaires pour l'entraînement du jour
    goal_adjustment_kcal: float    # surplus (gain) ou déficit (perte)
    target_mode: str               # standard | training_day | rest_day | fasting

    # Timing (si jeûne intermittent actif)
    eating_window_hours: Optional[float] = None
    fasting_start_at: Optional[str] = None   # "20:00"

    # Reasoning
    reasoning: str


class MicronutrientDetail(BaseModel):
    """Détail d'un micronutriment."""
    name: str
    name_fr: str
    consumed: Optional[float] = None     # quantité consommée (unité spécifique)
    target: float                         # apport journalier recommandé
    unit: str                             # mcg, mg, g
    pct_of_target: Optional[float] = None # % de l'objectif atteint
    status: str                           # sufficient | low | deficient | unknown
    food_sources: List[str] = []          # aliments riches en ce nutriment


class MicronutrientAnalysisResponse(BaseModel):
    """Analyse micronutritionnelle du jour."""
    date: str
    overall_micro_score: float = Field(..., ge=0, le=100)  # 0-100
    micronutrients: List[MicronutrientDetail]
    top_deficiencies: List[str]           # liste des noms en déficit
    data_quality: str                     # good | partial | estimated
    # % d'entrées avec données micronutrients
    entries_with_micro_data_pct: float
    analysis_note: str
