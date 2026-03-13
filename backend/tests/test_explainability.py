"""
SOMA LOT 17 — Tests unitaires du module d'explainabilité transverse.

Couvre :
  - labels.py   : risk_label, trend_label, day_type_label, biomarker_status_label, risk_level_label
  - confidence.py : confidence_tier, confidence_tier_label, format_confidence
  - severity.py  : severity_color, severity_icon, alert_severity

~20 tests purs, aucune dépendance DB.
"""
import pytest
from app.core.explainability.labels import (
    risk_label, trend_label, day_type_label, biomarker_status_label, risk_level_label,
)
from app.core.explainability.confidence import (
    confidence_tier, confidence_tier_label, format_confidence,
)
from app.core.explainability.severity import (
    severity_color, severity_icon, alert_severity,
    SEVERITY_COLORS, SEVERITY_ICONS,
)


# ─── Tests labels.py ────────────────────────────────────────────────────────

class TestRiskLabel:
    """risk_label(score) — seuils 0-20/21-40/41-60/61-80/81-100."""

    def test_minimal_risk(self):
        assert risk_label(0.0) == "Minimal"
        assert risk_label(10.0) == "Minimal"
        assert risk_label(20.0) == "Minimal"

    def test_low_risk(self):
        assert risk_label(21.0) == "Faible"
        assert risk_label(35.0) == "Faible"
        assert risk_label(40.0) == "Faible"

    def test_moderate_risk(self):
        assert risk_label(41.0) == "Modéré"
        assert risk_label(55.0) == "Modéré"
        assert risk_label(60.0) == "Modéré"

    def test_high_risk(self):
        assert risk_label(61.0) == "Élevé"
        assert risk_label(70.0) == "Élevé"
        assert risk_label(80.0) == "Élevé"

    def test_critical_risk(self):
        assert risk_label(81.0) == "Critique"
        assert risk_label(95.0) == "Critique"
        assert risk_label(100.0) == "Critique"


class TestTrendLabel:
    """trend_label(direction) — improving / stable / declining."""

    def test_improving(self):
        assert trend_label("improving") == "En amélioration"

    def test_stable(self):
        assert trend_label("stable") == "Stable"

    def test_declining(self):
        assert trend_label("declining") == "En déclin"

    def test_unknown_direction(self):
        result = trend_label("unknown_value")
        assert result == "Inconnu"


class TestDayTypeLabel:
    """day_type_label(day_type) — all adaptive nutrition day types."""

    def test_all_day_types(self):
        mapping = {
            "rest": "Repos",
            "training": "Entraînement",
            "intense_training": "Entraînement intensif",
            "recovery": "Récupération",
            "deload": "Décharge",
        }
        for key, expected in mapping.items():
            assert day_type_label(key) == expected, f"Failed for {key}"

    def test_unknown_day_type(self):
        result = day_type_label("custom_type")
        assert isinstance(result, str)
        assert len(result) > 0


class TestBiomarkerStatusLabel:
    """biomarker_status_label — toutes les valeurs supportées."""

    def test_known_statuses(self):
        assert biomarker_status_label("optimal") == "Optimal"
        assert biomarker_status_label("adequate") == "Adéquat"
        assert biomarker_status_label("suboptimal") == "Sous-optimal"
        assert biomarker_status_label("deficient") == "Déficient"
        assert biomarker_status_label("elevated") == "Élevé"
        assert biomarker_status_label("normal") == "Normal"
        assert biomarker_status_label("low") == "Insuffisant"
        assert biomarker_status_label("high") == "Élevé"
        assert biomarker_status_label("critical_low") == "Critique (bas)"
        assert biomarker_status_label("critical_high") == "Critique (élevé)"
        assert biomarker_status_label("toxic") == "Toxique"


class TestRiskLevelLabel:
    """risk_level_label — niveaux du coach platform."""

    def test_all_levels(self):
        assert "Vert" in risk_level_label("green")
        assert "Jaune" in risk_level_label("yellow")
        assert "Orange" in risk_level_label("orange")
        assert "Rouge" in risk_level_label("red")


# ─── Tests confidence.py ─────────────────────────────────────────────────────

class TestConfidenceTier:
    """confidence_tier(score) — seuils 0.7/0.4."""

    def test_high_confidence(self):
        assert confidence_tier(0.7) == "high"
        assert confidence_tier(0.85) == "high"
        assert confidence_tier(1.0) == "high"

    def test_medium_confidence(self):
        assert confidence_tier(0.4) == "medium"
        assert confidence_tier(0.55) == "medium"
        assert confidence_tier(0.699) == "medium"

    def test_low_confidence(self):
        assert confidence_tier(0.0) == "low"
        assert confidence_tier(0.2) == "low"
        assert confidence_tier(0.399) == "low"


class TestFormatConfidence:
    """format_confidence(score) — format "X% (tier)"."""

    def test_high_confidence_format(self):
        result = format_confidence(0.73)
        assert "73%" in result
        assert "élevée" in result

    def test_medium_confidence_format(self):
        result = format_confidence(0.45)
        assert "45%" in result
        assert "moyenne" in result

    def test_low_confidence_format(self):
        result = format_confidence(0.12)
        assert "12%" in result
        assert "faible" in result

    def test_zero_confidence(self):
        result = format_confidence(0.0)
        assert "0%" in result
        assert "faible" in result

    def test_full_confidence(self):
        result = format_confidence(1.0)
        assert "100%" in result
        assert "élevée" in result


# ─── Tests severity.py ───────────────────────────────────────────────────────

class TestSeverityColor:
    """severity_color(level) — retourne une couleur hex valide."""

    def test_critical_color(self):
        color = severity_color("critical")
        assert color.startswith("#")
        assert len(color) == 7

    def test_warning_color(self):
        color = severity_color("warning")
        assert color.startswith("#")

    def test_info_color(self):
        color = severity_color("info")
        assert color.startswith("#")

    def test_unknown_level_returns_gray(self):
        color = severity_color("unknown_level")
        assert color.startswith("#")


class TestSeverityIcon:
    """severity_icon(level) — retourne un emoji."""

    def test_critical_icon(self):
        assert severity_icon("critical") == "🔴"

    def test_warning_icon(self):
        assert severity_icon("warning") == "🟠"

    def test_info_icon(self):
        assert severity_icon("info") == "🟢"

    def test_unknown_icon_returns_default(self):
        icon = severity_icon("totally_unknown")
        assert isinstance(icon, str)


class TestAlertSeverity:
    """alert_severity(alert_type) — mapping types → severités."""

    def test_overtraining_is_critical(self):
        assert alert_severity("overtraining_risk") == "critical"

    def test_injury_risk_is_warning(self):
        assert alert_severity("injury_risk") == "warning"

    def test_low_readiness_is_warning(self):
        assert alert_severity("low_readiness") == "warning"

    def test_inactivity_is_info(self):
        assert alert_severity("inactivity") == "info"

    def test_unknown_alert_type_defaults_to_info(self):
        assert alert_severity("some_unknown_type") == "info"


class TestSeverityConstants:
    """SEVERITY_COLORS et SEVERITY_ICONS contiennent les clés essentielles."""

    def test_colors_has_critical(self):
        assert "critical" in SEVERITY_COLORS
        assert SEVERITY_COLORS["critical"].startswith("#")

    def test_icons_has_all_levels(self):
        for level in ["critical", "warning", "info", "green", "red"]:
            assert level in SEVERITY_ICONS
