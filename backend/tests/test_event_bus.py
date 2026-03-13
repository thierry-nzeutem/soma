"""
Tests pour EventBus — LOT 11.
~15 tests (in-process asyncio event bus).
"""
import pytest
import asyncio
from datetime import datetime
import uuid

from app.events.event_bus import EventBus, get_event_bus
from app.events.event_types import (
    SomaEvent,
    MealLogged,
    WorkoutCompleted,
    DigitalTwinComputed,
    MetricsComputed,
)


# ── EventBus core ─────────────────────────────────────────────────────────────

class TestEventBus:

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self):
        bus = EventBus()
        received = []

        @bus.on(MealLogged)
        async def handler(event: MealLogged):
            received.append(event)

        event = MealLogged(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)
        assert len(received) == 1
        assert received[0] is event

    @pytest.mark.asyncio
    async def test_multiple_handlers_for_same_event(self):
        bus = EventBus()
        calls = []

        @bus.on(WorkoutCompleted)
        async def handler1(event):
            calls.append("h1")

        @bus.on(WorkoutCompleted)
        async def handler2(event):
            calls.append("h2")

        event = WorkoutCompleted(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)
        assert "h1" in calls
        assert "h2" in calls

    @pytest.mark.asyncio
    async def test_handler_not_called_for_different_event_type(self):
        bus = EventBus()
        received = []

        @bus.on(MealLogged)
        async def handler(event):
            received.append(event)

        # Publish a different event type
        event = WorkoutCompleted(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)
        assert received == []

    @pytest.mark.asyncio
    async def test_subscribe_programmatic(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(MetricsComputed, handler)
        event = MetricsComputed(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_handler(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(MealLogged, handler)
        bus.unsubscribe(MealLogged, handler)

        event = MealLogged(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)
        assert received == []

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_propagate(self):
        bus = EventBus()

        @bus.on(MealLogged)
        async def failing_handler(event):
            raise ValueError("Test error")

        # Should not raise
        event = MealLogged(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)  # Should not raise

    @pytest.mark.asyncio
    async def test_publish_fire_and_forget(self):
        bus = EventBus()
        received = []

        @bus.on(DigitalTwinComputed)
        async def handler(event):
            received.append(event)

        event = DigitalTwinComputed(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        await bus.publish(event)  # fire-and-forget
        # Give the event loop a moment to process
        await asyncio.sleep(0.05)
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_no_handlers_no_error(self):
        bus = EventBus()
        event = MealLogged(user_id=uuid.uuid4(), occurred_at=datetime.utcnow())
        # No handlers registered — should not raise
        await bus.publish_and_wait(event)

    @pytest.mark.asyncio
    async def test_event_user_id_preserved(self):
        bus = EventBus()
        uid = uuid.uuid4()
        received_uid = None

        @bus.on(MealLogged)
        async def handler(event: MealLogged):
            nonlocal received_uid
            received_uid = event.user_id

        event = MealLogged(user_id=uid, occurred_at=datetime.utcnow())
        await bus.publish_and_wait(event)
        assert received_uid == uid


# ── SomaEvent base ────────────────────────────────────────────────────────────

class TestSomaEvent:
    def test_event_has_user_id_and_occurred_at(self):
        uid = uuid.uuid4()
        now = datetime.utcnow()
        event = MealLogged(user_id=uid, occurred_at=now)
        assert event.user_id == uid
        assert event.occurred_at == now

    def test_workout_completed_event(self):
        event = WorkoutCompleted(
            user_id=uuid.uuid4(),
            occurred_at=datetime.utcnow(),
        )
        assert isinstance(event, SomaEvent)


# ── get_event_bus singleton ───────────────────────────────────────────────────

class TestGetEventBus:
    def test_singleton_returns_same_instance(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_singleton_is_event_bus_instance(self):
        assert isinstance(get_event_bus(), EventBus)
