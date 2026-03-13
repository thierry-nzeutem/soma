"""SOMA LOT 15 -- Injury Prevention Engine schemas."""
from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class RiskZoneResponse(BaseModel):
    body_part: str
    risk_level: str = Field(description="minimal|low|moderate|high|critical")
    risk_score: float = Field(ge=0, le=100)
    contributing_factors: list[str]
    recommendations: list[str]


class InjuryRiskResponse(BaseModel):
    analysis_date: str
    injury_risk_score: float = Field(ge=0, le=100)
    injury_risk_category: str = Field(description="minimal|low|moderate|high|critical")
    acwr_risk_score: float = Field(ge=0, le=100)
    fatigue_risk_score: float = Field(ge=0, le=100)
    asymmetry_risk_score: float = Field(ge=0, le=100)
    sleep_risk_score: float = Field(ge=0, le=100)
    monotony_risk_score: float = Field(ge=0, le=100)
    risk_zones: list[RiskZoneResponse]
    movement_compensation_patterns: list[str]
    fatigue_compensation_risk: bool
    training_overload_risk: bool
    recommendations: list[str]
    immediate_actions: list[str]
    confidence: float = Field(ge=0, le=1)


class InjuryHistoryItem(BaseModel):
    snapshot_date: str
    injury_risk_score: float
    injury_risk_category: str
    primary_risk_zone: Optional[str] = None


class InjuryHistoryResponse(BaseModel):
    user_id: str
    days_requested: int
    snapshots: list[InjuryHistoryItem]
    total_count: int


class InjuryRecommendationsResponse(BaseModel):
    injury_risk_score: float
    injury_risk_category: str
    immediate_actions: list[str]
    recommendations: list[str]
    risk_zones: list[RiskZoneResponse]
