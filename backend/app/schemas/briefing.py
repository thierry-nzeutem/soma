"""Schémas Pydantic — Daily Briefing — LOT 18.

DailyBriefingResponse : réponse de GET /daily/briefing.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DailyBriefingResponse(BaseModel):
    """Briefing matinal quotidien — agrégation des données de santé du jour."""

    briefing_date: date
    generated_at: datetime

    # ── Récupération ──────────────────────────────────────────────────────────
    readiness_score: Optional[float] = Field(None, ge=0, le=100)
    readiness_level: Optional[str] = Field(None)       # "low"|"moderate"|"good"|"excellent"
    readiness_color: str = Field("#FF9500")             # hex color
    recommended_intensity: Optional[str] = Field(None) # "rest"|"light"|"moderate"|"normal"|"push"

    # ── Sommeil ───────────────────────────────────────────────────────────────
    sleep_duration_h: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality_label: Optional[str] = Field(None)   # "poor"|"fair"|"good"|"excellent"

    # ── Entraînement ──────────────────────────────────────────────────────────
    training_type: Optional[str] = Field(None)
    training_intensity: Optional[str] = Field(None)
    training_duration_min: Optional[int] = Field(None, ge=0, le=300)

    # ── Nutrition ─────────────────────────────────────────────────────────────
    calorie_target: Optional[float] = Field(None, ge=0)
    protein_target_g: Optional[float] = Field(None, ge=0)
    carb_target_g: Optional[float] = Field(None, ge=0)
    fat_target_g: Optional[float] = Field(None, ge=0)
    hydration_target_ml: int = Field(2500, ge=0)

    # ── Jumeau numérique ──────────────────────────────────────────────────────
    twin_status: Optional[str] = Field(None)            # "fresh"|"good"|"moderate"|"tired"|"critical"
    twin_primary_concern: Optional[str] = Field(None)

    # ── Alertes & insights ────────────────────────────────────────────────────
    alerts: list[str] = Field(default_factory=list)    # max 3
    top_insight: Optional[str] = Field(None)
    coach_tip: Optional[str] = Field(None)

    model_config = {"from_attributes": True}
