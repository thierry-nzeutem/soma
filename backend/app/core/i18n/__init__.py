"""SOMA i18n — Internationalisation simple pour labels backend.

Le backend reste data-centric (scores numériques, clés enum).
Ce module traduit uniquement les labels générés côté serveur
(briefing, coach tips, readiness levels, sleep quality).

Usage :
    from app.core.i18n import t

    label = t("readiness_level.excellent", locale="en")
    # → "Excellent" (EN) ou "Excellent" (FR)
"""

from app.core.i18n.translations import t, get_supported_locales

__all__ = ["t", "get_supported_locales"]
