"""Tests pour le service d'analyse du sommeil (architecture, consistance, problemes)."""

import pytest
from datetime import datetime, timedelta, timezone

from app.services.sleep_analysis_service import (
    compute_sleep_architecture_score,
    compute_sleep_consistency_score,
    detect_sleep_problems,
)


# ── Architecture scoring tests ──────────────────────────────────────────────

class TestSleepArchitectureScore:
    """Tests pour compute_sleep_architecture_score()."""

    def test_ideal_distribution_scores_high(self):
        """Distribution ideale : deep 20%, REM 22%, light 53%, awake 5%."""
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=96,   # 20%
            rem_sleep_minutes=106,   # 22%
            light_sleep_minutes=254, # 53%
            awake_minutes=24,        # 5%
        )
        assert result.architecture_score >= 80
        assert result.architecture_quality == "excellent"

    def test_no_deep_sleep_penalized(self):
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=0,
            rem_sleep_minutes=120,
            light_sleep_minutes=360,
            awake_minutes=0,
        )
        assert result.architecture_score < 70
        assert "insufficient_deep_sleep" in result.areas_to_improve

    def test_no_rem_sleep_penalized(self):
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=96,
            rem_sleep_minutes=0,
            light_sleep_minutes=384,
            awake_minutes=0,
        )
        assert result.architecture_score < 70
        assert "insufficient_rem_sleep" in result.areas_to_improve

    def test_excessive_awake_time_penalized(self):
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=72,
            rem_sleep_minutes=96,
            light_sleep_minutes=216,
            awake_minutes=96,  # 20% — very high
        )
        assert "excessive_wake_time" in result.areas_to_improve

    def test_no_stages_with_good_duration(self):
        """Sans phases disponibles, score estime sur la duree."""
        result = compute_sleep_architecture_score(
            duration_minutes=480,
        )
        assert result.architecture_score == 75
        assert result.architecture_quality == "estimated_good"
        assert "sleep_stages_unknown" in result.areas_to_improve

    def test_no_stages_with_short_duration(self):
        result = compute_sleep_architecture_score(
            duration_minutes=300,  # 5h
        )
        assert result.architecture_score == 30
        assert result.architecture_quality == "estimated_poor"

    def test_no_stages_with_fair_duration(self):
        result = compute_sleep_architecture_score(
            duration_minutes=420,  # 7h
        )
        assert result.architecture_score == 60
        assert result.architecture_quality == "estimated_fair"

    def test_zero_duration_returns_empty(self):
        result = compute_sleep_architecture_score(duration_minutes=0)
        assert result.architecture_score == 0
        assert result.architecture_quality == "unknown"

    def test_none_duration_returns_empty(self):
        result = compute_sleep_architecture_score()
        assert result.architecture_score == 0

    def test_percentages_sum_to_100(self):
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=96,
            rem_sleep_minutes=96,
            light_sleep_minutes=264,
            awake_minutes=24,
        )
        total_pct = result.deep_pct + result.rem_pct + result.light_pct + result.awake_pct
        assert abs(total_pct - 100.0) < 0.5

    def test_score_clamped_to_0_100(self):
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=480,  # 100% deep — impossible
            rem_sleep_minutes=0,
            light_sleep_minutes=0,
            awake_minutes=0,
        )
        assert 0 <= result.architecture_score <= 100

    def test_short_duration_flagged(self):
        result = compute_sleep_architecture_score(
            duration_minutes=300,
            deep_sleep_minutes=60,
            rem_sleep_minutes=60,
            light_sleep_minutes=180,
            awake_minutes=0,
        )
        assert "insufficient_duration" in result.areas_to_improve

    def test_good_quality_label(self):
        result = compute_sleep_architecture_score(
            duration_minutes=480,
            deep_sleep_minutes=96,
            rem_sleep_minutes=96,
            light_sleep_minutes=264,
            awake_minutes=24,
        )
        assert result.architecture_quality in ("excellent", "good")

    def test_poor_quality_label(self):
        result = compute_sleep_architecture_score(
            duration_minutes=240,
            deep_sleep_minutes=10,
            rem_sleep_minutes=10,
            light_sleep_minutes=200,
            awake_minutes=20,
        )
        assert result.architecture_quality in ("poor", "fair")


# ── Consistency scoring tests ───────────────────────────────────────────────

