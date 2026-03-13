"""SOMA Translations — Dictionnaire simple FR/EN pour labels backend.

Couvre ~50 labels utilisés dans les réponses API :
- Niveaux de readiness
- Qualité de sommeil
- Types de jour
- Niveaux de risque
- Labels briefing
- Labels coach / insights
"""

from typing import Optional

# ── Supported locales ────────────────────────────────────────────────────────

SUPPORTED_LOCALES = ("fr", "en")
DEFAULT_LOCALE = "fr"

# ── Translation dictionary ──────────────────────────────────────────────────

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Readiness levels ─────────────────────────────────────────────────
    "readiness.excellent": {"fr": "Excellent", "en": "Excellent"},
    "readiness.good": {"fr": "Bon", "en": "Good"},
    "readiness.moderate": {"fr": "Modéré", "en": "Moderate"},
    "readiness.low": {"fr": "Faible", "en": "Low"},
    "readiness.rest": {"fr": "Repos nécessaire", "en": "Rest needed"},

    # ── Sleep quality ────────────────────────────────────────────────────
    "sleep.excellent": {"fr": "Excellente", "en": "Excellent"},
    "sleep.good": {"fr": "Bonne", "en": "Good"},
    "sleep.fair": {"fr": "Correcte", "en": "Fair"},
    "sleep.poor": {"fr": "Mauvaise", "en": "Poor"},
    "sleep.unknown": {"fr": "Inconnue", "en": "Unknown"},

    # ── Architecture quality ─────────────────────────────────────────────
    "architecture.excellent": {"fr": "Excellent", "en": "Excellent"},
    "architecture.good": {"fr": "Bon", "en": "Good"},
    "architecture.fair": {"fr": "Correct", "en": "Fair"},
    "architecture.poor": {"fr": "Faible", "en": "Poor"},
    "architecture.estimated_good": {"fr": "Bon (estimé)", "en": "Good (estimated)"},
    "architecture.estimated_fair": {"fr": "Correct (estimé)", "en": "Fair (estimated)"},
    "architecture.estimated_poor": {"fr": "Faible (estimé)", "en": "Poor (estimated)"},

    # ── Day types ────────────────────────────────────────────────────────
    "day_type.rest": {"fr": "Repos", "en": "Rest"},
    "day_type.training": {"fr": "Entraînement", "en": "Training"},
    "day_type.intense_training": {"fr": "Entraînement intense", "en": "Intense training"},
    "day_type.recovery": {"fr": "Récupération", "en": "Recovery"},
    "day_type.deload": {"fr": "Décharge", "en": "Deload"},

    # ── Risk levels ──────────────────────────────────────────────────────
    "risk.low": {"fr": "Faible", "en": "Low"},
    "risk.moderate": {"fr": "Modéré", "en": "Moderate"},
    "risk.high": {"fr": "Élevé", "en": "High"},
    "risk.critical": {"fr": "Critique", "en": "Critical"},
    "risk.green": {"fr": "Vert", "en": "Green"},
    "risk.yellow": {"fr": "Jaune", "en": "Yellow"},
    "risk.orange": {"fr": "Orange", "en": "Orange"},
    "risk.red": {"fr": "Rouge", "en": "Red"},

    # ── Severity ─────────────────────────────────────────────────────────
    "severity.info": {"fr": "Info", "en": "Info"},
    "severity.warning": {"fr": "Attention", "en": "Warning"},
    "severity.critical": {"fr": "Critique", "en": "Critical"},

    # ── Briefing ─────────────────────────────────────────────────────────
    "briefing.greeting_morning": {"fr": "Bonjour", "en": "Good morning"},
    "briefing.greeting_afternoon": {"fr": "Bon après-midi", "en": "Good afternoon"},
    "briefing.greeting_evening": {"fr": "Bonsoir", "en": "Good evening"},
    "briefing.readiness_label": {"fr": "Votre score de préparation", "en": "Your readiness score"},
    "briefing.sleep_label": {"fr": "Sommeil", "en": "Sleep"},
    "briefing.nutrition_label": {"fr": "Nutrition", "en": "Nutrition"},
    "briefing.training_label": {"fr": "Entraînement", "en": "Training"},
    "briefing.no_data": {"fr": "Données insuffisantes", "en": "Insufficient data"},

    # ── Coach ────────────────────────────────────────────────────────────
    "coach.synthesis": {"fr": "Synthèse", "en": "Summary"},
    "coach.recommendations": {"fr": "Recommandations", "en": "Recommendations"},
    "coach.warning": {"fr": "Attention", "en": "Warning"},

    # ── Trends ───────────────────────────────────────────────────────────
    "trend.improving": {"fr": "En amélioration", "en": "Improving"},
    "trend.stable": {"fr": "Stable", "en": "Stable"},
    "trend.declining": {"fr": "En déclin", "en": "Declining"},

    # ── Consistency ──────────────────────────────────────────────────────
    "consistency.excellent": {"fr": "Excellent", "en": "Excellent"},
    "consistency.good": {"fr": "Bon", "en": "Good"},
    "consistency.moderate": {"fr": "Modéré", "en": "Moderate"},
    "consistency.poor": {"fr": "Faible", "en": "Poor"},
    "consistency.insufficient_data": {"fr": "Données insuffisantes", "en": "Insufficient data"},

    # ── Sleep problems ───────────────────────────────────────────────────
    "problem.chronic_insufficient": {
        "fr": "Sommeil chroniquement insuffisant",
        "en": "Chronically insufficient sleep",
    },
    "problem.quality_degradation": {
        "fr": "Dégradation de la qualité du sommeil",
        "en": "Sleep quality degradation",
    },
    "problem.late_bedtime": {
        "fr": "Coucher régulièrement tardif",
        "en": "Consistently late bedtime",
    },
    "problem.fragmented_sleep": {
        "fr": "Sommeil fragmenté",
        "en": "Fragmented sleep",
    },
    "problem.insufficient_deep_sleep": {
        "fr": "Sommeil profond insuffisant",
        "en": "Insufficient deep sleep",
    },

    # ── General ──────────────────────────────────────────────────────────
    "general.score": {"fr": "Score", "en": "Score"},
    "general.details": {"fr": "Détails", "en": "Details"},
    "general.recommendations": {"fr": "Recommandations", "en": "Recommendations"},
    "general.period_days": {"fr": "jours", "en": "days"},
}


def t(key: str, locale: Optional[str] = None) -> str:
    """Translate a key to the given locale.

    Falls back to French if locale is unsupported or key is missing.
    Returns the key itself if not found in any locale.

    Args:
        key: Dotted translation key (e.g. "readiness.excellent")
        locale: Target locale ("fr" or "en"). Defaults to "fr".

    Returns:
        Translated string.
    """
    locale = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(locale, entry.get(DEFAULT_LOCALE, key))


def get_supported_locales() -> tuple[str, ...]:
    """Return supported locale codes."""
    return SUPPORTED_LOCALES
