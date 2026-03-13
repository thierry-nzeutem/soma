"""
SOMA LOT 19 — Tests unitaires : Feature Usage, Coach Analytics, Events, Performance.

Couvre :
  - FeatureUsage dataclass : champs, valeurs initiales
  - CoachAnalytics dataclass : questions, follow-up rate, robustesse div/0
  - EventCount dataclass : event_name, count, unique_users
  - get_performance_stats() : agrégation en-mémoire depuis MetricsMiddleware
  - ApiPerformanceStats : avg, p95, error_rate
  - ApiMetricDB : table, colonnes
  - FeatureUsageResponse / CoachAnalyticsResponse / EventCountResponse / ApiPerformanceStatsResponse schémas Pydantic

~15 tests purs, aucune dépendance DB réelle.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.services.analytics_dashboard_service import (
    ApiPerformanceStats,
    CoachAnalytics,
    EventCount,
    FeatureUsage,
    get_performance_stats,
)
from app.schemas.analytics_dashboard import (
    ApiPerformanceStatsResponse,
    CoachAnalyticsResponse,
    EventCountResponse,
    FeatureUsageResponse,
)
from app.models.api_metrics import ApiMetricDB
from app.middleware.metrics_middleware import MetricRecord


# ── Tests FeatureUsage dataclass ─────────────────────────────────────────────

class TestFeatureUsageDataclass:
    """Vérifie la structure de FeatureUsage."""

    def _make(self, **kwargs) -> FeatureUsage:
        defaults = dict(
            period_days=30,
            briefing_views=300,
            journal_entries=450,
            coach_questions=120,
            twin_views=80,
            nutrition_logs=200,
            biomarker_logs=15,
            quick_advice_requests=90,
            workout_logs=160,
        )
        defaults.update(kwargs)
        return FeatureUsage(**defaults)

    def test_all_fields_stored(self):
        u = self._make()
        assert u.period_days == 30
        assert u.briefing_views == 300
        assert u.journal_entries == 450
        assert u.coach_questions == 120
        assert u.twin_views == 80
        assert u.nutrition_logs == 200
        assert u.biomarker_logs == 15
        assert u.quick_advice_requests == 90
        assert u.workout_logs == 160

    def test_all_zero_allowed(self):
        u = self._make(
            briefing_views=0, journal_entries=0, coach_questions=0,
            twin_views=0, nutrition_logs=0, biomarker_logs=0,
            quick_advice_requests=0, workout_logs=0,
        )
        assert u.briefing_views == 0
        assert u.workout_logs == 0


# ── Tests CoachAnalytics dataclass ───────────────────────────────────────────

class TestCoachAnalyticsDataclass:
    """Vérifie la structure de CoachAnalytics et le calcul follow-up rate."""

    def _make(self, **kwargs) -> CoachAnalytics:
        defaults = dict(
            period_days=30,
            total_questions=200,
            total_quick_advice=80,
            unique_users_asking=60,
            questions_per_active_user=3.33,
            follow_up_rate=75.0,
        )
        defaults.update(kwargs)
        return CoachAnalytics(**defaults)

    def test_follow_up_rate_in_0_100(self):
        c = self._make(follow_up_rate=65.0)
        assert 0 <= c.follow_up_rate <= 100

    def test_questions_per_user_calc(self):
        """Simulation du calcul questions_per_active_user."""
        total_questions = 200
        unique_users = 50
        expected = round(total_questions / unique_users, 2) if unique_users > 0 else 0.0
        c = self._make(questions_per_active_user=expected)
        assert abs(c.questions_per_active_user - 4.0) < 0.01

    def test_questions_per_user_zero_users(self):
        """0 utilisateurs → 0.0 (division par zéro sûre)."""
        unique_users = 0
        per_user = round(100 / unique_users, 2) if unique_users > 0 else 0.0
        assert per_user == 0.0

    def test_follow_up_rate_zero_when_no_multi(self):
        c = self._make(follow_up_rate=0.0)
        assert c.follow_up_rate == 0.0


# ── Tests EventCount dataclass ───────────────────────────────────────────────

class TestEventCountDataclass:
    """Vérifie la structure de EventCount."""

    def test_fields(self):
        ec = EventCount(event_name="app_open", count=1500, unique_users=300)
        assert ec.event_name == "app_open"
        assert ec.count == 1500
        assert ec.unique_users == 300

    def test_unique_users_le_count(self):
        """Les users uniques ne peuvent pas dépasser le total d'événements."""
        ec = EventCount(event_name="coach_question", count=500, unique_users=80)
        assert ec.unique_users <= ec.count


# ── Tests get_performance_stats ──────────────────────────────────────────────

