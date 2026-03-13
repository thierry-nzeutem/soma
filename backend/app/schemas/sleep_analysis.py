"""Schemas Pydantic pour l'analyse du sommeil."""

from typing import List, Optional
from pydantic import BaseModel


class SleepArchitectureResponse(BaseModel):
    """Distribution des phases de sommeil et score."""
    deep_pct: float = 0.0
    rem_pct: float = 0.0
    light_pct: float = 0.0
    awake_pct: float = 0.0
    architecture_score: int = 0
    architecture_quality: str = "unknown"
    areas_to_improve: List[str] = []


class SleepConsistencyResponse(BaseModel):
    """Regularite des horaires de sommeil."""
    avg_bedtime_hour: Optional[float] = None
    avg_wake_hour: Optional[float] = None
    bedtime_variance_min: float = 0.0
    wake_variance_min: float = 0.0
    consistency_score: int = 0
    consistency_label: str = "unknown"
    sessions_analyzed: int = 0


class SleepProblemResponse(BaseModel):
    """Un probleme de sommeil detecte."""
    problem_type: str
    severity: str
    description: str
    recommendation: str
    evidence_days: int = 0


class SleepAnalysisResponse(BaseModel):
    """Resultat agrege des 3 analyses de sommeil."""
    architecture: Optional[SleepArchitectureResponse] = None
    consistency: Optional[SleepConsistencyResponse] = None
    problems: List[SleepProblemResponse] = []