class TestSleepConsistencyScore:
    """Tests pour compute_sleep_consistency_score()."""

    def _make_sessions(self, bedtime_hours: list, wake_hours: list) -> list:
        """Helper pour creer des sessions avec des heures specifiques."""
        sessions = []
        base_date = datetime(2026, 3, 1, tzinfo=timezone.utc)
        for i, (bh, wh) in enumerate(zip(bedtime_hours, wake_hours)):
            bed_h = int(bh)
            bed_m = int((bh - bed_h) * 60)
            wake_h = int(wh)
            wake_m = int((wh - wake_h) * 60)
            start = base_date + timedelta(days=i, hours=bed_h, minutes=bed_m)
            end = base_date + timedelta(days=i + 1, hours=wake_h, minutes=wake_m)
            sessions.append({"start_at": start, "end_at": end})
        return sessions

    def test_uniform_times_scores_high(self):
        """Horaires identiques chaque nuit = score excellent."""
        sessions = self._make_sessions(
            bedtime_hours=[23.0] * 7,
            wake_hours=[7.0] * 7,
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.consistency_score >= 85
        assert result.consistency_label == "excellent"

    def test_variable_times_scores_low(self):
        """Horaires tres variables = score faible."""
        sessions = self._make_sessions(
            bedtime_hours=[21.0, 1.0, 22.0, 3.0, 23.0, 0.5, 20.0],
            wake_hours=[5.0, 9.0, 6.0, 11.0, 7.0, 8.5, 4.0],
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.consistency_score < 60

    def test_insufficient_sessions(self):
        """Moins de 3 sessions = insufficient_data."""
        result = compute_sleep_consistency_score([
            {"start_at": datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc),
             "end_at": datetime(2026, 3, 2, 7, 0, tzinfo=timezone.utc)},
        ])
        assert result.consistency_label == "insufficient_data"

    def test_empty_list(self):
        result = compute_sleep_consistency_score([])
        assert result.consistency_label == "insufficient_data"
        assert result.sessions_analyzed == 0

    def test_three_sessions_minimum(self):
        sessions = self._make_sessions(
            bedtime_hours=[23.0, 23.5, 22.5],
            wake_hours=[7.0, 7.5, 6.5],
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.consistency_label != "insufficient_data"
        assert result.sessions_analyzed == 3

    def test_avg_times_calculated(self):
        sessions = self._make_sessions(
            bedtime_hours=[23.0, 23.0, 23.0],
            wake_hours=[7.0, 7.0, 7.0],
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.avg_bedtime_hour is not None
        assert result.avg_wake_hour is not None
        assert abs(result.avg_wake_hour - 7.0) < 0.1

    def test_variance_zero_for_identical(self):
        sessions = self._make_sessions(
            bedtime_hours=[23.0, 23.0, 23.0, 23.0, 23.0],
            wake_hours=[7.0, 7.0, 7.0, 7.0, 7.0],
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.bedtime_variance_min == 0.0
        assert result.wake_variance_min == 0.0

    def test_iso_string_parsing(self):
        """Sessions avec start_at/end_at en string ISO."""
        sessions = [
            {"start_at": "2026-03-01T23:00:00+00:00", "end_at": "2026-03-02T07:00:00+00:00"},
            {"start_at": "2026-03-02T23:30:00+00:00", "end_at": "2026-03-03T07:30:00+00:00"},
            {"start_at": "2026-03-03T22:30:00+00:00", "end_at": "2026-03-04T06:30:00+00:00"},
        ]
        result = compute_sleep_consistency_score(sessions)
        assert result.consistency_label != "insufficient_data"

    def test_moderate_variance(self):
        sessions = self._make_sessions(
            bedtime_hours=[22.0, 23.0, 0.0, 23.5, 22.5],
            wake_hours=[6.0, 7.0, 8.0, 7.5, 6.5],
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.consistency_label in ("good", "moderate")

    def test_sessions_analyzed_count(self):
        sessions = self._make_sessions(
            bedtime_hours=[23.0] * 10,
            wake_hours=[7.0] * 10,
        )
        result = compute_sleep_consistency_score(sessions)
        assert result.sessions_analyzed == 10


# ── Problem detection tests ─────────────────────────────────────────────────

class TestSleepProblemDetection:
    """Tests pour detect_sleep_problems()."""

    def _make_sessions(self, count: int, **overrides) -> list:
        """Creer count sessions avec des valeurs par defaut."""
        base = datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc)
        sessions = []
        for i in range(count):
            s = {
                "start_at": base + timedelta(days=i),
                "end_at": base + timedelta(days=i, hours=8),
                "duration_minutes": overrides.get("duration_minutes", 480),
                "perceived_quality": overrides.get("perceived_quality", 4),
                "deep_sleep_minutes": overrides.get("deep_sleep_minutes", None),
                "awake_minutes": overrides.get("awake_minutes", None),
            }
            sessions.append(s)
        return sessions

    def test_no_problems_with_healthy_sleep(self):
        sessions = self._make_sessions(10, duration_minutes=480, perceived_quality=4)
        problems = detect_sleep_problems(sessions)
        assert len(problems) == 0

    def test_chronic_insufficient_high(self):
        sessions = self._make_sessions(10, duration_minutes=300)  # 5h
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "chronic_insufficient" in types
        chronic = next(p for p in problems if p.problem_type == "chronic_insufficient")
        assert chronic.severity == "high"

    def test_chronic_insufficient_moderate(self):
        # 4 nuits courtes, 6 normales
        sessions = self._make_sessions(6, duration_minutes=480)
        sessions += self._make_sessions(4, duration_minutes=300)
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "chronic_insufficient" in types
        chronic = next(p for p in problems if p.problem_type == "chronic_insufficient")
        assert chronic.severity == "moderate"

    def test_quality_degradation(self):
        """Qualite recente inferieure a qualite ancienne."""
        sessions = []
        base = datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc)
        for i in range(10):
            quality = 5 if i >= 5 else 3  # older=5, recent=3
            sessions.append({
                "start_at": base + timedelta(days=i),
                "end_at": base + timedelta(days=i, hours=8),
                "duration_minutes": 480,
                "perceived_quality": quality,
            })
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "quality_degradation" in types

    def test_no_quality_degradation_with_stable(self):
        sessions = self._make_sessions(10, perceived_quality=4)
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "quality_degradation" not in types

    def test_late_bedtime_detected(self):
        """Coucher moyen apres 00:30."""
        base = datetime(2026, 3, 1, 1, 0, tzinfo=timezone.utc)  # 01:00
        sessions = []
        for i in range(7):
            sessions.append({
                "start_at": base + timedelta(days=i),
                "end_at": base + timedelta(days=i, hours=7),
                "duration_minutes": 420,
                "perceived_quality": 4,
            })
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "late_bedtime" in types

    def test_no_late_bedtime_with_normal_hours(self):
        sessions = self._make_sessions(7)  # 23:00 default
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "late_bedtime" not in types

    def test_fragmented_sleep_detected(self):
        sessions = self._make_sessions(7, awake_minutes=50)
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "fragmented_sleep" in types

    def test_no_fragmented_with_low_awake(self):
        sessions = self._make_sessions(7, awake_minutes=10)
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "fragmented_sleep" not in types

    def test_insufficient_deep_sleep(self):
        sessions = self._make_sessions(7, deep_sleep_minutes=20, duration_minutes=480)
        # 20/480 = 4.2% — well below 10%
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "insufficient_deep_sleep" in types

    def test_sufficient_deep_sleep_no_problem(self):
        sessions = self._make_sessions(7, deep_sleep_minutes=96, duration_minutes=480)
        # 96/480 = 20% — ideal
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "insufficient_deep_sleep" not in types

    def test_too_few_sessions_returns_empty(self):
        sessions = self._make_sessions(3)
        problems = detect_sleep_problems(sessions)
        assert len(problems) == 0

    def test_empty_sessions_returns_empty(self):
        problems = detect_sleep_problems([])
        assert len(problems) == 0

    def test_problem_has_recommendation(self):
        sessions = self._make_sessions(10, duration_minutes=300)
        problems = detect_sleep_problems(sessions)
        for p in problems:
            assert p.recommendation
            assert len(p.recommendation) > 10

    def test_problem_has_evidence_days(self):
        sessions = self._make_sessions(10, duration_minutes=300)
        problems = detect_sleep_problems(sessions)
        for p in problems:
            assert p.evidence_days > 0

    def test_multiple_problems_detected(self):
        """Sessions avec coucher tardif + duree insuffisante."""
        base = datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc)  # 02:00
        sessions = []
        for i in range(10):
            sessions.append({
                "start_at": base + timedelta(days=i),
                "end_at": base + timedelta(days=i, hours=4),  # 4h sleep
                "duration_minutes": 240,
                "perceived_quality": 2,
            })
        problems = detect_sleep_problems(sessions)
        types = [p.problem_type for p in problems]
        assert "chronic_insufficient" in types
        assert "late_bedtime" in types
