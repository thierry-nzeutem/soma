"""
Motion Intelligence Engine — Pydantic response schemas.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ExerciseMotionProfileResponse(BaseModel):
    exercise_type: str
    sessions_analyzed: int
    avg_stability: float = Field(ge=0, le=100)
    avg_amplitude: float = Field(ge=0, le=100)
    avg_quality: float = Field(ge=0, le=100)
    stability_trend: str    # "improving" | "stable" | "declining"
    amplitude_trend: str
    quality_trend: str
    quality_variance: float
    last_session_date: Optional[str] = None
    alerts: list[str]


class MotionIntelligenceResponse(BaseModel):
    analysis_date: str
    sessions_analyzed: int
    days_analyzed: int
    movement_health_score: float = Field(ge=0, le=100)
    stability_score: float = Field(ge=0, le=100)
    mobility_score: float = Field(ge=0, le=100)
    asymmetry_score: float = Field(ge=0, le=100)
    overall_quality_trend: str
    consecutive_quality_sessions: int
    exercise_profiles: dict[str, ExerciseMotionProfileResponse]
    recommendations: list[str]
    risk_alerts: list[str]
    confidence: float = Field(ge=0, le=1)


class AsymmetryRiskResponse(BaseModel):
    """Fast-path response for asymmetry risk only."""
    analysis_date: str
    asymmetry_score: float = Field(ge=0, le=100)
    risk_level: str          # "low" | "moderate" | "high"
    sessions_analyzed: int
    confidence: float = Field(ge=0, le=1)
    alerts: list[str]


class MotionHistoryItem(BaseModel):
    snapshot_date: str
    movement_health_score: float
    stability_score: float
    mobility_score: float
    asymmetry_score: float
    overall_quality_trend: str
    confidence: float


class MotionHistoryResponse(BaseModel):
    user_id: str
    days_requested: int
    snapshots: list[MotionHistoryItem]
    total_count: int
