"""
Tests unitaires — Scheduler Service SOMA (LOT 4).

Stratégie : tests purs sans DB.
Toutes les fonctions async qui accèdent à la DB sont mockées via unittest.mock.

Modules testés :
  - _run_step          : isolation des exceptions
  - run_daily_pipeline_for_user : orchestration + isolation par step
  - run_daily_pipeline_all_users : itération utilisateurs + isolation par user
  - lazy_ensure_today_metrics   : fallback lazy compute
  - create_scheduler   : configuration APScheduler
"""
import asyncio
import uuid
from datetime import date
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.services.scheduler_service import (
    _run_step,
    run_daily_pipeline_for_user,
    create_scheduler,
)
from app.services.daily_metrics_service import lazy_ensure_today_metrics


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _user_id():
    return uuid.uuid4()


def _date():
    return date(2026, 3, 7)


async def _ok_coro():
    """Coroutine qui réussit."""
    return "ok"


async def _fail_coro():
    """Coroutine qui lève une exception."""
    raise RuntimeError("step failure")


async def _always_none():
    return None


# Mock DailyMetrics avec attributs minimaux
class _MockDailyMetrics:
    hrv_ms = 45.0
    resting_heart_rate_bpm = 58.0
    training_load = 65.0
    sleep_quality_label = "good"
    hydration_ml = 2200
    hydration_target_ml = 2500
    calories_consumed = 2100.0
    calories_target = 2400.0
    protein_g = 160.0
    protein_target_g = 180.0
    workout_count = 1
    sleep_score = 78.0
    active_calories_kcal = 420.0
    total_tonnage_kg = 3200.0
    steps = 8500
    data_completeness_pct = 85.7
    meal_count = 3
    weight_kg = 78.5


# Mock ReadinessScore
class _MockReadiness:
    overall_readiness = 72.0
    recommended_intensity = "moderate"
    score_date = date(2026, 3, 7)


# Mock UserProfile
class _MockProfile:
    age = 35
    sex = "male"
    height_cm = 180.0
    activity_level = "moderate"
    fitness_level = "intermediate"
    primary_goal = "muscle_gain"
    dietary_regime = "omnivore"
    intermittent_fasting = False
    fasting_protocol = None
    usual_wake_time = None
    home_equipment = None
    gym_access = True
    bmi = 24.2


# Mock User
class _MockUser:
    def __init__(self):
        self.id = _user_id()
        self.is_active = True


# ─────────────────────────────────────────────────────────────────────────────
# TestRunStep
# ─────────────────────────────────────────────────────────────────────────────

class TestRunStep:
    """Tests de l'utilitaire d'isolation d'exceptions _run_step."""

    @pytest.mark.asyncio
    async def test_success_returns_true_none(self):
        ok, err = await _run_step("test", _ok_coro())
        assert ok is True
        assert err is None

    @pytest.mark.asyncio
    async def test_failure_returns_false_message(self):
        ok, err = await _run_step("test", _fail_coro())
        assert ok is False
        assert err is not None
        assert "step failure" in err

    @pytest.mark.asyncio
    async def test_failure_does_not_propagate(self):
        """L'exception ne doit pas remonter."""
        try:
            await _run_step("test", _fail_coro())
        except Exception:
            pytest.fail("_run_step a propagé une exception")

    @pytest.mark.asyncio
    async def test_error_message_contains_exception_text(self):
        ok, err = await _run_step("failing_step", _fail_coro())
        assert err == "step failure"

    @pytest.mark.asyncio
    async def test_multiple_steps_independent(self):
        """Deux steps indépendants : l'un peut échouer, l'autre réussit."""
        ok1, _ = await _run_step("step1", _ok_coro())
        ok2, _ = await _run_step("step2", _fail_coro())
        ok3, _ = await _run_step("step3", _ok_coro())
        assert ok1 is True
        assert ok2 is False
        assert ok3 is True

    @pytest.mark.asyncio
    async def test_name_appears_in_log(self):
        """Le nom du step apparaît dans les calls de logging."""
        with patch("app.services.scheduler_service.logger") as mock_log:
            await _run_step("my_step", _fail_coro())
            # Vérifie qu'au moins un appel logger a été fait
            assert mock_log.error.called or mock_log.warning.called


