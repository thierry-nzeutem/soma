"""Cross-platform consistency tests.

Verifies that the theme palettes and i18n keys are consistent
between Flutter (SomaColors) and Desktop (CSS variables / JSON messages).

These tests parse the source files directly — no DB needed.
"""

import json
import re
from pathlib import Path

import pytest

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent.parent  # soma/
FLUTTER_COLORS = REPO_ROOT / "mobile" / "lib" / "core" / "theme" / "soma_colors.dart"
DESKTOP_CSS = REPO_ROOT / "desktop" / "src" / "app" / "globals.css"
DESKTOP_FR_JSON = REPO_ROOT / "desktop" / "src" / "lib" / "i18n" / "messages" / "fr.json"
DESKTOP_EN_JSON = REPO_ROOT / "desktop" / "src" / "lib" / "i18n" / "messages" / "en.json"
BACKEND_TRANSLATIONS = REPO_ROOT / "backend" / "app" / "core" / "i18n" / "translations.py"


# ── Theme Consistency ────────────────────────────────────────────────────────

class TestThemeConsistency:
    """Verify Flutter and Desktop theme palettes define the same tokens."""

    def test_flutter_colors_file_exists(self):
        assert FLUTTER_COLORS.exists(), f"Missing {FLUTTER_COLORS}"

    def test_desktop_css_file_exists(self):
        assert DESKTOP_CSS.exists(), f"Missing {DESKTOP_CSS}"

    def test_flutter_has_light_and_dark(self):
        """SomaColors should define both light and dark instances."""
        content = FLUTTER_COLORS.read_text(encoding="utf-8")
        assert "static const light" in content or "static final light" in content, \
            "SomaColors.light not found"
        assert "static const dark" in content or "static final dark" in content, \
            "SomaColors.dark not found"

    def test_desktop_css_has_light_and_dark(self):
        """globals.css should have :root (light) and .dark variables."""
        content = DESKTOP_CSS.read_text(encoding="utf-8")
        assert ":root" in content
        assert ".dark" in content

    def test_desktop_css_has_soma_variables(self):
        """Desktop CSS should define --soma-bg, --soma-surface, etc."""
        content = DESKTOP_CSS.read_text(encoding="utf-8")
        required_vars = ["--soma-bg", "--soma-surface", "--soma-border", "--soma-text"]
        for var in required_vars:
            assert var in content, f"Missing CSS variable {var}"

    def test_accent_color_consistent(self):
        """Accent color #00E5A0 should appear in both platforms."""
        flutter_content = FLUTTER_COLORS.read_text(encoding="utf-8")
        css_content = DESKTOP_CSS.read_text(encoding="utf-8")

        # Flutter uses 0xFF00E5A0 or Color(0xFF00E5A0)
        assert "00E5A0" in flutter_content.upper() or "00e5a0" in flutter_content.lower(), \
            "Flutter accent color #00E5A0 not found"
        assert "00E5A0" in css_content.upper() or "00e5a0" in css_content.lower(), \
            "Desktop accent color #00E5A0 not found"


# ── i18n Consistency ─────────────────────────────────────────────────────────

