"""SOMA LOT 13 - Pydantic schemas for learning domain."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class UserLearningProfileResponse(BaseModel):
    true_tdee: Optional[float] = None
    estimated_mifflin_tdee: Optional[float] = None
    metabolic_efficiency: float = Field(description="Ratio true/mifflin TDEE")
    metabolic_trend: str = Field(description="improving|stable|declining")
    recovery_profile: str = Field(description="fast|normal|slow")
    recovery_factor: float = Field(ge=0.5, le=1.5)
    avg_recovery_days: float = Field(ge=0)
    training_load_tolerance: float = Field(ge=0, description="Weekly load in AU")
    adaptation_rate: float = Field(ge=0, le=1)
    optimal_acwr: float = Field(ge=0.8, le=1.5)
    carb_response: float = Field(ge=-1, le=1)
    protein_response: float = Field(ge=-1, le=1)
    sleep_recovery_factor: float = Field(ge=0.5, le=1.5)
    confidence: float = Field(ge=0, le=1)
    days_analyzed: int = Field(ge=0)
    data_sufficient: bool
    insights: list[str] = Field(default_factory=list)


class LearningInsightResponse(BaseModel):
    insight_type: str
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)
    actionable: bool = True


class LearningInsightsResponse(BaseModel):
    user_id: str
    profile: UserLearningProfileResponse
    top_insights: list[LearningInsightResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class LearningRecomputeResponse(BaseModel):
    success: bool
    message: str
    days_analyzed: int
    confidence: float
