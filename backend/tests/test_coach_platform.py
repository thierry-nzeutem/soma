"""
Tests SOMA LOT 14 — Coach Platform.
~20 tests purs.
"""
import pytest
from datetime import date, datetime

from app.domains.coach_platform.service import (
    compute_athlete_dashboard_summary,
    _determine_risk_level,
    _generate_athlete_alerts,
    build_coach_athlete_context,
    AthleteDashboardSummary,
)


# ── Tests: _determine_risk_level ───────────────────────────────────────────────

class TestDetermineRiskLevel:
    def test_all_good_metrics_green(self):
        level = _determine_risk_level(readiness=80, fatigue=30, injury_risk=10)
        assert level == "green"

    def test_low_readiness_triggers_yellow(self):
        level = _determine_risk_level(readiness=55, fatigue=30, injury_risk=10)
        assert level in ("yellow", "orange")

    def test_very_low_readiness_triggers_red(self):
        level = _determine_risk_level(readiness=35, fatigue=30, injury_risk=10)
        assert level == "red"

    def test_critical_injury_risk_triggers_red(self):
        level = _determine_risk_level(readiness=70, fatigue=40, injury_risk=80)
        assert level == "red"

    def test_high_fatigue_triggers_orange_or_red(self):
        level = _determine_risk_level(readiness=70, fatigue=75, injury_risk=20)
        assert level in ("orange", "red")

    def test_none_values_return_green(self):
        level = _determine_risk_level(readiness=None, fatigue=None, injury_risk=None)
        assert level == "green"

    def test_priority_order_red_wins(self):
        # Both low readiness AND high fatigue -> red
        level = _determine_risk_level(readiness=35, fatigue=85, injury_risk=75)
        assert level == "red"


# ── Tests: _generate_athlete_alerts ───────────────────────────────────────────

class TestGenerateAthleteAlerts:
    def test_no_alerts_when_all_good(self):
        alerts = _generate_athlete_alerts(
            readiness=80,
            fatigue=30,
            injury_risk=20,
            acwr=1.1,
            days_since_session=2,
        )
        assert len(alerts) == 0

    def test_injury_risk_alert_when_above_65(self):
        alerts = _generate_athlete_alerts(
            readiness=70,
            fatigue=40,
            injury_risk=70,
            acwr=1.1,
            days_since_session=2,
        )
        injury_alerts = [a for a in alerts if a.alert_type == "injury_risk"]
        assert len(injury_alerts) == 1

    def test_overtraining_alert_when_acwr_high(self):
        alerts = _generate_athlete_alerts(
            readiness=70,
            fatigue=40,
            injury_risk=20,
            acwr=1.6,
            days_since_session=2,
        )
        ot_alerts = [a for a in alerts if a.alert_type == "overtraining"]
        assert len(ot_alerts) == 1

    def test_inactivity_alert_after_10_days(self):
        alerts = _generate_athlete_alerts(
            readiness=70,
            fatigue=40,
            injury_risk=20,
            acwr=1.0,
            days_since_session=12,
        )
        inact_alerts = [a for a in alerts if a.alert_type == "inactivity"]
        assert len(inact_alerts) == 1

    def test_low_readiness_alert(self):
        alerts = _generate_athlete_alerts(
            readiness=40,
            fatigue=40,
            injury_risk=20,
            acwr=1.0,
            days_since_session=2,
        )
        lr_alerts = [a for a in alerts if a.alert_type == "low_readiness"]
        assert len(lr_alerts) == 1

    def test_critical_injury_risk_is_critical_severity(self):
        alerts = _generate_athlete_alerts(
            readiness=70,
            fatigue=40,
            injury_risk=85,
            acwr=1.0,
            days_since_session=2,
        )
        injury_alerts = [a for a in alerts if a.alert_type == "injury_risk"]
        assert len(injury_alerts) == 1
        assert injury_alerts[0].severity == "critical"


# ── Tests: compute_athlete_dashboard_summary ──────────────────────────────────

class TestComputeAthleteDashboardSummary:
    def test_minimal_inputs(self):
        summary = compute_athlete_dashboard_summary(
            athlete_id="athlete_1",
            athlete_name="Test Athlete",
        )
        assert summary.athlete_id == "athlete_1"
        assert summary.athlete_name == "Test Athlete"
        assert summary.risk_level == "green"  # no data = green

    def test_all_fields_present(self):
        summary = compute_athlete_dashboard_summary(
            athlete_id="a1",
            athlete_name="Athlete A",
            readiness_score=75.0,
            fatigue_score=40.0,
            injury_risk_score=20.0,
            biological_age_delta=-3.0,
            movement_health_score=80.0,
            nutrition_compliance=85.0,
            sleep_quality=90.0,
            training_load_this_week=350.0,
            acwr=1.1,
            days_since_last_session=1,
        )
        assert summary.readiness_score == 75.0
        assert summary.biological_age_delta == -3.0
        assert summary.risk_level == "green"

    def test_high_risk_scenario(self):
        summary = compute_athlete_dashboard_summary(
            athlete_id="a2",
            athlete_name="At Risk Athlete",
            readiness_score=35.0,  # critical
            fatigue_score=80.0,
            injury_risk_score=75.0,
        )
        assert summary.risk_level in ("orange", "red")
        assert len(summary.active_alerts) > 0

    def test_to_dict_serializable(self):
        summary = compute_athlete_dashboard_summary(
            athlete_id="a3",
            athlete_name="Test",
        )
        d = summary.to_dict()
        assert isinstance(d, dict)
        assert "athlete_id" in d
        assert "risk_level" in d
        assert "active_alerts" in d

    def test_snapshot_date_defaults_to_today(self):
        summary = compute_athlete_dashboard_summary(
            athlete_id="a4",
            athlete_name="Test",
        )
        assert summary.snapshot_date == date.today()

    def test_build_coach_context_short_enough(self):
        summary = compute_athlete_dashboard_summary(
            athlete_id="a5",
            athlete_name="Very Long Athlete Name That Could Break Things",
            readiness_score=75.0,
            fatigue_score=50.0,
        )
        ctx = build_coach_athlete_context(summary)
        assert isinstance(ctx, str)
        assert len(ctx) <= 200
