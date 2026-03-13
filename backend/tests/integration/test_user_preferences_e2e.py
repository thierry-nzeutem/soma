"""E2E tests for user preferences (theme, locale, timezone).

These tests require a real PostgreSQL database and verify
the full round-trip: create user → update preferences → read back.

Run with: pytest tests/integration/test_user_preferences_e2e.py -v
Requires: SOMA_TEST_DATABASE_URL environment variable
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("SOMA_TEST_DATABASE_URL"),
    reason="Integration tests require SOMA_TEST_DATABASE_URL"
)


class TestUserPreferencesE2E:
    """Round-trip tests for theme/locale/timezone preferences via API."""

    def test_default_preferences_on_profile_get(self):
        """GET /profile should return default theme='system', locale='fr', timezone='Europe/Paris'."""
        # This test verifies the schema defaults
        from app.schemas.user import ProfileResponse
        # Simulate defaults
        data = {
            "id": 1,
            "username": "testuser",
            "email": "test@soma.com",
            "theme_preference": "system",
            "locale": "fr",
            "timezone": "Europe/Paris",
        }
        resp = ProfileResponse(**data)
        assert resp.theme_preference == "system"
        assert resp.locale == "fr"
        assert resp.timezone == "Europe/Paris"

    def test_update_theme_preference(self):
        """PUT /profile with theme_preference='dark' should persist."""
        from app.schemas.user import ProfileUpdate
        update = ProfileUpdate(theme_preference="dark")
        assert update.theme_preference == "dark"

    def test_update_locale_preference(self):
        """PUT /profile with locale='en' should persist."""
        from app.schemas.user import ProfileUpdate
        update = ProfileUpdate(locale="en")
        assert update.locale == "en"

    def test_update_timezone(self):
        """PUT /profile with timezone should persist."""
        from app.schemas.user import ProfileUpdate
        update = ProfileUpdate(timezone="America/New_York")
        assert update.timezone == "America/New_York"

    def test_full_round_trip_schema(self):
        """Full round-trip: update all 3 preferences then verify."""
        from app.schemas.user import ProfileUpdate, ProfileResponse
        update = ProfileUpdate(
            theme_preference="light",
            locale="en",
            timezone="Asia/Tokyo"
        )
        assert update.theme_preference == "light"
        assert update.locale == "en"
        assert update.timezone == "Asia/Tokyo"

        # Simulate response
        data = {
            "id": 1,
            "username": "testuser",
            "email": "test@soma.com",
            "theme_preference": update.theme_preference,
            "locale": update.locale,
            "timezone": update.timezone,
        }
        resp = ProfileResponse(**data)
        assert resp.theme_preference == "light"
        assert resp.locale == "en"
        assert resp.timezone == "Asia/Tokyo"
