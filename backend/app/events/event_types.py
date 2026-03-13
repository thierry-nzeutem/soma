"""
SOMA event types — typed dataclasses for the in-process event bus.

All events inherit from SomaEvent and carry a user_id + timestamp.
The event bus dispatches them to registered async handlers.

Usage:
    from app.events.event_types import WorkoutCompleted
    await get_event_bus().publish(WorkoutCompleted(user_id=user_id, session_id=session_id))
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class SomaEvent:
    """Base class for all SOMA events."""
    user_id: uuid.UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)


# ── Journal events ────────────────────────────────────────────────────────────

@dataclass
class MealLogged(SomaEvent):
    """Fired after a nutrition entry is persisted."""
    entry_id: Optional[uuid.UUID] = None
    calories: Optional[float] = None
    meal_type: Optional[str] = None


@dataclass
class SleepLogged(SomaEvent):
    """Fired after a sleep log is recorded."""
    sleep_minutes: Optional[float] = None
    sleep_score: Optional[float] = None
    log_date: Optional[date] = None


@dataclass
class WorkoutCompleted(SomaEvent):
    """Fired after a workout session is ended/saved."""
    session_id: Optional[uuid.UUID] = None
    training_load: Optional[float] = None
    duration_seconds: Optional[int] = None


@dataclass
class VisionSessionSaved(SomaEvent):
    """Fired after a Computer Vision session is persisted."""
    vision_session_id: Optional[uuid.UUID] = None
    exercise_type: Optional[str] = None
    quality_score: Optional[float] = None


# ── Computed / pipeline events ────────────────────────────────────────────────

@dataclass
class MetricsComputed(SomaEvent):
    """Fired after DailyMetrics are recomputed for a user."""
    metrics_date: Optional[date] = None
    completeness_pct: Optional[float] = None


@dataclass
class ReadinessUpdated(SomaEvent):
    """Fired after ReadinessScore is recomputed."""
    score_date: Optional[date] = None
    overall_readiness: Optional[float] = None


@dataclass
class MetabolicStateUpdated(SomaEvent):
    """Fired after MetabolicStateSnapshot is upserted."""
    snapshot_date: Optional[date] = None
    confidence_score: Optional[float] = None


@dataclass
class DigitalTwinComputed(SomaEvent):
    """Fired after DigitalTwinSnapshot is computed and persisted."""
    snapshot_date: Optional[date] = None
    overall_status: Optional[str] = None
    global_confidence: Optional[float] = None


@dataclass
class BiologicalAgeUpdated(SomaEvent):
    """Fired after BiologicalAgeSnapshot is recomputed."""
    snapshot_date: Optional[date] = None
    biological_age: Optional[float] = None
    biological_age_delta: Optional[float] = None


@dataclass
class NutritionTargetsUpdated(SomaEvent):
    """Fired after adaptive nutrition targets are recomputed."""
    target_date: Optional[date] = None
    day_type: Optional[str] = None
    calorie_target: Optional[float] = None


@dataclass
class CoachQuestionAsked(SomaEvent):
    """Fired after a user sends a message to the coach."""
    thread_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
