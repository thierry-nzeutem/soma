"""Schéma HomeSummary — agrégateur de démarrage mobile (LOT 5)."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel
import uuid


class HomeSummaryMetrics(BaseModel):
    """Sous-ensemble des métriques du jour pour la vue home."""
    metrics_date: date
    weight_kg: Optional[float] = None
    calories_consumed: Optional[float] = None
    calories_target: Optional[float] = None
    protein_g: Optional[float] = None
    protein_target_g: Optional[float] = None
    hydration_ml: Optional[int] = None
    hydration_target_ml: Optional[int] = None
    steps: Optional[int] = None
    sleep_minutes: Optional[int] = None
    sleep_quality_label: Optional[str] = None
    hrv_ms: Optional[float] = None
    workout_count: int = 0
    readiness_score: Optional[float] = None
    data_completeness_pct: float = 0.0


class HomeSummaryReadiness(BaseModel):
    """Score de récupération résumé."""
    overall_readiness: Optional[float] = None
    recommended_intensity: Optional[str] = None
    readiness_level: Optional[str] = None  # excellent | good | fair | poor


class HomeSummaryInsight(BaseModel):
    """Insight non lu pour affichage dans la home."""
    id: uuid.UUID
    category: str
    severity: str
    message: str


class HomeSummaryPlan(BaseModel):
    """Plan santé du jour résumé."""
    readiness_level: str
    recommended_intensity: str
    protein_target_g: float
    calorie_target: float
    steps_goal: int
    workout_recommendation: Dict[str, Any]
    daily_tips: List[str] = []
    alerts: List[Dict[str, str]] = []
    from_cache: bool = False


class HomeSummaryLongevity(BaseModel):
    """Score longévité résumé."""
    longevity_score: Optional[float] = None
    biological_age_estimate: Optional[float] = None


class HomeSummaryResponse(BaseModel):
    """
    Agrégateur de démarrage de l'app mobile.

    Remplace 5 appels API en 1 seul :
      - GET /metrics/daily
      - GET /scores/readiness/today
      - GET /insights?unread=true
      - GET /health/plan/today
      - GET /scores/longevity (optionnel)
    """
    summary_date: date
    generated_at: datetime

    metrics: Optional[HomeSummaryMetrics] = None
    readiness: Optional[HomeSummaryReadiness] = None
    unread_insights: List[HomeSummaryInsight] = []
    plan: Optional[HomeSummaryPlan] = None
    longevity: Optional[HomeSummaryLongevity] = None

    # Méta
    unread_insights_count: int = 0
    has_active_plan: bool = False
