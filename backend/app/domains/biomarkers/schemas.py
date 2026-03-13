"""SOMA LOT 16 — Biomarker Pydantic schemas."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class LabResultCreate(BaseModel):
    marker_name: str
    value: float
    unit: str
    lab_date: date
    source: str = "manual"
    confidence: float = Field(default=1.0, ge=0, le=1)


class LabResultResponse(BaseModel):
    id: str
    marker_name: str
    value: float
    unit: str
    lab_date: str
    source: str
    confidence: float


class BiomarkerMarkerAnalysis(BaseModel):
    marker_name: str
    value: float
    unit: str
    status: str = Field(description="optimal|adequate|suboptimal|deficient|elevated|toxic")
    score: float = Field(ge=0, le=100)
    deviation_pct: float
    interpretation: str
    recommendations: list[str]


class BiomarkerAnalysisResponse(BaseModel):
    analysis_date: str
    metabolic_health_score: float = Field(ge=0, le=100)
    inflammation_score: float = Field(ge=0, le=100, description="Higher = worse")
    cardiovascular_risk: float = Field(ge=0, le=100)
    longevity_modifier: float = Field(ge=-10, le=10, description="Years added/subtracted from biological age")
    markers_analyzed: int
    optimal_markers: int
    suboptimal_markers: int
    deficient_markers: list[str]
    elevated_markers: list[str]
    priority_actions: list[str]
    supplementation_recommendations: list[str]
    dietary_recommendations: list[str]
    confidence: float = Field(ge=0, le=1)


class BiomarkerDetailedResponse(BiomarkerAnalysisResponse):
    marker_analyses: list[BiomarkerMarkerAnalysis]


class LongevityImpactResponse(BaseModel):
    longevity_modifier: float
    metabolic_health_score: float
    inflammation_score: float
    cardiovascular_risk: float
    key_longevity_factors: list[str]
    longevity_recommendations: list[str]


class BiomarkerReferenceRange(BaseModel):
    marker_name: str
    unit: str
    optimal_low: Optional[float]
    optimal_high: Optional[float]
    adequate_low: Optional[float]
    adequate_high: Optional[float]
    category: str
