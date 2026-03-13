"""
In-process async event bus for SOMA.

Design:
- Simple pub/sub using asyncio (no external broker for LOT 11).
- Redis Pub/Sub adapter planned for LOT 12 (>100k users).
- Handlers are async callables registered per event type.
- Dispatch is fire-and-forget: errors in handlers are logged, not re-raised.
- Thread-safe: uses asyncio.Lock for handler registration.

Usage:
    bus = get_event_bus()

    # Subscribe
    @bus.on(WorkoutCompleted)
    async def handle_workout(event: WorkoutCompleted) -> None:
        await invalidate_training_cache(event.user_id)

    # Publish (fire-and-forget)
    await bus.publish(WorkoutCompleted(user_id=uid, session_id=sid))

    # Publish and wait for all handlers
    await bus.publish_and_wait(WorkoutCompleted(user_id=uid))
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Type

from app.events.event_types import SomaEvent

logger = logging.getLogger(__name__)

Handler = Callable[[Any], Awaitable[None]]


class EventBus:
    """Async in-process event bus."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def on(self, event_type: Type[SomaEvent]) -> Callable[[Handler], Handler]:
        """Decorator to register an async handler for an event type."""
        def decorator(fn: Handler) -> Handler:
            self._handlers[event_type].append(fn)
            logger.debug("EventBus: registered handler %s for %s", fn.__name__, event_type.__name__)
            return fn
        return decorator

    def subscribe(self, event_type: Type[SomaEvent], handler: Handler) -> None:
        """Programmatic handler registration (alternative to @bus.on)."""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[SomaEvent], handler: Handler) -> None:
        """Remove a previously registered handler."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: SomaEvent) -> None:
        """
        Fire-and-forget: schedule all handlers as background tasks.
        Errors in handlers are caught and logged individually.
        """
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return
        for handler in handlers:
            asyncio.create_task(self._safe_call(handler, event))

    async def publish_and_wait(self, event: SomaEvent) -> None:
        """
        Publish and await all handlers before returning.
        Useful in tests or when downstream consistency is required.
        """
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return
        tasks = [self._safe_call(h, event) for h in handlers]
        await asyncio.gather(*tasks)

    async def _safe_call(self, handler: Handler, event: SomaEvent) -> None:
        """Call handler, catching and logging any exception."""
        try:
            await handler(event)
        except Exception as exc:
            logger.error(
                "EventBus handler %s failed for %s: %s",
                getattr(handler, "__name__", repr(handler)),
                type(event).__name__,
                exc,
                exc_info=True,
            )

    def clear_all_handlers(self) -> None:
        """Clear all registered handlers (useful in tests)."""
        self._handlers.clear()

    def handler_count(self, event_type: Type[SomaEvent]) -> int:
        """Return number of handlers for a given event type."""
        return len(self._handlers.get(event_type, []))


# ── Singleton ────────────────────────────────────────────────────────────────

_bus_instance: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return the global EventBus singleton."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = EventBus()
    return _bus_instance