class TestI18nConsistency:
    """Verify i18n keys match between Desktop FR and EN JSON files."""

    def test_desktop_fr_json_exists(self):
        assert DESKTOP_FR_JSON.exists()

    def test_desktop_en_json_exists(self):
        assert DESKTOP_EN_JSON.exists()

    def test_desktop_fr_en_same_keys(self):
        """FR and EN JSON files should have identical key structure."""
        fr = json.loads(DESKTOP_FR_JSON.read_text(encoding="utf-8"))
        en = json.loads(DESKTOP_EN_JSON.read_text(encoding="utf-8"))

        def flat_keys(d, prefix=""):
            keys = set()
            for k, v in d.items():
                full = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys |= flat_keys(v, full)
                else:
                    keys.add(full)
            return keys

        fr_keys = flat_keys(fr)
        en_keys = flat_keys(en)

        missing_in_en = fr_keys - en_keys
        missing_in_fr = en_keys - fr_keys

        assert not missing_in_en, f"Keys in FR but missing in EN: {missing_in_en}"
        assert not missing_in_fr, f"Keys in EN but missing in FR: {missing_in_fr}"

    def test_desktop_json_no_empty_values(self):
        """No translation value should be empty string."""
        fr = json.loads(DESKTOP_FR_JSON.read_text(encoding="utf-8"))
        en = json.loads(DESKTOP_EN_JSON.read_text(encoding="utf-8"))

        def check_empty(d, prefix="", locale=""):
            empties = []
            for k, v in d.items():
                full = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    empties.extend(check_empty(v, full, locale))
                elif isinstance(v, str) and not v.strip():
                    empties.append(f"{locale}:{full}")
            return empties

        empties = check_empty(fr, locale="fr") + check_empty(en, locale="en")
        assert not empties, f"Empty translation values: {empties}"

    def test_backend_translations_have_fr_and_en(self):
        """Backend translations.py should define both FR and EN for each key."""
        if not BACKEND_TRANSLATIONS.exists():
            pytest.skip("Backend translations file not found")

        content = BACKEND_TRANSLATIONS.read_text(encoding="utf-8")
        assert '"fr"' in content or "'fr'" in content
        assert '"en"' in content or "'en'" in content

    def test_backend_supported_locales(self):
        """Backend should support fr and en locales."""
        from app.core.i18n import get_supported_locales
        locales = get_supported_locales()
        assert "fr" in locales
        assert "en" in locales


# ── Flutter i18n ─────────────────────────────────────────────────────────────

class TestFlutterI18n:
    """Verify Flutter ARB files exist and are consistent."""

    def test_flutter_fr_arb_exists(self):
        arb = REPO_ROOT / "mobile" / "lib" / "l10n" / "app_fr.arb"
        assert arb.exists(), f"Missing {arb}"

    def test_flutter_en_arb_exists(self):
        arb = REPO_ROOT / "mobile" / "lib" / "l10n" / "app_en.arb"
        assert arb.exists(), f"Missing {arb}"

    def test_flutter_arb_valid_json(self):
        """Both ARB files should be valid JSON."""
        fr_arb = REPO_ROOT / "mobile" / "lib" / "l10n" / "app_fr.arb"
        en_arb = REPO_ROOT / "mobile" / "lib" / "l10n" / "app_en.arb"

        fr = json.loads(fr_arb.read_text(encoding="utf-8"))
        en = json.loads(en_arb.read_text(encoding="utf-8"))

        # Should have @@locale
        assert fr.get("@@locale") == "fr"
        assert en.get("@@locale") == "en"

    def test_flutter_arb_keys_match(self):
        """FR and EN ARB files should have matching non-metadata keys."""
        fr_arb = REPO_ROOT / "mobile" / "lib" / "l10n" / "app_fr.arb"
        en_arb = REPO_ROOT / "mobile" / "lib" / "l10n" / "app_en.arb"

        fr = json.loads(fr_arb.read_text(encoding="utf-8"))
        en = json.loads(en_arb.read_text(encoding="utf-8"))

        # Filter out @@ metadata keys and @key description keys
        fr_keys = {k for k in fr if not k.startswith("@")}
        en_keys = {k for k in en if not k.startswith("@")}

        missing_in_en = fr_keys - en_keys
        missing_in_fr = en_keys - fr_keys

        assert not missing_in_en, f"Keys in FR ARB but missing in EN: {missing_in_en}"
        assert not missing_in_fr, f"Keys in EN ARB but missing in FR: {missing_in_fr}"

    def test_flutter_l10n_yaml_exists(self):
        """l10n.yaml config should exist."""
        config = REPO_ROOT / "mobile" / "l10n.yaml"
        assert config.exists()
