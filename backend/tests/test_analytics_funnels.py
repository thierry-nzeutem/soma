"""
SOMA LOT 19 — Tests unitaires : Analytics Funnels.

Couvre :
  - _FUNNEL_STEPS : constante, ordre, noms d'événements
  - FunnelStep dataclass : champs, calcul conversion/drop-off
  - OnboardingFunnel dataclass : steps, overall_conversion_rate
  - Calcul conversion step-by-step (logique isolée)
  - Robustesse division par zéro (0 utilisateurs au step 1)
  - Schemas Pydantic FunnelStepResponse + OnboardingFunnelResponse

~13 tests purs, aucune dépendance DB réelle.
"""
from __future__ import annotations

import pytest

from app.services.analytics_dashboard_service import (
    FunnelStep,
    OnboardingFunnel,
    _FUNNEL_STEPS,
)
from app.schemas.analytics_dashboard import (
    FunnelStepResponse,
    OnboardingFunnelResponse,
)


# ── Tests _FUNNEL_STEPS constante ───────────────────────────────────────────

class TestFunnelStepsConstant:
    """_FUNNEL_STEPS doit contenir 5 étapes dans le bon ordre."""

    def test_has_five_steps(self):
        assert len(_FUNNEL_STEPS) == 5

    def test_first_step_is_app_open(self):
        name, event = _FUNNEL_STEPS[0]
        assert event == "app_open"

    def test_second_step_is_onboarding_complete(self):
        name, event = _FUNNEL_STEPS[1]
        assert event == "onboarding_complete"

    def test_third_step_is_morning_briefing(self):
        name, event = _FUNNEL_STEPS[2]
        assert event == "morning_briefing_view"

    def test_fourth_step_is_journal_entry(self):
        name, event = _FUNNEL_STEPS[3]
        assert event == "journal_entry"

    def test_fifth_step_is_coach_question(self):
        name, event = _FUNNEL_STEPS[4]
        assert event == "coach_question"

    def test_all_steps_have_name_and_event(self):
        for step_name, event_name in _FUNNEL_STEPS:
            assert isinstance(step_name, str) and len(step_name) > 0
            assert isinstance(event_name, str) and len(event_name) > 0


# ── Tests calcul conversion step-by-step ────────────────────────────────────

class TestFunnelConversionCalc:
    """Vérifie le calcul de conversion isolé depuis get_funnel_onboarding."""

    def _simulate_steps(self, counts: list[int], days: int = 30) -> OnboardingFunnel:
        """Réplique la logique Python de get_funnel_onboarding sans DB."""
        step_counts = [
            (_FUNNEL_STEPS[i][0], _FUNNEL_STEPS[i][1], count)
            for i, count in enumerate(counts)
        ]
        steps = []
        for i, (name, event, count) in enumerate(step_counts):
            if i == 0:
                conversion = 100.0
                drop_off = 0.0
            else:
                prev_count = step_counts[i - 1][2]
                conversion = round(count / prev_count * 100, 1) if prev_count > 0 else 0.0
                drop_off = round(100.0 - conversion, 1)
            steps.append(FunnelStep(
                step_index=i + 1,
                step_name=name,
                event_name=event,
                users_count=count,
                conversion_from_previous=conversion,
                drop_off_rate=drop_off,
            ))

        top_count = step_counts[0][2] if step_counts else 0
        last_count = step_counts[-1][2] if step_counts else 0
        overall = round(last_count / top_count * 100, 1) if top_count > 0 else 0.0

        return OnboardingFunnel(period_days=days, steps=steps, overall_conversion_rate=overall)

    def test_first_step_always_100_conversion(self):
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        assert funnel.steps[0].conversion_from_previous == 100.0
        assert funnel.steps[0].drop_off_rate == 0.0

    def test_conversion_decreases_along_funnel(self):
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        # Chaque étape doit avoir une conversion ≤ 100%
        for step in funnel.steps[1:]:
            assert step.conversion_from_previous <= 100.0

    def test_step2_conversion_80_percent(self):
        """1000 → 800 : conversion = 80.0%."""
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        assert funnel.steps[1].conversion_from_previous == 80.0

    def test_step2_dropoff_20_percent(self):
        """1000 → 800 : drop-off = 20.0%."""
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        assert funnel.steps[1].drop_off_rate == 20.0

    def test_overall_conversion_rate_correct(self):
        """1000 → 200 : overall = 20.0%."""
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        assert funnel.overall_conversion_rate == 20.0

    def test_zero_step1_overall_is_zero(self):
        """0 utilisateurs au step 1 → overall = 0.0 (division par zéro sûre)."""
        funnel = self._simulate_steps([0, 0, 0, 0, 0])
        assert funnel.overall_conversion_rate == 0.0

    def test_perfect_funnel_100_overall(self):
        """Tous les utilisateurs complètent le funnel → 100.0%."""
        funnel = self._simulate_steps([500, 500, 500, 500, 500])
        assert funnel.overall_conversion_rate == 100.0

    def test_five_steps_returned(self):
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        assert len(funnel.steps) == 5

    def test_step_index_is_1_based(self):
        funnel = self._simulate_steps([1000, 800, 600, 400, 200])
        for i, step in enumerate(funnel.steps):
            assert step.step_index == i + 1


# ── Tests schemas Pydantic ───────────────────────────────────────────────────

class TestFunnelSchemas:
    """Vérifie les schémas Pydantic FunnelStep et OnboardingFunnel."""

    def test_funnel_step_response_valid(self):
        data = dict(
            step_index=1,
            step_name="App Ouvert",
            event_name="app_open",
            users_count=1000,
            conversion_from_previous=100.0,
            drop_off_rate=0.0,
        )
        step = FunnelStepResponse(**data)
        assert step.step_index == 1
        assert step.conversion_from_previous == 100.0

    def test_onboarding_funnel_response_valid(self):
        steps = [
            FunnelStepResponse(
                step_index=i + 1,
                step_name=f"Step {i+1}",
                event_name=f"event_{i+1}",
                users_count=1000 - i * 100,
                conversion_from_previous=100.0 if i == 0 else 90.0,
                drop_off_rate=0.0 if i == 0 else 10.0,
            )
            for i in range(5)
        ]
        funnel = OnboardingFunnelResponse(
            period_days=30,
            steps=steps,
            overall_conversion_rate=60.0,
        )
        assert len(funnel.steps) == 5
        assert funnel.overall_conversion_rate == 60.0
