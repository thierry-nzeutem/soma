"""Schémas Pydantic v2 — scores journaliers (ReadinessScore, LOT 2)."""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
import uuid


class ReadinessScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    score_date: date

    # Composantes
    sleep_score: Optional[float] = None           # 0-100
    hrv_score: Optional[float] = None             # 0-100
    training_load_score: Optional[float] = None   # 0-100
    recovery_score: Optional[float] = None        # 0-100 (alias sleep pour compat)
    nutrition_score: Optional[float] = None       # 0-100 (réservé pour versions futures)
    hydration_score: Optional[float] = None       # 0-100 (réservé)

    # Score global
    overall_readiness: Optional[float] = None     # 0-100

    # Recommandation
    recommended_intensity: Optional[str] = None   # rest | light | moderate | normal | push
    reasoning: Optional[str] = None
    confidence_score: Optional[float] = None      # 0.0-1.0 (proportion de données disponibles)
    variables_used: Optional[dict] = None         # méta : quelles données ont alimenté le calcul

    algorithm_version: str = "v1.0"
    created_at: datetime
    updated_at: datetime


class ReadinessScoreHistoryResponse(BaseModel):
    """Historique sur N jours."""
    history: List[ReadinessScoreResponse]
    days_requested: int
    days_available: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
