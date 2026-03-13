"""
Adaptive Nutrition Engine — Pydantic response schemas.
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class NutritionTargetResponse(BaseModel):
    value: float
    unit: str
    rationale: str
    priority: str   # "critical" | "high" | "normal" | "low"


class AdaptiveNutritionPlanResponse(BaseModel):
    target_date: str
    day_type: str
    glycogen_status: str

    calorie_target: NutritionTargetResponse
    protein_target: NutritionTargetResponse
    carb_target: NutritionTargetResponse
    fat_target: NutritionTargetResponse
    fiber_target: NutritionTargetResponse
    hydration_target: NutritionTargetResponse

    meal_timing_strategy: str
    fasting_compatible: bool
    fasting_rationale: str
    pre_workout_guidance: Optional[str] = None
    post_workout_guidance: Optional[str] = None
    recovery_nutrition_focus: str
    electrolyte_focus: str
    supplementation_focus: list[str]

    confidence: float = Field(ge=0, le=1)
    assumptions: list[str]
    alerts: list[str]


class AdaptiveNutritionTargetsResponse(BaseModel):
    """Compact response — macros only, no strategies."""
    target_date: str
    day_type: str
    calorie_target: float
    protein_g: float
    carb_g: float
    fat_g: float
    hydration_ml: float
    fasting_compatible: bool
    confidence: float = Field(ge=0, le=1)
    alerts: list[str]
