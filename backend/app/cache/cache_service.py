"""
Redis-based cache service (async).

Usage:
    cache = CacheService(redis_url)
    await cache.set(key, value, ttl=3600)
    value = await cache.get(key)  # returns None if missing/expired
    await cache.delete(key)
    await cache.invalidate_prefix("twin:{user_id}")

Design:
- Values are JSON-serialized (dicts, lists, primitives).
- TTL in seconds.
- Graceful degradation: if Redis unavailable, log warning and return None (no crash).
- Singleton via get_cache_service() with lazy init.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Redis is optional — import gracefully
try:
    import redis.asyncio as aioredis  # type: ignore[import]
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    logger.warning("redis package not installed — cache disabled. Install redis>=5.0 to enable.")


class CacheService:
    """Async Redis cache with JSON serialization and graceful degradation."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Optional[Any] = None
        self._enabled = _REDIS_AVAILABLE and bool(redis_url)

    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        if not self._enabled:
            return
        try:
            self._client = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await self._client.ping()
            logger.info("Redis cache connected: %s", self._redis_url.split("@")[-1])
        except Exception as exc:
            logger.warning("Redis connection failed (%s) — cache disabled.", exc)
            self._client = None
            self._enabled = False

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Core operations ───────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        """Return cached value (deserialized) or None if missing/error."""
        if not self._client:
            return None
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.debug("Cache GET error key=%s: %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Store value as JSON with TTL. Returns True on success."""
        if not self._client:
            return False
        try:
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl, serialized)
            return True
        except Exception as exc:
            logger.debug("Cache SET error key=%s: %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a specific key. Returns True if key existed."""
        if not self._client:
            return False
        try:
            result = await self._client.delete(key)
            return bool(result)
        except Exception as exc:
            logger.debug("Cache DELETE error key=%s: %s", key, exc)
            return False

    async def invalidate_prefix(self, prefix: str) -> int:
        """
        Delete all keys matching a prefix pattern (uses SCAN to avoid blocking).
        Returns count of deleted keys.
        """
        if not self._client:
            return 0
        deleted = 0
        pattern = f"{prefix}*" if not prefix.endswith("*") else prefix
        try:
            async for key in self._client.scan_iter(match=pattern, count=100):
                await self._client.delete(key)
                deleted += 1
        except Exception as exc:
            logger.debug("Cache INVALIDATE_PREFIX error prefix=%s: %s", prefix, exc)
        return deleted

    async def exists(self, key: str) -> bool:
        """Return True if key exists in cache."""
        if not self._client:
            return False
        try:
            return bool(await self._client.exists(key))
        except Exception:
            return False

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None


# ── Singleton ────────────────────────────────────────────────────────────────

_cache_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Return the global CacheService singleton (lazy init)."""
    global _cache_instance
    if _cache_instance is None:
        from app.core.config import settings
        _cache_instance = CacheService(settings.REDIS_URL or "")
    return _cache_instance


async def init_cache() -> None:
    """Call at app startup to connect Redis."""
    await get_cache_service().connect()


async def close_cache() -> None:
    """Call at app shutdown to disconnect Redis."""
    await get_cache_service().disconnect()
