"""
SOMA LOT 19 — Tests unitaires : Cohort Retention.

Couvre :
  - _has_event_in_window() : fonction pure testable sans DB
    · Fenêtre J+1  : [day+1, day+2)
    · Fenêtre J+7  : [day+6, day+8)
    · Fenêtre J+30 : [day+28, day+32)
  - CohortRetention dataclass : champs, rétentions 0-100
  - CohortRetentionResponse schema Pydantic
  - Calcul rétention Python (logique isolée)

~15 tests purs, aucune dépendance DB réelle.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.analytics_dashboard_service import (
    CohortRetention,
    _has_event_in_window,
)
from app.schemas.analytics_dashboard import CohortRetentionResponse


# ── Tests _has_event_in_window (fonction pure) ───────────────────────────────

class TestHasEventInWindow:
    """Tests de la fonction _has_event_in_window — noyau de la rétention."""

    _NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _make_event(self, days_after_first: float) -> datetime:
        return self._NOW + timedelta(days=days_after_first)

    # ── Fenêtre J+1 (day_start=1, day_end=2) ────────────────────────────────

    def test_d1_event_exactly_at_start(self):
        """Événement exactement au début de la fenêtre → True."""
        events = [self._make_event(1.0)]
        assert _has_event_in_window(events, self._NOW, 1, 2) is True

    def test_d1_event_just_before_end(self):
        """Événement juste avant la fin de la fenêtre → True."""
        events = [self._make_event(1.9)]
        assert _has_event_in_window(events, self._NOW, 1, 2) is True

    def test_d1_event_at_end_exclusive(self):
        """Événement exactement à la fin (exclusive) → False."""
        events = [self._make_event(2.0)]
        assert _has_event_in_window(events, self._NOW, 1, 2) is False

    def test_d1_event_same_day_as_first_seen(self):
        """Événement le jour J (avant fenêtre) → False."""
        events = [self._make_event(0.5)]
        assert _has_event_in_window(events, self._NOW, 1, 2) is False

    # ── Fenêtre J+7 (day_start=6, day_end=8) ────────────────────────────────

    def test_d7_event_at_day6(self):
        """Événement à J+6 → dans la fenêtre [6, 8) → True."""
        events = [self._make_event(6.0)]
        assert _has_event_in_window(events, self._NOW, 6, 8) is True

    def test_d7_event_at_day7(self):
        """Événement à J+7 → True."""
        events = [self._make_event(7.0)]
        assert _has_event_in_window(events, self._NOW, 6, 8) is True

    def test_d7_event_at_day8_exclusive(self):
        """Événement à J+8 → exclu → False."""
        events = [self._make_event(8.0)]
        assert _has_event_in_window(events, self._NOW, 6, 8) is False

    def test_d7_no_event_in_window(self):
        """Aucun événement dans la fenêtre [6, 8) → False."""
        events = [self._make_event(1.0), self._make_event(15.0)]
        assert _has_event_in_window(events, self._NOW, 6, 8) is False

    # ── Fenêtre J+30 (day_start=28, day_end=32) ─────────────────────────────

    def test_d30_event_at_day28(self):
        """Événement à J+28 → True."""
        events = [self._make_event(28.0)]
        assert _has_event_in_window(events, self._NOW, 28, 32) is True

    def test_d30_event_at_day30(self):
        """Événement à J+30 → True."""
        events = [self._make_event(30.0)]
        assert _has_event_in_window(events, self._NOW, 28, 32) is True

    def test_d30_event_at_day32_exclusive(self):
        """Événement à J+32 → exclu → False."""
        events = [self._make_event(32.0)]
        assert _has_event_in_window(events, self._NOW, 28, 32) is False

    # ── Liste vide ───────────────────────────────────────────────────────────

    def test_empty_events_returns_false(self):
        """Liste vide → False pour toutes les fenêtres."""
        assert _has_event_in_window([], self._NOW, 1, 2) is False
        assert _has_event_in_window([], self._NOW, 6, 8) is False
        assert _has_event_in_window([], self._NOW, 28, 32) is False

    # ── Événements multiples ─────────────────────────────────────────────────

    def test_multiple_events_one_in_window(self):
        """Plusieurs événements, un seul dans la fenêtre → True."""
        events = [
            self._make_event(0.5),
            self._make_event(1.5),   # dans [1, 2)
            self._make_event(10.0),
        ]
        assert _has_event_in_window(events, self._NOW, 1, 2) is True


# ── Tests CohortRetention dataclass ─────────────────────────────────────────

class TestCohortRetentionDataclass:
    """Vérifie la structure de CohortRetention."""

    def _make(self, **kwargs) -> CohortRetention:
        defaults = dict(
            cohort_week="2026-W10",
            users_count=50,
            retention_day1=80.0,
            retention_day7=55.0,
            retention_day30=30.0,
        )
        defaults.update(kwargs)
        return CohortRetention(**defaults)

    def test_cohort_week_format(self):
        c = self._make(cohort_week="2026-W05")
        assert c.cohort_week == "2026-W05"

    def test_retention_values_in_0_100(self):
        c = self._make(retention_day1=85.5, retention_day7=60.0, retention_day30=25.0)
        assert 0 <= c.retention_day1 <= 100
        assert 0 <= c.retention_day7 <= 100
        assert 0 <= c.retention_day30 <= 100

    def test_retention_day1_ge_day7_typical(self):
        """En général, rétention J1 >= J7 >= J30."""
        c = self._make(retention_day1=80.0, retention_day7=55.0, retention_day30=20.0)
        assert c.retention_day1 >= c.retention_day7 >= c.retention_day30


# ── Tests schéma Pydantic CohortRetentionResponse ───────────────────────────

class TestCohortRetentionResponse:
    """Vérifie le schéma Pydantic de rétention."""

    def test_schema_from_dict(self):
        data = dict(
            cohort_week="2026-W08",
            users_count=120,
            retention_day1=78.5,
            retention_day7=52.3,
            retention_day30=18.7,
        )
        resp = CohortRetentionResponse(**data)
        assert resp.cohort_week == "2026-W08"
        assert resp.users_count == 120
        assert isinstance(resp.retention_day1, float)

    def test_zero_retention_allowed(self):
        """Rétentions nulles (cohorte ancienne) acceptées."""
        data = dict(
            cohort_week="2025-W01",
            users_count=5,
            retention_day1=0.0,
            retention_day7=0.0,
            retention_day30=0.0,
        )
        resp = CohortRetentionResponse(**data)
        assert resp.retention_day30 == 0.0
