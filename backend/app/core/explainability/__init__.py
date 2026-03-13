"""
SOMA LOT 17 — Transverse Explainability Module.

Provides shared label functions, confidence tiers, and severity mappings
used across all SOMA health domains (learning, injury, coach_platform, biomarkers).

Usage:
    from app.core.explainability.labels import risk_label, trend_label
    from app.core.explainability.confidence import confidence_tier, format_confidence
    from app.core.explainability.severity import severity_color, alert_severity
"""
from app.core.explainability.labels import (
    risk_label,
    trend_label,
    day_type_label,
    biomarker_status_label,
    risk_level_label,
)
from app.core.explainability.confidence import (
    confidence_tier,
    format_confidence,
)
from app.core.explainability.severity import (
    severity_color,
    severity_icon,
    alert_severity,
    SEVERITY_COLORS,
    SEVERITY_ICONS,
)

__all__ = [
    "risk_label",
    "trend_label",
    "day_type_label",
    "biomarker_status_label",
    "risk_level_label",
    "confidence_tier",
    "format_confidence",
    "severity_color",
    "severity_icon",
    "alert_severity",
    "SEVERITY_COLORS",
    "SEVERITY_ICONS",
]
