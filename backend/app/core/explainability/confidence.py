"""
SOMA LOT 17 — Explainability Confidence.

Helpers for converting 0–1 confidence scores to human-readable tiers and labels.
All functions are pure (no side effects).
"""


def confidence_tier(score: float) -> str:
    """
    Convert a 0–1 confidence score to a tier string.

    Thresholds:
      >= 0.7  → "high"
      >= 0.4  → "medium"
      < 0.4   → "low"

    Args:
        score: Confidence value in [0.0, 1.0]

    Returns:
        "high" | "medium" | "low"
    """
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    else:
        return "low"


def confidence_tier_label(score: float) -> str:
    """
    Convert a 0–1 confidence score to a French tier label.

    Returns:
        "élevée" | "moyenne" | "faible"
    """
    tier = confidence_tier(score)
    labels = {
        "high": "élevée",
        "medium": "moyenne",
        "low": "faible",
    }
    return labels[tier]


def format_confidence(score: float) -> str:
    """
    Format a confidence score as a human-readable French string.

    Example:
        format_confidence(0.73) → "73% (élevée)"
        format_confidence(0.45) → "45% (moyenne)"
        format_confidence(0.12) → "12% (faible)"

    Args:
        score: Confidence value in [0.0, 1.0]

    Returns:
        String like "73% (élevée)"
    """
    pct = int(round(score * 100))
    tier = confidence_tier_label(score)
    return f"{pct}% ({tier})"
