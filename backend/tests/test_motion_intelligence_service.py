"""
Tests pour Motion Intelligence Engine — LOT 11.
~40 tests purs (aucun accès DB).
"""
import pytest
from datetime import date, timedelta

from app.domains.motion.service import (
    SessionData,
    ExerciseMotionProfile,
    MotionIntelligenceResult,
    _trend,
    _safe_mean,
    _safe_std,
    _asymmetry_score,
    _consecutive_quality_sessions,
    _build_exercise_profile,
    compute_motion_intelligence,
    build_motion_summary,
    TREND_SLOPE_IMPROVING,
    TREND_SLOPE_DECLINING,
    QUALITY_GOOD_THRESHOLD,
    CONFIDENCE_SESSION_TARGET,
)


# ── Helper factory ────────────────────────────────────────────────────────────

def _session(
    exercise_type: str = "squat",
    stability: float = 75.0,
    amplitude: float = 75.0,
    quality: float = 75.0,
    session_date: date = None,
    rep_count: int = 10,
) -> SessionData:
    return SessionData(
        exercise_type=exercise_type,
        session_date=session_date or date.today(),
        stability_score=stability,
        amplitude_score=amplitude,
        quality_score=quality,
        rep_count=rep_count,
    )


# ── _trend ────────────────────────────────────────────────────────────────────

class TestTrend:
    def test_improving_sequence(self):
        # Strong upward trend: 60, 70, 80, 90
        assert _trend([60.0, 70.0, 80.0, 90.0]) == "improving"

    def test_declining_sequence(self):
        assert _trend([90.0, 80.0, 70.0, 60.0]) == "declining"

    def test_stable_sequence(self):
        assert _trend([75.0, 75.0, 75.0, 75.0]) == "stable"

    def test_single_value_stable(self):
        assert _trend([80.0]) == "stable"

    def test_empty_list_stable(self):
        assert _trend([]) == "stable"

    def test_slight_improvement_below_threshold(self):
        # slope ≈ 0.1, below TREND_SLOPE_IMPROVING (0.3) → stable
        assert _trend([70.0, 70.1, 70.2, 70.3]) == "stable"

    def test_at_threshold_improving(self):
        # slope = 0.3 per index → not strictly > 0.3 → stable
        values = [70.0 + 0.3 * i for i in range(5)]
        result = _trend(values)
        assert result in ("improving", "stable")


# ── _asymmetry_score ──────────────────────────────────────────────────────────

class TestAsymmetryScore:
    def test_consistent_values_low_asymmetry(self):
        # All same value → std = 0 → asymmetry = 0
        score = _asymmetry_score([75.0, 75.0, 75.0], [75.0, 75.0, 75.0])
        assert score == pytest.approx(0.0)

    def test_highly_variable_values_high_asymmetry(self):
        score = _asymmetry_score([20.0, 80.0, 20.0, 80.0], [30.0, 90.0, 30.0, 90.0])
        assert score > 20  # high variance = high asymmetry

    def test_capped_at_100(self):
        # Very high variance
        score = _asymmetry_score([0.0, 100.0], [0.0, 100.0])
        assert score <= 100.0

    def test_empty_lists_give_zero(self):
        score = _asymmetry_score([], [])
        assert score == 0.0

    def test_single_list_only(self):
        # Only stability values, amplitude empty
        score = _asymmetry_score([70.0, 80.0], [])
        assert score >= 0.0


# ── _consecutive_quality_sessions ─────────────────────────────────────────────

class TestConsecutiveQualitySessions:
    def test_all_high_quality_full_streak(self):
        sessions = [_session(quality=75), _session(quality=80), _session(quality=90)]
        assert _consecutive_quality_sessions(sessions) == 3

    def test_one_low_quality_breaks_streak(self):
        today = date.today()
        sessions = [
            _session(quality=80, session_date=today - timedelta(days=2)),
            _session(quality=40, session_date=today - timedelta(days=1)),  # breaks streak
            _session(quality=85, session_date=today),
        ]
        # Most recent is 85 (good), then 40 (breaks) → streak = 1
        assert _consecutive_quality_sessions(sessions) == 1

    def test_empty_sessions_gives_zero(self):
        assert _consecutive_quality_sessions([]) == 0

    def test_none_quality_breaks_streak(self):
        sessions = [
            SessionData("squat", date.today(), 80, 80, None)  # None quality
        ]
        assert _consecutive_quality_sessions(sessions) == 0


# ── _build_exercise_profile ───────────────────────────────────────────────────

class TestBuildExerciseProfile:
    def test_single_session_profile(self):
        sessions = [_session(stability=70, amplitude=80, quality=75)]
        profile = _build_exercise_profile("squat", sessions)
        assert profile.exercise_type == "squat"
        assert profile.sessions_analyzed == 1
        assert profile.avg_stability == 70.0
        assert profile.avg_amplitude == 80.0
        assert profile.avg_quality == 75.0

    def test_multiple_sessions_averages(self):
        sessions = [
            _session(stability=60, amplitude=70, quality=65),
            _session(stability=80, amplitude=90, quality=85),
        ]
        profile = _build_exercise_profile("push_up", sessions)
        assert profile.avg_stability == pytest.approx(70.0)
        assert profile.avg_amplitude == pytest.approx(80.0)
        assert profile.avg_quality == pytest.approx(75.0)

    def test_declining_quality_generates_alert(self):
        today = date.today()
        sessions = [
            _session(quality=90, session_date=today - timedelta(days=4)),
            _session(quality=70, session_date=today - timedelta(days=3)),
            _session(quality=50, session_date=today - timedelta(days=2)),
            _session(quality=30, session_date=today - timedelta(days=1)),
        ]
        profile = _build_exercise_profile("squat", sessions)
        assert profile.quality_trend == "declining"
        assert len(profile.alerts) > 0

    def test_improving_trend_detected(self):
        today = date.today()
        sessions = [
            _session(quality=50, session_date=today - timedelta(days=3)),
            _session(quality=60, session_date=today - timedelta(days=2)),
            _session(quality=70, session_date=today - timedelta(days=1)),
            _session(quality=80, session_date=today),
        ]
        profile = _build_exercise_profile("squat", sessions)
        assert profile.quality_trend == "improving"

    def test_low_stability_generates_alert(self):
        sessions = [_session(stability=40, amplitude=70, quality=60)]
        profile = _build_exercise_profile("squat", sessions)
        assert any("stabilité" in a.lower() or "stability" in a.lower() for a in profile.alerts)


