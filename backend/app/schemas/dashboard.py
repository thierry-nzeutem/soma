"""Schémas Pydantic pour le dashboard SOMA — GET /api/v1/dashboard/today."""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel


class WeightSummary(BaseModel):
    current_kg: Optional[float]
    """Dernier poids mesuré disponible (peut dater de plusieurs jours)."""
    measured_at: Optional[datetime]
    """Date de la mesure du dernier poids."""
    delta_7d_kg: Optional[float]
    """Variation de poids sur les 7 derniers jours. None si données insuffisantes."""
    delta_direction: Optional[str]
    """'decreasing' | 'stable' | 'increasing'. None si données insuffisantes."""
    goal_kg: Optional[float]
    """Objectif de poids défini dans le profil."""
    gap_to_goal_kg: Optional[float]
    """Écart au goal. Négatif = en dessous du goal."""
    bmi_current: Optional[float]


class HydrationSummary(BaseModel):
    total_ml: int
    """Volume total consommé aujourd'hui."""
    target_ml: int
    """Objectif journalier."""
    pct: float
    """Pourcentage de l'objectif atteint (0-100+)."""
    status: str
    """'insufficient' | 'adequate' | 'optimal'"""
    entries_count: int


class SleepSummary(BaseModel):
    duration_minutes: Optional[int]
    """Durée de la nuit précédente."""
    duration_hours: Optional[float]
    sleep_score: Optional[int]
    """Score sommeil 0-100 (si disponible via source)."""
    perceived_quality: Optional[int]
    """Qualité perçue 1-5."""
    deep_sleep_minutes: Optional[int]
    rem_sleep_minutes: Optional[int]
    avg_hrv_ms: Optional[float]
    debt_minutes: Optional[int]
    """Dette de sommeil estimée vs objectif 8h. Positif = manque, négatif = surplus."""
    quality_label: str
    """'poor' | 'fair' | 'good' | 'excellent' | 'unknown'"""


class ActivitySummary(BaseModel):
    steps: Optional[float]
    steps_goal: int
    """Objectif de pas journalier (défaut 8000)."""
    steps_pct: Optional[float]
    active_calories_kcal: Optional[float]
    distance_km: Optional[float]
    stand_hours: Optional[float]
    resting_heart_rate_bpm: Optional[float]
    hrv_ms: Optional[float]
    vo2_max: Optional[float]
    today_workout: Optional[dict]
    """Séance du jour si elle existe (statut, type, durée, tonnage)."""


class NutritionSummary(BaseModel):
    calories_consumed: Optional[float]
    """Total calories ingérées aujourd'hui. None si aucune entrée."""
    calories_target: Optional[float]
    protein_g: Optional[float]
    protein_target_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fiber_g: Optional[float]
    meal_count: int
    fasting_active: bool
    """True si l'utilisateur est en fenêtre de jeûne."""
    fasting_hours_elapsed: Optional[float]
    """Heures écoulées depuis le dernier repas."""
    energy_balance_kcal: Optional[float]
    """Calories consommées - TDEE estimé. Positif = surplus, négatif = déficit."""


class RecoverySummary(BaseModel):
    readiness_score: Optional[float]
    """Score global de forme/récupération 0-100. V1 simplifié."""
    recovery_score: Optional[float]
    sleep_contribution: Optional[float]
    hrv_contribution: Optional[float]
    training_load_contribution: Optional[float]
    recommended_intensity: str
    """'rest' | 'light' | 'moderate' | 'normal' | 'push'"""
    confidence: float
    """Niveau de confiance du score 0-1 (dépend des données disponibles)."""
    reasoning: str
    """Explication courte du score."""


class DashboardAlert(BaseModel):
    type: str
    """'hydration' | 'sleep' | 'nutrition' | 'training' | 'recovery' | 'weight'"""
    severity: str
    """'info' | 'warning' | 'alert'"""
    message: str
    action: Optional[str]
    """Action suggérée courte."""


class DashboardRecommendation(BaseModel):
    category: str
    """'workout' | 'nutrition' | 'recovery' | 'hydration' | 'sleep'"""
    text: str
    priority: int
    """1 = plus important"""


class DataSourceMeta(BaseModel):
    has_weight: bool
    has_sleep: bool
    has_hrv: bool
    has_steps: bool
    has_nutrition: bool
    has_workout_today: bool
    data_freshness_hours: Optional[float]
    """Fraîcheur de la donnée la plus récente disponible."""
    profile_completeness_pct: Optional[float]


class DashboardResponse(BaseModel):
    """Réponse complète du dashboard journalier SOMA."""
    date: str
    """Date du dashboard (YYYY-MM-DD)."""

    # ─── Sections principales ───────────────────────────────────────────────────
    body: WeightSummary
    hydration: HydrationSummary
    sleep: SleepSummary
    activity: ActivitySummary
    nutrition: NutritionSummary
    recovery: RecoverySummary

    # ─── Alertes et recommandations ─────────────────────────────────────────────
    alerts: List[DashboardAlert]
    recommendations: List[DashboardRecommendation]

    # ─── Méta ───────────────────────────────────────────────────────────────────
    metadata: DataSourceMeta
    generated_at: datetime
