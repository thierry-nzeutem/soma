"""Enumeration des fonctionnalites SOMA et matrice plan/feature."""
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.plans import PlanCode


class FeatureCode(str, Enum):
    # Free tier
    BASIC_DASHBOARD = "basic_dashboard"
    BASIC_HEALTH_METRICS = "basic_health_metrics"
    LOCAL_AI_TIPS = "local_ai_tips"

    # AI tier
    AI_COACH = "ai_coach"
    DAILY_BRIEFING = "daily_briefing"
    ADVANCED_INSIGHTS = "advanced_insights"
    PDF_REPORTS = "pdf_reports"
    ANOMALY_DETECTION = "anomaly_detection"
    BIOLOGICAL_AGE = "biological_age"

    # Performance tier
    READINESS_SCORE = "readiness_score"
    INJURY_PREDICTION = "injury_prediction"
    BIOMECHANICS_VISION = "biomechanics_vision"
    ADVANCED_VO2MAX = "advanced_vo2max"
    TRAINING_LOAD = "training_load"
