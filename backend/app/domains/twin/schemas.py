"""Pydantic v2 schemas for Digital Twin V2 API responses."""
from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class TwinComponentResponse(BaseModel):
    """Serialized TwinComponent — includes full explainability fields."""
    value: float
    status: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    variables_used: list[str] = []


class DigitalTwinStateResponse(BaseModel):
    """Full Digital Twin state response."""
    snapshot_date: str  # YYYY-MM-DD

    # Energy & substrate
    energy_balance: TwinComponentResponse
    glycogen: TwinComponentResponse
    carb_availability: TwinComponentResponse
    protein_status: TwinComponentResponse

    # Hydration
    hydration: TwinComponentResponse

    # Recovery
    fatigue: TwinComponentResponse
    inflammation: TwinComponentResponse
    sleep_debt: TwinComponentResponse
    recovery_capacity: TwinComponentResponse

    # Readiness
    training_readiness: TwinComponentResponse

    # Stress & metabolic
    stress_load: TwinComponentResponse
    metabolic_flexibility: TwinComponentResponse

    # Risk flags
    plateau_risk: bool
    under_recovery_risk: bool

    # Synthesis
    overall_status: str
    primary_concern: str
    global_confidence: float = Field(ge=0.0, le=1.0)
    recommendations: list[str] = []


class DigitalTwinSummaryResponse(BaseModel):
    """Compact summary for dashboard / coach context."""
    snapshot_date: str
    overall_status: str
    training_readiness: float
    fatigue: float
    glycogen_status: str
    primary_concern: str
    plateau_risk: bool
    under_recovery_risk: bool
    global_confidence: float
    summary_text: str


class DigitalTwinHistoryItem(BaseModel):
    """Single entry for history list."""
    snapshot_date: str
    overall_status: str
    training_readiness: float
    fatigue: float
    global_confidence: float


class DigitalTwinHistoryResponse(BaseModel):
    """History list response."""
    user_id: str
    days_requested: int
    snapshots: list[DigitalTwinHistoryItem]
    total_count: int
