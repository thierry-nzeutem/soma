"""
SOMA LOT 18 — Tests unitaires analytics produit.

Couvre :
  - track_event() : persistance silencieuse fire-and-forget
  - EVENTS : constantes reconnues
  - TrackEventRequest / TrackEventResponse schémas Pydantic
  - AnalyticsEventDB : champs et table

~10 tests purs, aucune dépendance DB réelle (mock db).
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.analytics import track_event, EVENTS
from app.core.analytics.tracker import track_event as _track_event_direct
from app.models.analytics import AnalyticsEventDB
from app.api.v1.endpoints.analytics_events import TrackEventRequest, TrackEventResponse


# ── Tests EVENTS constants ──────────────────────────────────────────────────

class TestEventsConstants:
    """EVENTS doit contenir les événements produit standards."""

    def test_events_is_set(self):
        assert isinstance(EVENTS, (set, frozenset))

    def test_onboarding_complete_defined(self):
        assert "onboarding_complete" in EVENTS

    def test_morning_briefing_view_defined(self):
        assert "morning_briefing_view" in EVENTS

    def test_quick_advice_requested_defined(self):
        assert "quick_advice_requested" in EVENTS

    def test_workout_logged_defined(self):
        assert "workout_logged" in EVENTS

    def test_nutrition_logged_defined(self):
        assert "nutrition_logged" in EVENTS

    def test_events_count_reasonable(self):
        assert len(EVENTS) >= 9


# ── Tests TrackEventRequest schéma ─────────────────────────────────────────

class TestTrackEventRequest:
    """Validation du schéma de requête analytics."""

    def test_valid_event_name(self):
        req = TrackEventRequest(event_name="morning_briefing_view")
        assert req.event_name == "morning_briefing_view"

    def test_with_properties(self):
        req = TrackEventRequest(
            event_name="journal_entry",
            properties={"type": "workout", "duration_min": 45},
        )
        assert req.properties["type"] == "workout"

    def test_no_properties_is_none(self):
        req = TrackEventRequest(event_name="app_open")
        assert req.properties is None

    def test_event_name_max_100_chars(self):
        from pydantic import ValidationError
        long_name = "a" * 101
        with pytest.raises(ValidationError):
            TrackEventRequest(event_name=long_name)

    def test_event_name_100_chars_valid(self):
        name = "a" * 100
        req = TrackEventRequest(event_name=name)
        assert len(req.event_name) == 100


# ── Tests AnalyticsEventDB modèle ──────────────────────────────────────────

class TestAnalyticsEventDB:
    """Vérification des métadonnées du modèle ORM."""

    def test_tablename(self):
        assert AnalyticsEventDB.__tablename__ == "analytics_events"

    def test_has_user_id_column(self):
        cols = [c.name for c in AnalyticsEventDB.__table__.columns]
        assert "user_id" in cols

    def test_has_event_name_column(self):
        cols = [c.name for c in AnalyticsEventDB.__table__.columns]
        assert "event_name" in cols

    def test_has_properties_column(self):
        cols = [c.name for c in AnalyticsEventDB.__table__.columns]
        assert "properties" in cols

    def test_has_created_at_column(self):
        cols = [c.name for c in AnalyticsEventDB.__table__.columns]
        assert "created_at" in cols


# ── Tests track_event comportement ─────────────────────────────────────────

class TestTrackEventFunction:
    """track_event doit être fire-and-forget (silencieux en cas d'erreur)."""

    @pytest.mark.asyncio
    async def test_track_event_adds_to_db(self):
        """track_event crée un AnalyticsEventDB et l'ajoute à la session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        user_id = uuid.uuid4()

        # On patche AnalyticsEventDB pour isoler la logique de track_event
        with patch("app.core.analytics.tracker.AnalyticsEventDB") as MockEvent:
            mock_instance = MagicMock()
            MockEvent.return_value = mock_instance

            await track_event(db, user_id, "app_open", {"source": "test"})

            MockEvent.assert_called_once()
            db.add.assert_called_once_with(mock_instance)
            call_kwargs = MockEvent.call_args[1]
            assert call_kwargs.get("user_id") == user_id
            assert call_kwargs.get("event_name") == "app_open"
            assert call_kwargs.get("properties") == {"source": "test"}

    @pytest.mark.asyncio
    async def test_track_event_silent_on_db_error(self):
        """track_event ne doit jamais propager d'exception."""
        db = AsyncMock()
        db.commit.side_effect = Exception("DB is down")
        user_id = uuid.uuid4()

        # Ne doit pas lever d'exception
        await track_event(db, user_id, "onboarding_complete")
        # Pas d'assertion supplémentaire — le silence est le comportement attendu

    @pytest.mark.asyncio
    async def test_track_event_no_properties(self):
        """Appel sans properties est valide (properties=None)."""
        db = AsyncMock()
        db.commit = AsyncMock()
        user_id = uuid.uuid4()

        with patch("app.core.analytics.tracker.AnalyticsEventDB") as MockEvent:
            mock_instance = MagicMock()
            MockEvent.return_value = mock_instance

            await track_event(db, user_id, "twin_viewed")
            call_kwargs = MockEvent.call_args[1]
            assert call_kwargs.get("properties") is None

    @pytest.mark.asyncio
    async def test_track_event_name_truncated_at_100(self):
        """Le nom d'événement est tronqué à 100 caractères."""
        db = AsyncMock()
        db.commit = AsyncMock()
        user_id = uuid.uuid4()
        long_name = "x" * 200

        with patch("app.core.analytics.tracker.AnalyticsEventDB") as MockEvent:
            mock_instance = MagicMock()
            MockEvent.return_value = mock_instance

            await track_event(db, user_id, long_name)
            call_kwargs = MockEvent.call_args[1]
            assert len(call_kwargs.get("event_name", "")) == 100