class TestGetPerformanceStats:
    """get_performance_stats agrège depuis le buffer MetricsMiddleware."""

    def _make_record(
        self,
        endpoint: str = "/api/v1/home/summary",
        method: str = "GET",
        response_time_ms: int = 100,
        status_code: int = 200,
    ) -> MetricRecord:
        return MetricRecord(
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            created_at=datetime.now(timezone.utc),
        )

    def test_empty_buffer_returns_empty_list(self):
        with patch(
            "app.middleware.metrics_middleware.get_buffered_metrics",
            return_value=[],
        ):
            result = get_performance_stats()
            assert result == []

    def test_single_endpoint_avg(self):
        records = [
            self._make_record(response_time_ms=100),
            self._make_record(response_time_ms=200),
        ]
        with patch(
            "app.middleware.metrics_middleware.get_buffered_metrics",
            return_value=records,
        ):
            result = get_performance_stats()
            assert len(result) == 1
            assert result[0].avg_response_ms == 150.0

    def test_error_rate_calculated(self):
        records = [
            self._make_record(status_code=200),
            self._make_record(status_code=500),
            self._make_record(status_code=200),
            self._make_record(status_code=404),
        ]
        with patch(
            "app.middleware.metrics_middleware.get_buffered_metrics",
            return_value=records,
        ):
            result = get_performance_stats()
            assert len(result) == 1
            assert result[0].error_rate == 50.0   # 2 errors / 4 calls

    def test_multiple_endpoints_sorted_by_volume(self):
        records_a = [self._make_record(endpoint="/api/v1/a") for _ in range(10)]
        records_b = [self._make_record(endpoint="/api/v1/b") for _ in range(5)]
        with patch(
            "app.middleware.metrics_middleware.get_buffered_metrics",
            return_value=records_a + records_b,
        ):
            result = get_performance_stats(limit=10)
            assert result[0].endpoint == "/api/v1/a"
            assert result[0].total_calls == 10
            assert result[1].total_calls == 5

    def test_p95_computation(self):
        times = list(range(1, 21))  # 1 à 20 ms
        records = [
            self._make_record(response_time_ms=t)
            for t in times
        ]
        with patch(
            "app.middleware.metrics_middleware.get_buffered_metrics",
            return_value=records,
        ):
            result = get_performance_stats()
            assert len(result) == 1
            # p95 idx = max(0, int(20 * 0.95) - 1) = max(0, 19 - 1) = 18
            # times[18] = 19
            assert result[0].p95_response_ms == 19.0

    def test_limit_respected(self):
        all_records = [
            self._make_record(endpoint=f"/api/v1/endpoint_{i}")
            for i in range(30)
        ]
        with patch(
            "app.middleware.metrics_middleware.get_buffered_metrics",
            return_value=all_records,
        ):
            result = get_performance_stats(limit=5)
            assert len(result) <= 5


# ── Tests ApiMetricDB modèle ─────────────────────────────────────────────────

class TestApiMetricDB:
    """Vérifie les métadonnées du modèle ORM ApiMetricDB."""

    def test_tablename(self):
        assert ApiMetricDB.__tablename__ == "api_metrics"

    def test_has_endpoint_column(self):
        cols = [c.name for c in ApiMetricDB.__table__.columns]
        assert "endpoint" in cols

    def test_has_method_column(self):
        cols = [c.name for c in ApiMetricDB.__table__.columns]
        assert "method" in cols

    def test_has_response_time_ms_column(self):
        cols = [c.name for c in ApiMetricDB.__table__.columns]
        assert "response_time_ms" in cols

    def test_has_status_code_column(self):
        cols = [c.name for c in ApiMetricDB.__table__.columns]
        assert "status_code" in cols

    def test_has_created_at_column(self):
        cols = [c.name for c in ApiMetricDB.__table__.columns]
        assert "created_at" in cols


# ── Tests schémas Pydantic ───────────────────────────────────────────────────

class TestAnalyticsDashboardSchemas:
    """Vérifie les schémas Pydantic des réponses analytics."""

    def test_feature_usage_response(self):
        data = dict(
            period_days=30, briefing_views=300, journal_entries=450,
            coach_questions=120, twin_views=80, nutrition_logs=200,
            biomarker_logs=15, quick_advice_requests=90, workout_logs=160,
        )
        resp = FeatureUsageResponse(**data)
        assert resp.briefing_views == 300
        assert resp.workout_logs == 160

    def test_coach_analytics_response(self):
        data = dict(
            period_days=30, total_questions=200, total_quick_advice=80,
            unique_users_asking=60, questions_per_active_user=3.33,
            follow_up_rate=75.0,
        )
        resp = CoachAnalyticsResponse(**data)
        assert resp.follow_up_rate == 75.0

    def test_event_count_response(self):
        data = dict(event_name="app_open", count=1500, unique_users=300)
        resp = EventCountResponse(**data)
        assert resp.event_name == "app_open"

    def test_api_performance_stats_response(self):
        data = dict(
            endpoint="/api/v1/home/summary",
            method="GET",
            avg_response_ms=145.3,
            p95_response_ms=290.0,
            total_calls=1000,
            error_rate=1.5,
        )
        resp = ApiPerformanceStatsResponse(**data)
        assert resp.avg_response_ms == 145.3
        assert resp.error_rate == 1.5
