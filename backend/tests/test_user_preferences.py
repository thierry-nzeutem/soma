"""Tests pour les preferences utilisateur — theme, locale, timezone (V011)."""

import pytest
from pydantic import ValidationError

from app.schemas.user import ProfileUpdate, ProfileResponse


# ── theme_preference validation ──────────────────────────────────────

class TestThemePreference:
    """Validation du champ theme_preference."""

    def test_theme_light_accepted(self):
        data = ProfileUpdate(theme_preference="light")
        assert data.theme_preference == "light"

    def test_theme_dark_accepted(self):
        data = ProfileUpdate(theme_preference="dark")
        assert data.theme_preference == "dark"

    def test_theme_system_accepted(self):
        data = ProfileUpdate(theme_preference="system")
        assert data.theme_preference == "system"

    def test_theme_invalid_value_rejected(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(theme_preference="auto")

    def test_theme_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(theme_preference="")

    def test_theme_none_is_valid(self):
        """None signifie 'pas de mise a jour' (partial update)."""
        data = ProfileUpdate(theme_preference=None)
        assert data.theme_preference is None

    def test_theme_default_in_response(self):
        resp = ProfileResponse(
            id="00000000-0000-0000-0000-000000000001",
            first_name=None, age=None, sex=None, height_cm=None,
            goal_weight_kg=None, primary_goal=None, activity_level=None,
            fitness_level=None, dietary_regime=None,
            intermittent_fasting=False, fasting_protocol=None,
            meals_per_day=3, home_equipment=None, gym_access=False,
            avg_energy_level=None, perceived_sleep_quality=None,
            computed=None, profile_completeness_score=None,
        )
        assert resp.theme_preference == "system"


# ── locale validation ────────────────────────────────────────────────

class TestLocale:
    """Validation du champ locale."""

    def test_locale_fr_accepted(self):
        data = ProfileUpdate(locale="fr")
        assert data.locale == "fr"

    def test_locale_en_accepted(self):
        data = ProfileUpdate(locale="en")
        assert data.locale == "en"

    def test_locale_invalid_rejected(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(locale="de")

    def test_locale_empty_rejected(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(locale="")

    def test_locale_none_is_valid(self):
        data = ProfileUpdate(locale=None)
        assert data.locale is None

    def test_locale_default_in_response(self):
        resp = ProfileResponse(
            id="00000000-0000-0000-0000-000000000001",
            first_name=None, age=None, sex=None, height_cm=None,
            goal_weight_kg=None, primary_goal=None, activity_level=None,
            fitness_level=None, dietary_regime=None,
            intermittent_fasting=False, fasting_protocol=None,
            meals_per_day=3, home_equipment=None, gym_access=False,
            avg_energy_level=None, perceived_sleep_quality=None,
            computed=None, profile_completeness_score=None,
        )
        assert resp.locale == "fr"


# ── timezone validation ──────────────────────────────────────────────

class TestTimezone:
    """Validation du champ timezone."""

    def test_timezone_europe_paris(self):
        data = ProfileUpdate(timezone="Europe/Paris")
        assert data.timezone == "Europe/Paris"

    def test_timezone_america_new_york(self):
        data = ProfileUpdate(timezone="America/New_York")
        assert data.timezone == "America/New_York"

    def test_timezone_utc(self):
        data = ProfileUpdate(timezone="UTC")
        assert data.timezone == "UTC"

    def test_timezone_asia_tokyo(self):
        data = ProfileUpdate(timezone="Asia/Tokyo")
        assert data.timezone == "Asia/Tokyo"

    def test_timezone_none_is_valid(self):
        data = ProfileUpdate(timezone=None)
        assert data.timezone is None

    def test_timezone_default_in_response(self):
        resp = ProfileResponse(
            id="00000000-0000-0000-0000-000000000001",
            first_name=None, age=None, sex=None, height_cm=None,
            goal_weight_kg=None, primary_goal=None, activity_level=None,
            fitness_level=None, dietary_regime=None,
            intermittent_fasting=False, fasting_protocol=None,
            meals_per_day=3, home_equipment=None, gym_access=False,
            avg_energy_level=None, perceived_sleep_quality=None,
            computed=None, profile_completeness_score=None,
        )
        assert resp.timezone == "Europe/Paris"


# ── Combined / partial update ────────────────────────────────────────

class TestCombinedPreferences:
    """Tests de mise a jour partielle combinant preferences + champs existants."""

    def test_partial_update_theme_only(self):
        data = ProfileUpdate(theme_preference="dark")
        dump = data.model_dump(exclude_none=True)
        assert dump == {"theme_preference": "dark"}

    def test_partial_update_locale_only(self):
        data = ProfileUpdate(locale="en")
        dump = data.model_dump(exclude_none=True)
        assert dump == {"locale": "en"}

    def test_partial_update_timezone_only(self):
        data = ProfileUpdate(timezone="America/Los_Angeles")
        dump = data.model_dump(exclude_none=True)
        assert dump == {"timezone": "America/Los_Angeles"}

    def test_partial_update_all_three(self):
        data = ProfileUpdate(theme_preference="light", locale="en", timezone="UTC")
        dump = data.model_dump(exclude_none=True)
        assert dump == {"theme_preference": "light", "locale": "en", "timezone": "UTC"}

    def test_partial_update_prefs_with_existing_fields(self):
        data = ProfileUpdate(theme_preference="dark", age=30)
        dump = data.model_dump(exclude_none=True)
        assert dump == {"theme_preference": "dark", "age": 30}

    def test_no_prefs_leaves_dump_empty(self):
        data = ProfileUpdate()
        dump = data.model_dump(exclude_none=True)
        assert dump == {}

    def test_response_includes_all_preferences(self):
        resp = ProfileResponse(
            id="00000000-0000-0000-0000-000000000001",
            first_name="Test", age=25, sex="male", height_cm=180.0,
            goal_weight_kg=75.0, primary_goal="maintenance",
            activity_level="moderate", fitness_level="intermediate",
            dietary_regime=None,
            intermittent_fasting=False, fasting_protocol=None,
            meals_per_day=3, home_equipment=None, gym_access=True,
            avg_energy_level=7, perceived_sleep_quality=8,
            computed=None, profile_completeness_score=85.0,
            theme_preference="light",
            locale="en",
            timezone="America/New_York",
        )
        assert resp.theme_preference == "light"
        assert resp.locale == "en"
        assert resp.timezone == "America/New_York"
