"""Analytics product module — LOT 18.

Fournit :
  - track_event(db, user_id, event_name, properties) — fire-and-forget
  - EVENTS : ensemble des noms d'événements valides
"""
from app.core.analytics.tracker import track_event, EVENTS

__all__ = ["track_event", "EVENTS"]
