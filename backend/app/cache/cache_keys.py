"""
Cache key builders and TTL constants.
All keys follow the pattern: {prefix}:{user_id}:{date_or_qualifier}
"""
import uuid
from datetime import date


# ── TTL Constants (seconds) ───────────────────────────────────────────────────
class TTL:
    """Time-to-live constants for each cache domain."""
    # New LOT 11 engines
    TWIN = 14_400           # 4h — Digital Twin (computed from daily data)
    BIOLOGICAL_AGE = 86_400 # 24h — Biological Age (slow-moving metric)
    ADAPTIVE_NUTRITION = 21_600  # 6h — Adaptive Nutrition (day-scoped)
    MOTION = 21_600         # 6h — Motion Intelligence (aggregated sessions)

    # Existing
    HOME_SUMMARY = 300      # 5min — Home summary (fast aggregator)
    HEALTH_PLAN = 21_600    # 6h — Health plan (matches existing DailyRecommendation)
    LONGEVITY = 86_400      # 24h — Longevity score
    READINESS = 3_600       # 1h — Readiness (matches MIN_RECOMPUTE_INTERVAL_H)
    METABOLIC_TWIN = 14_400 # 4h — Metabolic state snapshot
    COACH_CONTEXT = 900     # 15min — Coach context (fresh data preferred)
    PREDICTIONS = 3_600     # 1h — Injury risk / overtraining predictions


# ── Key Builders ─────────────────────────────────────────────────────────────
class CacheKeys:
    """Namespaced Redis key builders."""

    # ── LOT 11 domains ────────────────────────────────────────────────────────
    @staticmethod
    def twin_today(user_id: uuid.UUID, target_date: date) -> str:
        return f"twin:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def twin_history_prefix(user_id: uuid.UUID) -> str:
        return f"twin:hist:{user_id}"

    @staticmethod
    def biological_age(user_id: uuid.UUID, target_date: date) -> str:
        return f"bio_age:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def biological_age_history_prefix(user_id: uuid.UUID) -> str:
        return f"bio_age:hist:{user_id}"

    @staticmethod
    def adaptive_nutrition(user_id: uuid.UUID, target_date: date) -> str:
        return f"adaptive_nutrition:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def motion_summary(user_id: uuid.UUID, target_date: date) -> str:
        return f"motion:{user_id}:{target_date.isoformat()}"

    # ── Existing domains ──────────────────────────────────────────────────────
    @staticmethod
    def home_summary(user_id: uuid.UUID, target_date: date) -> str:
        return f"home:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def health_plan(user_id: uuid.UUID, target_date: date) -> str:
        return f"health_plan:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def longevity(user_id: uuid.UUID, target_date: date) -> str:
        return f"longevity:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def readiness(user_id: uuid.UUID, target_date: date) -> str:
        return f"readiness:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def metabolic_twin(user_id: uuid.UUID, target_date: date) -> str:
        return f"metabolic:{user_id}:{target_date.isoformat()}"

    @staticmethod
    def predictions(user_id: uuid.UUID, target_date: date) -> str:
        return f"predictions:{user_id}:{target_date.isoformat()}"

    # ── Invalidation patterns ──────────────────────────────────────────────────
    @staticmethod
    def user_all_prefix(user_id: uuid.UUID) -> str:
        """Prefix to invalidate ALL cache for a user (use with scan/delete pattern)."""
        return f"*:{user_id}:*"