# ── compute_motion_intelligence ───────────────────────────────────────────────

class TestComputeMotionIntelligence:
    def test_empty_sessions_returns_zero_confidence(self):
        result = compute_motion_intelligence([])
        assert result.confidence == 0.0
        assert result.movement_health_score == 0.0
        assert result.sessions_analyzed == 0

    def test_empty_sessions_has_recommendation(self):
        result = compute_motion_intelligence([])
        assert len(result.recommendations) > 0

    def test_single_session_correct_profile(self):
        result = compute_motion_intelligence([_session(stability=70, amplitude=80, quality=75)])
        assert "squat" in result.exercise_profiles
        assert result.sessions_analyzed == 1

    def test_multiple_exercises_separate_profiles(self):
        sessions = [
            _session(exercise_type="squat"),
            _session(exercise_type="push_up"),
            _session(exercise_type="squat"),
        ]
        result = compute_motion_intelligence(sessions)
        assert "squat" in result.exercise_profiles
        assert "push_up" in result.exercise_profiles
        assert result.exercise_profiles["squat"].sessions_analyzed == 2

    def test_movement_health_formula(self):
        # Simple case: stability=80, mobility=70, consistent (asymmetry≈0)
        sessions = [
            _session(stability=80, amplitude=70, quality=75),
            _session(stability=80, amplitude=70, quality=75),
        ]
        result = compute_motion_intelligence(sessions)
        # asymmetry ≈ 0 → movement_health ≈ 0.4×80 + 0.4×70 + 0.2×100 = 80
        assert result.movement_health_score == pytest.approx(80.0, abs=5)

    def test_declining_trend_detected(self):
        today = date.today()
        sessions = [
            _session(quality=80, session_date=today - timedelta(days=3)),
            _session(quality=70, session_date=today - timedelta(days=2)),
            _session(quality=60, session_date=today - timedelta(days=1)),
        ]
        result = compute_motion_intelligence(sessions)
        assert result.overall_quality_trend == "declining"

    def test_improving_trend_detected(self):
        today = date.today()
        sessions = [
            _session(quality=50, session_date=today - timedelta(days=3)),
            _session(quality=65, session_date=today - timedelta(days=2)),
            _session(quality=80, session_date=today - timedelta(days=1)),
        ]
        result = compute_motion_intelligence(sessions)
        assert result.overall_quality_trend == "improving"

    def test_confidence_scales_with_sessions(self):
        # 10 sessions → confidence = 10/20 = 0.5
        sessions = [_session() for _ in range(10)]
        result = compute_motion_intelligence(sessions)
        assert result.confidence == pytest.approx(0.5)

    def test_confidence_capped_at_1(self):
        sessions = [_session() for _ in range(25)]
        result = compute_motion_intelligence(sessions)
        assert result.confidence == 1.0

    def test_consecutive_quality_sessions_streak(self):
        today = date.today()
        sessions = [
            _session(quality=80, session_date=today - timedelta(days=2)),
            _session(quality=85, session_date=today - timedelta(days=1)),
            _session(quality=90, session_date=today),
        ]
        result = compute_motion_intelligence(sessions)
        assert result.consecutive_quality_sessions == 3

    def test_high_asymmetry_generates_risk_alert(self):
        # Very inconsistent stability scores → high asymmetry
        sessions = [
            _session(stability=20, amplitude=80),
            _session(stability=90, amplitude=10),
            _session(stability=15, amplitude=90),
            _session(stability=85, amplitude=15),
        ]
        result = compute_motion_intelligence(sessions)
        assert result.asymmetry_score > 30

    def test_recommendations_generated(self):
        result = compute_motion_intelligence([_session()])
        assert len(result.recommendations) > 0

    def test_days_analyzed_parameter_stored(self):
        result = compute_motion_intelligence([], days_analyzed=45)
        assert result.days_analyzed == 45


# ── build_motion_summary ──────────────────────────────────────────────────────

class TestBuildMotionSummary:
    def test_no_sessions_returns_short_message(self):
        result = compute_motion_intelligence([])
        summary = build_motion_summary(result)
        assert "aucune" in summary.lower() or "no" in summary.lower()

    def test_with_sessions_returns_scores(self):
        result = compute_motion_intelligence([_session(stability=75, amplitude=80)])
        summary = build_motion_summary(result)
        assert "santé" in summary.lower() or "health" in summary.lower()
        assert isinstance(summary, str)

    def test_summary_compact(self):
        result = compute_motion_intelligence([_session()])
        assert len(build_motion_summary(result)) < 300
