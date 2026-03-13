"""
SOMA LOT 17 — Explainability Severity.

Maps alert types and severity levels to visual indicators (colors, icons).
Used by coach platform alerts and injury prevention recommendations.
All functions are pure.
"""

# Hex color codes for UI rendering
SEVERITY_COLORS: dict[str, str] = {
    "critical": "#FF3B30",  # Red
    "warning": "#FF9500",   # Orange
    "moderate": "#FFCC00",  # Yellow
    "info": "#34C759",      # Green
    "low": "#34C759",       # Green (alias)
    "high": "#FF3B30",      # Red (alias)
    "orange": "#FF9500",    # Orange (coach platform risk level)
    "yellow": "#FFCC00",    # Yellow (coach platform risk level)
    "green": "#34C759",     # Green (coach platform risk level)
    "red": "#FF3B30",       # Red (coach platform risk level)
}

# Emoji icons for text-based display
SEVERITY_ICONS: dict[str, str] = {
    "critical": "🔴",
    "warning": "🟠",
    "moderate": "🟡",
    "info": "🟢",
    "low": "🟢",
    "high": "🔴",
    "orange": "🟠",
    "yellow": "🟡",
    "green": "🟢",
    "red": "🔴",
}

# Map alert types to their default severity
_ALERT_TYPE_SEVERITY: dict[str, str] = {
    "overtraining_risk": "critical",
    "injury_risk": "warning",
    "low_readiness": "warning",
    "poor_recovery": "warning",
    "inactivity": "info",
    "high_acwr": "critical",
    "fatigue": "warning",
    "sleep_deficit": "moderate",
    "nutrition_deficit": "moderate",
    "hydration": "info",
}


def severity_color(level: str) -> str:
    """
    Return the hex color for a severity level.

    Args:
        level: Severity level string (critical, warning, moderate, info, low, high,
               or coach platform risk: green, yellow, orange, red)

    Returns:
        Hex color string like "#FF3B30"
    """
    return SEVERITY_COLORS.get(level, "#8E8E93")  # Default: gray


def severity_icon(level: str) -> str:
    """
    Return the emoji icon for a severity level.

    Args:
        level: Severity level string

    Returns:
        Emoji string like "🔴"
    """
    return SEVERITY_ICONS.get(level, "⚪")  # Default: white circle


def alert_severity(alert_type: str) -> str:
    """
    Determine the severity of an alert based on its type.

    Args:
        alert_type: Alert type identifier (e.g., "overtraining_risk", "inactivity")

    Returns:
        Severity string: "critical" | "warning" | "moderate" | "info"
    """
    return _ALERT_TYPE_SEVERITY.get(alert_type, "info")
