"""
SOMA LOT 17 — Explainability Labels.

Human-readable French labels for scores, trends, day types and biomarker statuses.
All functions are pure (no side effects, no external dependencies).
"""


def risk_label(score: float) -> str:
    """
    Convert a 0-100 risk score to a French label.

    Thresholds:
      0–20   → Minimal
      21–40  → Faible
      41–60  → Modéré
      61–80  → Élevé
      81–100 → Critique
    """
    if score <= 20:
        return "Minimal"
    elif score <= 40:
        return "Faible"
    elif score <= 60:
        return "Modéré"
    elif score <= 80:
        return "Élevé"
    else:
        return "Critique"


def trend_label(direction: str) -> str:
    """
    Convert a trend direction string to a French label.

    Supported values: "improving", "stable", "declining"
    Unknown values return "Inconnu".
    """
    mapping = {
        "improving": "En amélioration",
        "stable": "Stable",
        "declining": "En déclin",
    }
    return mapping.get(direction, "Inconnu")


def day_type_label(day_type: str) -> str:
    """
    Convert an adaptive nutrition day type to a French label.

    Supported values: "rest", "training", "intense_training", "recovery", "deload"
    """
    mapping = {
        "rest": "Repos",
        "training": "Entraînement",
        "intense_training": "Entraînement intensif",
        "recovery": "Récupération",
        "deload": "Décharge",
    }
    return mapping.get(day_type, day_type.replace("_", " ").capitalize())


def biomarker_status_label(status: str) -> str:
    """
    Convert a biomarker analysis status to a French label.

    Supported values: "optimal", "adequate", "suboptimal", "deficient",
                      "elevated", "low", "high", "critical_low", "critical_high", "toxic"
    """
    mapping = {
        "optimal": "Optimal",
        "adequate": "Adéquat",
        "suboptimal": "Sous-optimal",
        "deficient": "Déficient",
        "elevated": "Élevé",
        "low": "Insuffisant",
        "high": "Élevé",
        "critical_low": "Critique (bas)",
        "critical_high": "Critique (élevé)",
        "toxic": "Toxique",
        "normal": "Normal",
    }
    return mapping.get(status, status.replace("_", " ").capitalize())


def risk_level_label(risk_level: str) -> str:
    """
    Convert a coach platform risk level (green/yellow/orange/red) to a French label.

    Used in athlete dashboard summaries.
    """
    mapping = {
        "green": "Vert — Tout va bien",
        "yellow": "Jaune — Surveiller",
        "orange": "Orange — Attention",
        "red": "Rouge — Intervention requise",
    }
    return mapping.get(risk_level, risk_level.capitalize())
