"""
Biological Age Engine — Pydantic response schemas.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class BiologicalAgeComponentResponse(BaseModel):
    factor_name: str
    display_name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    age_delta_years: float          # negative = biologically younger contribution
    explanation: str
    is_available: bool


class BiologicalAgeLeverResponse(BaseModel):
    lever_id: str
    title: str
    description: str
    potential_years_gained: float = Field(ge=0)
    difficulty: str                 # "easy" | "moderate" | "hard"
    timeframe: str                  # "weeks" | "months" | "years"
    component: str


class BiologicalAgeResponse(BaseModel):
    chronological_age: int
    biological_age: float
    biological_age_delta: float     # bio_age - chrono_age (negative = younger)
    longevity_risk_score: float = Field(ge=0, le=100)
    trend_direction: str            # "improving" | "stable" | "declining"
    confidence: float = Field(ge=0, le=1)
    explanation: str
    components: list[BiologicalAgeComponentResponse]
    levers: list[BiologicalAgeLeverResponse]


class BiologicalAgeLeversResponse(BaseModel):
    """Standalone levers endpoint response."""
    chronological_age: int
    biological_age: float
    biological_age_delta: float
    levers: list[BiologicalAgeLeverResponse]
    total_potential_years: float    # sum of potential_years_gained across all levers


class BiologicalAgeHistoryItem(BaseModel):
    snapshot_date: str
    biological_age: float
    biological_age_delta: float
    trend_direction: str
    confidence: float


class BiologicalAgeHistoryResponse(BaseModel):
    user_id: str
    days_requested: int
    snapshots: list[BiologicalAgeHistoryItem]
    total_count: int
