"""Tests pour le systeme i18n SOMA (translations + locale middleware)."""

import pytest

from app.core.i18n import t, get_supported_locales
from app.middleware.locale_middleware import _parse_accept_language


# ── Translation function tests ──────────────────────────────────────────────

class TestTranslations:
    """Tests pour la fonction t()."""

    def test_fr_default(self):
        assert t("readiness.excellent") == "Excellent"

    def test_fr_explicit(self):
        assert t("readiness.good", locale="fr") == "Bon"

    def test_en_translation(self):
        assert t("readiness.good", locale="en") == "Good"

    def test_sleep_quality_fr(self):
        assert t("sleep.excellent", locale="fr") == "Excellente"

    def test_sleep_quality_en(self):
        assert t("sleep.excellent", locale="en") == "Excellent"

    def test_day_type_fr(self):
        assert t("day_type.rest", locale="fr") == "Repos"

    def test_day_type_en(self):
        assert t("day_type.rest", locale="en") == "Rest"

    def test_risk_levels(self):
        assert t("risk.low", locale="fr") == "Faible"
        assert t("risk.low", locale="en") == "Low"
        assert t("risk.critical", locale="en") == "Critical"

    def test_consistency_labels(self):
        assert t("consistency.excellent", locale="fr") == "Excellent"
        assert t("consistency.poor", locale="en") == "Poor"

    def test_problem_types(self):
        assert t("problem.chronic_insufficient", locale="fr") == "Sommeil chroniquement insuffisant"
        assert t("problem.chronic_insufficient", locale="en") == "Chronically insufficient sleep"

    def test_briefing_labels(self):
        assert t("briefing.greeting_morning", locale="fr") == "Bonjour"
        assert t("briefing.greeting_morning", locale="en") == "Good morning"

    def test_unknown_key_returns_key(self):
        assert t("nonexistent.key") == "nonexistent.key"

    def test_unknown_locale_falls_back_to_fr(self):
        assert t("readiness.excellent", locale="de") == "Excellent"

    def test_none_locale_falls_back_to_fr(self):
        assert t("readiness.excellent", locale=None) == "Excellent"

    def test_empty_locale_falls_back_to_fr(self):
        assert t("readiness.excellent", locale="") == "Excellent"

    def test_architecture_quality_labels(self):
        assert t("architecture.excellent", locale="en") == "Excellent"
        assert t("architecture.estimated_good", locale="en") == "Good (estimated)"
        assert t("architecture.estimated_good", locale="fr") == "Bon (estimé)"

    def test_trend_labels(self):
        assert t("trend.improving", locale="en") == "Improving"
        assert t("trend.stable", locale="fr") == "Stable"
        assert t("trend.declining", locale="en") == "Declining"

    def test_coach_labels(self):
        assert t("coach.synthesis", locale="fr") == "Synthèse"
        assert t("coach.synthesis", locale="en") == "Summary"

    def test_severity_labels(self):
        assert t("severity.warning", locale="fr") == "Attention"
        assert t("severity.warning", locale="en") == "Warning"


class TestSupportedLocales:
    def test_returns_tuple(self):
        locales = get_supported_locales()
        assert isinstance(locales, tuple)

    def test_fr_and_en_supported(self):
        locales = get_supported_locales()
        assert "fr" in locales
        assert "en" in locales

    def test_length(self):
        assert len(get_supported_locales()) == 2


# ── Accept-Language parser tests ────────────────────────────────────────────

class TestAcceptLanguageParser:
    """Tests pour _parse_accept_language()."""

    def test_empty_header(self):
        assert _parse_accept_language("") == "fr"

    def test_fr_simple(self):
        assert _parse_accept_language("fr") == "fr"

    def test_en_simple(self):
        assert _parse_accept_language("en") == "en"

    def test_en_us(self):
        assert _parse_accept_language("en-US") == "en"

    def test_fr_fr(self):
        assert _parse_accept_language("fr-FR") == "fr"

    def test_multiple_with_quality(self):
        assert _parse_accept_language("en-US,en;q=0.9,fr;q=0.8") == "en"

    def test_fr_preferred(self):
        assert _parse_accept_language("fr-FR,fr;q=0.9,en;q=0.5") == "fr"

    def test_unsupported_falls_to_default(self):
        assert _parse_accept_language("de") == "fr"

    def test_unsupported_then_en(self):
        assert _parse_accept_language("de;q=1.0,en;q=0.5") == "en"

    def test_complex_header(self):
        assert _parse_accept_language("zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7") == "en"

    def test_equal_quality_first_wins(self):
        # Both have q=0.9, first match wins
        assert _parse_accept_language("en;q=0.9,fr;q=0.9") in ("en", "fr")

    def test_invalid_quality(self):
        assert _parse_accept_language("en;q=abc,fr") == "fr"

    def test_whitespace_handling(self):
        assert _parse_accept_language(" en , fr;q=0.5 ") == "en"

    def test_case_insensitive(self):
        assert _parse_accept_language("EN-US") == "en"

    def test_star_wildcard(self):
        # * doesn't match any supported locale
        assert _parse_accept_language("*") == "fr"
