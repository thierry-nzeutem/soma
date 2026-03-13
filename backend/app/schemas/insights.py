"""Schémas Pydantic v2 — Insights (LOT 3)."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
import uuid


class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    detected_at: datetime
    insight_date: date

    # Classification
    category: str   # nutrition | sleep | activity | recovery | training | hydration | weight
    severity: str   # info | warning | critical

    # Contenu
    title: str
    message: str
    action: Optional[str] = None
    data_evidence: Optional[Dict[str, Any]] = None

    # Statut
    is_read: bool = False
    is_dismissed: bool = False
    expires_at: Optional[datetime] = None

    created_at: datetime


class InsightListResponse(BaseModel):
    """Liste d'insights avec résumé."""
    insights: List[InsightResponse]
    total: int
    unread_count: int
    critical_count: int

    # Résumé par catégorie
    by_category: Dict[str, int] = {}    # {"nutrition": 2, "sleep": 1}
    by_severity: Dict[str, int] = {}    # {"warning": 2, "info": 1}


class InsightMarkReadRequest(BaseModel):
    """Marquer un ou plusieurs insights comme lus."""
    insight_ids: List[uuid.UUID] = Field(..., min_length=1)


class SupplementRecommendationResponse(BaseModel):
    """Suggestion de complément générée par le Supplement Engine."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    supplement_name: str
    goal: str
    reason: str
    observed_data_basis: Optional[str] = None
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    evidence_type: str   # data_observed | hypothesis | pattern

    # Dosage
    suggested_dose: Optional[str] = None
    suggested_timing: Optional[str] = None
    trial_duration_weeks: Optional[int] = None
    precautions: Optional[str] = None

    is_active: bool = True


class SupplementRecommendationsResponse(BaseModel):
    """Réponse complète du Supplement Engine."""
    recommendations: List[SupplementRecommendationResponse]
    total: int
    analysis_basis: str    # Résumé des données utilisées
    generated_at: datetime


class LongevityScoreResponse(BaseModel):
    """Score de longévité multi-dimensionnel."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    score_date: date

    # Composantes (0-100 chacune)
    cardio_score: Optional[float] = None
    strength_score: Optional[float] = None
    sleep_score: Optional[float] = None
    nutrition_score: Optional[float] = None
    weight_score: Optional[float] = None
    body_comp_score: Optional[float] = None
    consistency_score: Optional[float] = None

    # Score global
    longevity_score: Optional[float] = None      # 0-100
    biological_age_estimate: Optional[float] = None  # années

    # Tendances
    trend_30d: Optional[float] = None   # delta score sur 30j
    trend_90d: Optional[float] = None   # delta score sur 90j

    # Leviers d'amélioration
    top_improvement_levers: Optional[Dict[str, Any]] = None

    algorithm_version: str = "v1.0"
    created_at: datetime


class DailyHealthPlanResponse(BaseModel):
    """Plan santé journalier généré chaque matin."""
    date: str
    generated_at: datetime
    from_cache: bool = False  # True si servi depuis DailyRecommendation (cache 6h)

    # Séance recommandée
    workout_recommendation: Dict[str, Any]    # type, intensité, durée, notes

    # Objectifs du jour
    protein_target_g: float
    calorie_target: float
    hydration_target_ml: float
    steps_goal: int
    sleep_target_hours: float

    # Contexte récupération
    readiness_level: str      # excellent | good | fair | poor
    recommended_intensity: str

    # Alertes prioritaires (≤ 3)
    alerts: List[Dict[str, str]] = []

    # Conseils du jour (2-3 actions concrètes)
    daily_tips: List[str] = []

    # Fenêtre alimentaire (si jeûne)
    eating_window: Optional[Dict[str, Any]] = None

    # Micro-focus (un nutriment à surveiller)
    nutrition_focus: Optional[str] = None
