"""
SOMA LOT 14 — Coach Pro / Multi-Athletes Platform.

Provides multi-tenant coach functionality:
- Coach profiles and athlete management
- Athlete Dashboard Summaries (aggregated from all SOMA engines)
- Training program management
- Athlete notes and alerts
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class CoachProfile:
    """Coach account with professional profile."""
    id: str
    user_id: str
    name: str
    specializations: list[str]
    certification: Optional[str]
    bio: Optional[str]
    max_athletes: int = 50
    is_active: bool = True
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "specializations": self.specializations,
            "certification": self.certification,
            "bio": self.bio,
            "max_athletes": self.max_athletes,
            "is_active": self.is_active,
        }


@dataclass
class AthleteProfile:
    """Athlete profile linked to a SOMA user account."""
    id: str
    user_id: str
    display_name: str
    sport: Optional[str]
    goal: Optional[str]
    date_of_birth: Optional[date]
    notes: Optional[str]
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "sport": self.sport,
            "goal": self.goal,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "notes": self.notes,
            "is_active": self.is_active,
        }


@dataclass
class CoachAthleteLink:
    """Many-to-many link between coach and athlete."""
    id: str
    coach_id: str
    athlete_id: str
    linked_at: datetime
    is_active: bool = True
    role: str = "primary"


@dataclass
class AthleteDashboardSummary:
    """Aggregated health snapshot for the coach dashboard."""
    athlete_id: str
    athlete_name: str
    snapshot_date: date
    readiness_score: Optional[float]
    fatigue_score: Optional[float]
    injury_risk_score: Optional[float]
    biological_age_delta: Optional[float]
    movement_health_score: Optional[float]
    nutrition_compliance: Optional[float]
    sleep_quality: Optional[float]
    training_load_this_week: Optional[float]
    acwr: Optional[float]
    days_since_last_session: Optional[int]
    active_alerts: list[str]
    risk_level: str

    def to_dict(self) -> dict:
        return {
            "athlete_id": self.athlete_id,
            "athlete_name": self.athlete_name,
            "snapshot_date": self.snapshot_date.isoformat(),
            "readiness_score": self.readiness_score,
            "fatigue_score": self.fatigue_score,
            "injury_risk_score": self.injury_risk_score,
            "biological_age_delta": self.biological_age_delta,
            "movement_health_score": self.movement_health_score,
            "nutrition_compliance": self.nutrition_compliance,
            "sleep_quality": self.sleep_quality,
            "training_load_this_week": self.training_load_this_week,
            "acwr": self.acwr,
            "days_since_last_session": self.days_since_last_session,
            "active_alerts": self.active_alerts,
            "risk_level": self.risk_level,
        }


@dataclass
class TrainingProgram:
    """Hierarchical training program assigned to athletes."""
    id: str
    coach_id: str
    name: str
    description: Optional[str]
    duration_weeks: int
    sport_focus: str
    difficulty: str
    weeks: list["ProgramWeek"] = field(default_factory=list)
    created_at: Optional[datetime] = None
    is_template: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "name": self.name,
            "description": self.description,
            "duration_weeks": self.duration_weeks,
            "sport_focus": self.sport_focus,
            "difficulty": self.difficulty,
            "weeks": [w.to_dict() for w in self.weeks],
            "is_template": self.is_template,
        }


@dataclass
class ProgramWeek:
    """One week within a training program."""
    week_number: int
    theme: str
    target_volume: str
    workouts: list["ProgramWorkout"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "week_number": self.week_number,
            "theme": self.theme,
            "target_volume": self.target_volume,
            "workouts": [w.to_dict() for w in self.workouts],
        }


@dataclass
class ProgramWorkout:
    """Single workout within a program week."""
    day_of_week: int
    name: str
    workout_type: str
    duration_minutes: int
    intensity: str
    exercises: list[dict]
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "day_of_week": self.day_of_week,
            "name": self.name,
            "workout_type": self.workout_type,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "exercises": self.exercises,
            "notes": self.notes,
        }


@dataclass
class AthleteNote:
    """Coach observation/note for an athlete."""
    id: str
    coach_id: str
    athlete_id: str
    note_date: date
    content: str
    category: str
    is_private: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "athlete_id": self.athlete_id,
            "note_date": self.note_date.isoformat(),
            "content": self.content,
            "category": self.category,
            "is_private": self.is_private,
        }


@dataclass
class AthleteAlert:
    """Automated health alert for the coach dashboard."""
    id: str
    athlete_id: str
    alert_type: str
    severity: str
    message: str
    generated_at: datetime
    is_acknowledged: bool = False
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "generated_at": self.generated_at.isoformat(),
            "is_acknowledged": self.is_acknowledged,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
        }


def _determine_risk_level(
    readiness: Optional[float],
    fatigue: Optional[float],
    injury_risk: Optional[float],
) -> str:
    """
    Determine overall risk level for the coach dashboard.

    green: All metrics in safe range
    yellow: Some metrics approaching concern
    orange: One metric in concerning range
    red: One or more metrics critical
    """
    flags = []
    if readiness is not None:
        if readiness < 40:
            flags.append("red")
        elif readiness < 60:
            flags.append("yellow")
    if fatigue is not None:
        if fatigue > 80:
            flags.append("red")
        elif fatigue > 65:
            flags.append("orange")
        elif fatigue > 50:
            flags.append("yellow")
    if injury_risk is not None:
        if injury_risk > 70:
            flags.append("red")
        elif injury_risk > 50:
            flags.append("orange")
        elif injury_risk > 30:
            flags.append("yellow")
    if not flags:
        return "green"
    priority = ["red", "orange", "yellow", "green"]
    for level in priority:
        if level in flags:
            return level
    return "green"


def _generate_athlete_alerts(
    readiness: Optional[float],
    fatigue: Optional[float],
    injury_risk: Optional[float],
    acwr: Optional[float],
    days_since_session: Optional[int],
) -> list[AthleteAlert]:
    """Generate automated alerts based on athlete metrics."""
    alerts = []
    now = datetime.now()
    if injury_risk is not None and injury_risk > 65:
        severity = "critical" if injury_risk > 80 else "warning"
        msg = f"Risque blessure élevé: {injury_risk:.0f}/100 — réviser la charge d'entraînement."
        alerts.append(AthleteAlert(
            id=str(uuid.uuid4()), athlete_id="", alert_type="injury_risk",
            severity=severity, message=msg, generated_at=now,
            metric_value=injury_risk, threshold_value=65.0,
        ))
    if acwr is not None and acwr > 1.5:
        msg = f"ACWR critique: {acwr:.2f} — risque de surentraînement."
        alerts.append(AthleteAlert(
            id=str(uuid.uuid4()), athlete_id="", alert_type="overtraining",
            severity="warning" if acwr < 1.8 else "critical", message=msg,
            generated_at=now, metric_value=acwr, threshold_value=1.5,
        ))
    if readiness is not None and readiness < 45:
        msg = f"Readiness basse: {readiness:.0f}/100 — considérer une journée de récupération."
        alerts.append(AthleteAlert(
            id=str(uuid.uuid4()), athlete_id="", alert_type="low_readiness",
            severity="warning", message=msg, generated_at=now,
            metric_value=readiness, threshold_value=45.0,
        ))
    if fatigue is not None and fatigue > 80:
        msg = f"Fatigue excessive: {fatigue:.0f}/100 — repos recommandé."
        alerts.append(AthleteAlert(
            id=str(uuid.uuid4()), athlete_id="", alert_type="poor_recovery",
            severity="warning", message=msg, generated_at=now,
            metric_value=fatigue, threshold_value=80.0,
        ))
    if days_since_session is not None and days_since_session > 10:
        msg = f"Inactivité: {days_since_session} jours sans séance enregistrée."
        alerts.append(AthleteAlert(
            id=str(uuid.uuid4()), athlete_id="", alert_type="inactivity",
            severity="info", message=msg, generated_at=now,
            metric_value=float(days_since_session), threshold_value=10.0,
        ))
    return alerts


def compute_athlete_dashboard_summary(
    athlete_id: str,
    athlete_name: str,
    readiness_score: Optional[float] = None,
    fatigue_score: Optional[float] = None,
    injury_risk_score: Optional[float] = None,
    biological_age_delta: Optional[float] = None,
    movement_health_score: Optional[float] = None,
    nutrition_compliance: Optional[float] = None,
    sleep_quality: Optional[float] = None,
    training_load_this_week: Optional[float] = None,
    acwr: Optional[float] = None,
    days_since_last_session: Optional[int] = None,
    snapshot_date: Optional[date] = None,
) -> AthleteDashboardSummary:
    """
    Compute comprehensive athlete dashboard summary for the coach.

    Aggregates data from all SOMA engines into a unified view.
    All inputs optional — graceful degradation.
    """
    target_date = snapshot_date or date.today()
    risk_level = _determine_risk_level(readiness_score, fatigue_score, injury_risk_score)
    alerts = _generate_athlete_alerts(
        readiness=readiness_score,
        fatigue=fatigue_score,
        injury_risk=injury_risk_score,
        acwr=acwr,
        days_since_session=days_since_last_session,
    )
    for alert in alerts:
        alert.athlete_id = athlete_id
    alert_messages = [a.message for a in alerts if not a.is_acknowledged]
    return AthleteDashboardSummary(
        athlete_id=athlete_id,
        athlete_name=athlete_name,
        snapshot_date=target_date,
        readiness_score=readiness_score,
        fatigue_score=fatigue_score,
        injury_risk_score=injury_risk_score,
        biological_age_delta=biological_age_delta,
        movement_health_score=movement_health_score,
        nutrition_compliance=nutrition_compliance,
        sleep_quality=sleep_quality,
        training_load_this_week=training_load_this_week,
        acwr=acwr,
        days_since_last_session=days_since_last_session,
        active_alerts=alert_messages,
        risk_level=risk_level,
    )


def build_coach_athlete_context(summary: AthleteDashboardSummary) -> str:
    """Compact summary (≤200 chars) for coach AI context."""
    alerts_str = f", alertes: {len(summary.active_alerts)}" if summary.active_alerts else ""
    parts = (
        f"Athlète {summary.athlete_name}: readiness {summary.readiness_score or '?'}/100, "
        f"fatigue {summary.fatigue_score or '?'}/100, risque {summary.risk_level}{alerts_str}"
    )
    return (parts[0] + parts[1])[:200]
