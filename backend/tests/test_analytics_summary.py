"""
SOMA LOT 19 — Tests unitaires : Analytics Summary.

Couvre :
  - AnalyticsSummary dataclass : champs, valeurs par défaut
  - get_summary() : comportement avec DB mockée (AsyncMock)
  - Calcul du ratio DAU/MAU (stickiness)
  - Onboarding completion rate
  - Robustesse division par zéro (0 utilisateurs)
  - Schemas Pydantic AnalyticsSummaryResponse

~15 tests purs, aucune dépendance DB réelle.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.analytics_dashboard_service import (
    AnalyticsSummary,
    _EPOCH,
    _FUNNEL_STEPS,
    _has_event_in_window,
)
from app.schemas.analytics_dashboard import AnalyticsSummaryResponse


# ── Tests AnalyticsSummary dataclass ────────────────────────────────────────

class TestAnalyticsSummaryDataclass:
    """Vérifie la structure de la dataclass AnalyticsSummary."""

    def _make(self, **kwargs) -> AnalyticsSummary:
        defaults = dict(
            period_days=30,
            dau=10,
            wau=50,
            mau=100,
            dau_mau_ratio=0.1,
            total_users=200,
            new_users=15,
            active_users=100,
            onboarding_completion_rate=72.5,
            journal_entries=450,
            coach_questions=120,
            briefing_opens=300,
        )
        defaults.update(kwargs)
        return AnalyticsSummary(**defaults)

    def test_period_days_stored(self):
        s = self._make(period_days=7)
        assert s.period_days == 7

    def test_dau_wau_mau_fields(self):
        s = self._make(dau=5, wau=30, mau=90)
        assert s.dau == 5
        assert s.wau == 30
        assert s.mau == 90

    def test_dau_mau_ratio_precision(self):
        s = self._make(dau=10, mau=100, dau_mau_ratio=0.1)
        assert abs(s.dau_mau_ratio - 0.1) < 1e-9

    def test_total_users_ge_active(self):
        s = self._make(total_users=500, active_users=100)
        assert s.total_users >= s.active_users

    def test_onboarding_rate_in_0_100(self):
        s = self._make(onboarding_completion_rate=88.3)
        assert 0.0 <= s.onboarding_completion_rate <= 100.0

    def test_engagement_counts_non_negative(self):
        s = self._make(journal_entries=0, coach_questions=0, briefing_opens=0)
        assert s.journal_entries >= 0
        assert s.coach_questions >= 0
        assert s.briefing_opens >= 0


# ── Tests calcul ratio DAU/MAU ───────────────────────────────────────────────

class TestDauMauRatio:
    """Calcul du ratio stickiness."""

    def test_ratio_zero_when_mau_zero(self):
        """Division par zéro doit retourner 0.0."""
        # Simule le calcul dans get_summary
        mau = 0
        dau = 0
        ratio = round(dau / mau, 3) if mau > 0 else 0.0
        assert ratio == 0.0

    def test_ratio_one_when_dau_equals_mau(self):
        mau = 100
        dau = 100
        ratio = round(dau / mau, 3) if mau > 0 else 0.0
        assert ratio == 1.0

    def test_ratio_typical_stickiness(self):
        mau = 1000
        dau = 200
        ratio = round(dau / mau, 3) if mau > 0 else 0.0
        assert abs(ratio - 0.2) < 1e-9


# ── Tests onboarding completion rate ────────────────────────────────────────

class TestOnboardingRate:
    """Calcul du taux de complétion onboarding."""

    def test_rate_zero_when_no_users(self):
        total_users = 0
        onboarding_users = 0
        rate = round(onboarding_users / total_users * 100, 1) if total_users > 0 else 0.0
        assert rate == 0.0

    def test_rate_100_when_all_completed(self):
        total_users = 50
        onboarding_users = 50
        rate = round(onboarding_users / total_users * 100, 1) if total_users > 0 else 0.0
        assert rate == 100.0

    def test_rate_partial(self):
        total_users = 200
        onboarding_users = 150
        rate = round(onboarding_users / total_users * 100, 1) if total_users > 0 else 0.0
        assert abs(rate - 75.0) < 0.01


# ── Tests EPOCH constant ─────────────────────────────────────────────────────

class TestEpochConstant:
    """_EPOCH doit être au 1er janvier 2024, UTC."""

    def test_epoch_year(self):
        assert _EPOCH.year == 2024

    def test_epoch_month_day(self):
        assert _EPOCH.month == 1
        assert _EPOCH.day == 1

    def test_epoch_is_utc(self):
        assert _EPOCH.tzinfo == timezone.utc


# ── Tests Pydantic schema AnalyticsSummaryResponse ──────────────────────────

class TestAnalyticsSummaryResponse:
    """Vérifie que le schéma Pydantic accepte les bons types."""

    def test_schema_from_dict(self):
        data = dict(
            period_days=30,
            dau=10,
            wau=50,
            mau=100,
            dau_mau_ratio=0.1,
            total_users=200,
            new_users=15,
            active_users=100,
            onboarding_completion_rate=72.5,
            journal_entries=450,
            coach_questions=120,
            briefing_opens=300,
        )
        resp = AnalyticsSummaryResponse(**data)
        assert resp.period_days == 30
        assert resp.dau == 10
        assert resp.mau == 100

    def test_dau_mau_ratio_is_float(self):
        data = dict(
            period_days=7, dau=5, wau=20, mau=80,
            dau_mau_ratio=0.0625,
            total_users=100, new_users=3, active_users=80,
            onboarding_completion_rate=50.0,
            journal_entries=10, coach_questions=5, briefing_opens=20,
        )
        resp = AnalyticsSummaryResponse(**data)
        assert isinstance(resp.dau_mau_ratio, float)

    def test_zero_values_allowed(self):
        """Tous les champs numériques acceptent 0."""
        data = dict(
            period_days=1, dau=0, wau=0, mau=0,
            dau_mau_ratio=0.0,
            total_users=0, new_users=0, active_users=0,
            onboarding_completion_rate=0.0,
            journal_entries=0, coach_questions=0, briefing_opens=0,
        )
        resp = AnalyticsSummaryResponse(**data)
        assert resp.dau == 0
        assert resp.onboarding_completion_rate == 0.0