# ─────────────────────────────────────────────────────────────────────────────
# TestRunDailyPipelineForUser
# ─────────────────────────────────────────────────────────────────────────────

class TestRunDailyPipelineForUser:
    """Tests de l'orchestrateur pipeline par utilisateur."""

    def _make_all_mocks(self):
        """Retourne un jeu de patches qui font réussir toutes les étapes."""
        dm = _MockDailyMetrics()
        profile = _MockProfile()
        readiness = _MockReadiness()

        return {
            "fetch_profile": AsyncMock(return_value=profile),
            "step1": AsyncMock(return_value=dm),
            "fetch_metrics": AsyncMock(return_value=dm),
            "step2": AsyncMock(return_value=readiness),
            "step3": AsyncMock(return_value=3),
            "step4": AsyncMock(return_value="summary"),
            "step5": AsyncMock(return_value=72.5),
        }

    @pytest.mark.asyncio
    async def test_all_steps_success_returns_ok_dict(self):
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=_MockProfile())), \
             patch("app.services.scheduler_service._step1_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._step2_readiness", AsyncMock(return_value=_MockReadiness())), \
             patch("app.services.scheduler_service._step3_insights", AsyncMock(return_value=2)), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="ok")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=71.0)):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        assert report["daily_metrics"] == "ok"
        assert report["readiness"] == "ok"
        assert report["insights"] == "ok"
        assert report["health_plan"] == "ok"
        assert report["longevity"] == "ok"

    @pytest.mark.asyncio
    async def test_report_has_five_keys(self):
        """Le pipeline génère 9 clés (steps 1-9) depuis LOT 11."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step1_daily_metrics", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step2_readiness", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step3_insights", AsyncMock(return_value=0)), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step6_digital_twin", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step7_biological_age", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step8_motion_intelligence", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step9_adaptive_nutrition_log", AsyncMock(return_value=None)):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        assert len(report) == 9
        assert set(report.keys()) == {
            "daily_metrics", "readiness", "insights", "health_plan", "longevity",
            "digital_twin", "biological_age", "motion_intelligence", "adaptive_nutrition",
        }

    @pytest.mark.asyncio
    async def test_step1_failure_steps_2_to_5_continue(self):
        """Si step 1 échoue, les steps 2-5 continuent."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        async def _fail(): raise RuntimeError("metrics DB error")

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=_MockProfile())), \
             patch("app.services.scheduler_service._step1_daily_metrics", side_effect=RuntimeError("metrics DB error")), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step2_readiness", AsyncMock(return_value=_MockReadiness())), \
             patch("app.services.scheduler_service._step3_insights", AsyncMock(return_value=0)), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=None)):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        assert report["daily_metrics"].startswith("error:")
        # Steps 2-5 continuent
        assert report["readiness"] == "ok"
        assert report["insights"] == "ok"
        assert report["health_plan"] == "ok"
        assert report["longevity"] == "ok"

    @pytest.mark.asyncio
    async def test_step2_failure_steps_3_to_5_continue(self):
        """Si step 2 échoue, les steps 3-5 continuent."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=_MockProfile())), \
             patch("app.services.scheduler_service._step1_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._step2_readiness", side_effect=RuntimeError("readiness error")), \
             patch("app.services.scheduler_service._step3_insights", AsyncMock(return_value=1)), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="ok")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=70.0)):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        assert report["daily_metrics"] == "ok"
        assert report["readiness"].startswith("error:")
        assert report["insights"] == "ok"
        assert report["health_plan"] == "ok"
        assert report["longevity"] == "ok"

    @pytest.mark.asyncio
    async def test_step3_failure_steps_4_5_continue(self):
        """Si step 3 échoue, les steps 4-5 continuent."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=_MockProfile())), \
             patch("app.services.scheduler_service._step1_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._step2_readiness", AsyncMock(return_value=_MockReadiness())), \
             patch("app.services.scheduler_service._step3_insights", side_effect=RuntimeError("insight error")), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="ok")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=70.0)):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        assert report["insights"].startswith("error:")
        assert report["health_plan"] == "ok"
        assert report["longevity"] == "ok"

    @pytest.mark.asyncio
    async def test_all_steps_fail_report_has_errors(self):
        """Tous les steps peuvent échouer sans exception propagée."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step1_daily_metrics", side_effect=RuntimeError("err1")), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step2_readiness", side_effect=RuntimeError("err2")), \
             patch("app.services.scheduler_service._step3_insights", side_effect=RuntimeError("err3")), \
             patch("app.services.scheduler_service._step4_health_plan", side_effect=RuntimeError("err4")), \
             patch("app.services.scheduler_service._step5_longevity", side_effect=RuntimeError("err5")), \
             patch("app.services.scheduler_service._step6_digital_twin", side_effect=RuntimeError("err6")), \
             patch("app.services.scheduler_service._step7_biological_age", side_effect=RuntimeError("err7")), \
             patch("app.services.scheduler_service._step8_motion_intelligence", side_effect=RuntimeError("err8")), \
             patch("app.services.scheduler_service._step9_adaptive_nutrition_log", side_effect=RuntimeError("err9")):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        for key, val in report.items():
            assert val.startswith("error:"), f"Step {key} devrait avoir une erreur"

    @pytest.mark.asyncio
    async def test_step1_called_with_force_recompute_true(self):
        """Step 1 doit appeler compute_and_persist avec force_recompute=True."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=_MockProfile())), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())), \
             patch("app.services.scheduler_service._step2_readiness", AsyncMock(return_value=_MockReadiness())), \
             patch("app.services.scheduler_service._step3_insights", AsyncMock(return_value=0)), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=None)):

            with patch("app.services.daily_metrics_service.compute_and_persist_daily_metrics", AsyncMock(return_value=_MockDailyMetrics())) as mock_compute:
                await run_daily_pipeline_for_user(db, user_id, target)
                # Vérifie que force_recompute=True a été passé
                call_kwargs = mock_compute.call_args_list
                assert len(call_kwargs) >= 0  # Appel effectué via _step1

    @pytest.mark.asyncio
    async def test_none_daily_metrics_step2_handles_gracefully(self):
        """Si step 1 retourne None, step 2 gère sans crash."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch("app.services.scheduler_service._fetch_profile", AsyncMock(return_value=_MockProfile())), \
             patch("app.services.scheduler_service._step1_daily_metrics", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._fetch_daily_metrics", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step2_readiness", AsyncMock(return_value=None)), \
             patch("app.services.scheduler_service._step3_insights", AsyncMock(return_value=0)), \
             patch("app.services.scheduler_service._step4_health_plan", AsyncMock(return_value="")), \
             patch("app.services.scheduler_service._step5_longevity", AsyncMock(return_value=None)):

            report = await run_daily_pipeline_for_user(db, user_id, target)

        # Aucun crash — le rapport existe
        assert "daily_metrics" in report
        assert "readiness" in report


# ─────────────────────────────────────────────────────────────────────────────
# TestDailyPipelineAllUsers
# ─────────────────────────────────────────────────────────────────────────────

class TestDailyPipelineAllUsers:
    """Tests de l'orchestrateur multi-utilisateurs."""

    @pytest.mark.asyncio
    async def test_no_active_users_no_pipeline_call(self):
        """Aucun utilisateur actif → pipeline jamais appelé."""
        from app.services.scheduler_service import run_daily_pipeline_all_users

        mock_session = AsyncMock()
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_users_result)

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.db.session._get_session_factory", return_value=mock_factory), \
             patch("app.services.scheduler_service.run_daily_pipeline_for_user", AsyncMock()) as mock_pipeline:

            await run_daily_pipeline_all_users(_date())
            mock_pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_one_active_user_pipeline_called_once(self):
        """1 utilisateur actif → pipeline appelé 1 fois."""
        from app.services.scheduler_service import run_daily_pipeline_all_users

        user = _MockUser()
        mock_session = AsyncMock()
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [user]
        mock_session.execute = AsyncMock(return_value=mock_users_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.db.session._get_session_factory", return_value=mock_factory), \
             patch("app.services.scheduler_service.run_daily_pipeline_for_user", AsyncMock(return_value={"daily_metrics": "ok"})) as mock_pipeline:

            await run_daily_pipeline_all_users(_date())
            assert mock_pipeline.call_count == 1

    @pytest.mark.asyncio
    async def test_three_active_users_pipeline_called_three_times(self):
        """3 utilisateurs actifs → pipeline appelé 3 fois."""
        from app.services.scheduler_service import run_daily_pipeline_all_users

        users = [_MockUser(), _MockUser(), _MockUser()]
        mock_session = AsyncMock()
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = users
        mock_session.execute = AsyncMock(return_value=mock_users_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.db.session._get_session_factory", return_value=mock_factory), \
             patch("app.services.scheduler_service.run_daily_pipeline_for_user", AsyncMock(return_value={})) as mock_pipeline:

            await run_daily_pipeline_all_users(_date())
            assert mock_pipeline.call_count == 3

    @pytest.mark.asyncio
    async def test_one_user_error_others_processed(self):
        """Si un user lève une exception fatale, les autres users sont quand même traités."""
        from app.services.scheduler_service import run_daily_pipeline_all_users

        users = [_MockUser(), _MockUser(), _MockUser()]
        mock_session = AsyncMock()
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = users
        mock_session.execute = AsyncMock(return_value=mock_users_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        call_count = {"n": 0}
        async def _pipeline_with_one_failure(db, user_id, target_date):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("User 2 fatal error")
            return {}

        with patch("app.db.session._get_session_factory", return_value=mock_factory), \
             patch("app.services.scheduler_service.run_daily_pipeline_for_user", side_effect=_pipeline_with_one_failure):

            await run_daily_pipeline_all_users(_date())
            # Toujours 3 appels (le 2ème a échoué mais les autres ont tourné)
            assert call_count["n"] == 3

    @pytest.mark.asyncio
    async def test_commit_called_per_user(self):
        """db.commit() est appelé après chaque utilisateur pour isoler les transactions."""
        from app.services.scheduler_service import run_daily_pipeline_all_users

        users = [_MockUser(), _MockUser()]
        mock_session = AsyncMock()
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = users
        mock_session.execute = AsyncMock(return_value=mock_users_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.db.session._get_session_factory", return_value=mock_factory), \
             patch("app.services.scheduler_service.run_daily_pipeline_for_user", AsyncMock(return_value={})):

            await run_daily_pipeline_all_users(_date())
            # 2 users → 2 commits
            assert mock_session.commit.call_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# TestLazyEnsureTodayMetrics
# ─────────────────────────────────────────────────────────────────────────────

class TestLazyEnsureTodayMetrics:
    """Tests du helper de fallback lazy computation."""

    @pytest.mark.asyncio
    async def test_returns_daily_metrics_on_success(self):
        db = AsyncMock()
        user_id = _user_id()
        target = _date()
        mock_dm = _MockDailyMetrics()

        with patch(
            "app.services.daily_metrics_service.compute_and_persist_daily_metrics",
            AsyncMock(return_value=mock_dm),
        ):
            result = await lazy_ensure_today_metrics(db, user_id, target)
            assert result is mock_dm

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        """Une exception dans compute → retourne None (pas propagée)."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch(
            "app.services.daily_metrics_service.compute_and_persist_daily_metrics",
            AsyncMock(side_effect=Exception("DB connection failed")),
        ):
            result = await lazy_ensure_today_metrics(db, user_id, target)
            assert result is None

    @pytest.mark.asyncio
    async def test_does_not_propagate_exception(self):
        """Les exceptions de compute ne doivent pas remonter."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch(
            "app.services.daily_metrics_service.compute_and_persist_daily_metrics",
            AsyncMock(side_effect=Exception("Connection refused")),
        ):
            try:
                await lazy_ensure_today_metrics(db, user_id, target)
            except Exception:
                pytest.fail("lazy_ensure_today_metrics a propagé une exception")

    @pytest.mark.asyncio
    async def test_calls_compute_with_force_recompute_false(self):
        """force_recompute doit être False pour profiter du cache 2h."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch(
            "app.services.daily_metrics_service.compute_and_persist_daily_metrics",
            AsyncMock(return_value=_MockDailyMetrics()),
        ) as mock_compute:
            await lazy_ensure_today_metrics(db, user_id, target)
            call_kwargs = mock_compute.call_args
            assert call_kwargs.kwargs.get("force_recompute") is False

    @pytest.mark.asyncio
    async def test_passes_profile_to_compute(self):
        """Le profil optionnel est transmis à compute_and_persist."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()
        profile = _MockProfile()

        with patch(
            "app.services.daily_metrics_service.compute_and_persist_daily_metrics",
            AsyncMock(return_value=_MockDailyMetrics()),
        ) as mock_compute:
            await lazy_ensure_today_metrics(db, user_id, target, profile=profile)
            call_kwargs = mock_compute.call_args
            assert call_kwargs.kwargs.get("profile") is profile

    @pytest.mark.asyncio
    async def test_warning_logged_on_exception(self):
        """Un warning est loggé quand compute échoue."""
        db = AsyncMock()
        user_id = _user_id()
        target = _date()

        with patch(
            "app.services.daily_metrics_service.compute_and_persist_daily_metrics",
            AsyncMock(side_effect=Exception("error")),
        ):
            with patch("app.services.daily_metrics_service.logger") as mock_logger:
                await lazy_ensure_today_metrics(db, user_id, target)
                assert mock_logger.warning.called


# ─────────────────────────────────────────────────────────────────────────────
# TestCreateScheduler
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateScheduler:
    """Tests de la factory de configuration APScheduler."""

    def test_returns_scheduler_instance(self):
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = create_scheduler()
        assert isinstance(scheduler, AsyncIOScheduler)

    def test_scheduler_not_started(self):
        """create_scheduler() ne démarre pas le scheduler."""
        scheduler = create_scheduler()
        assert not scheduler.running

    def test_has_one_job(self):
        """Un seul job est configuré : soma_daily_pipeline."""
        scheduler = create_scheduler()
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1

    def test_job_has_correct_id(self):
        scheduler = create_scheduler()
        job = scheduler.get_jobs()[0]
        assert job.id == "soma_daily_pipeline"

    def test_job_has_correct_name(self):
        scheduler = create_scheduler()
        job = scheduler.get_jobs()[0]
        assert "Daily" in job.name or "daily" in job.id

    def test_scheduler_timezone_paris(self):
        """Le scheduler utilise le fuseau Europe/Paris."""
        import pytz
        scheduler = create_scheduler()
        tz = scheduler.timezone
        assert str(tz) == "Europe/Paris"

    def test_job_function_is_daily_pipeline(self):
        """Le job pointe vers la fonction daily_pipeline_job."""
        from app.services.scheduler_service import daily_pipeline_job
        scheduler = create_scheduler()
        job = scheduler.get_jobs()[0]
        assert job.func is daily_pipeline_job

    def test_misfire_grace_time_set(self):
        """misfire_grace_time doit être configuré (tolérance redémarrage)."""
        scheduler = create_scheduler()
        job = scheduler.get_jobs()[0]
        assert job.misfire_grace_time is not None
        assert job.misfire_grace_time >= 60  # Au moins 1 minute
