"""
Tests pour CacheService et CacheKeys — LOT 11.
~15 tests (sans Redis réel, utilise graceful degradation).
"""
import pytest
from datetime import date
import uuid

from app.cache.cache_service import CacheService
from app.cache.cache_keys import CacheKeys, TTL


# ── CacheKeys ─────────────────────────────────────────────────────────────────

class TestCacheKeys:
    def test_twin_key_contains_user_id_and_date(self):
        uid = uuid.uuid4()
        d = date(2025, 1, 15)
        key = CacheKeys.twin_today(uid, d)
        assert str(uid) in key
        assert "2025-01-15" in key

    def test_biological_age_key_distinct_from_twin(self):
        uid = uuid.uuid4()
        d = date.today()
        k1 = CacheKeys.twin_today(uid, d)
        k2 = CacheKeys.biological_age(uid, d)
        assert k1 != k2

    def test_adaptive_nutrition_key(self):
        uid = uuid.uuid4()
        key = CacheKeys.adaptive_nutrition(uid, date.today())
        assert "nutrition" in key.lower() or str(uid) in key

    def test_motion_summary_key(self):
        uid = uuid.uuid4()
        key = CacheKeys.motion_summary(uid, date.today())
        assert "motion" in key.lower() or str(uid) in key

    def test_user_all_prefix(self):
        uid = uuid.uuid4()
        prefix = CacheKeys.user_all_prefix(uid)
        assert str(uid) in prefix

    def test_different_users_different_keys(self):
        uid1, uid2 = uuid.uuid4(), uuid.uuid4()
        d = date.today()
        assert CacheKeys.twin_today(uid1, d) != CacheKeys.twin_today(uid2, d)

    def test_different_dates_different_keys(self):
        uid = uuid.uuid4()
        k1 = CacheKeys.twin_today(uid, date(2025, 1, 1))
        k2 = CacheKeys.twin_today(uid, date(2025, 1, 2))
        assert k1 != k2


# ── TTL constants ─────────────────────────────────────────────────────────────

class TestTTL:
    def test_twin_ttl_is_4h(self):
        assert TTL.TWIN == 4 * 3600

    def test_bio_age_ttl_is_24h(self):
        assert TTL.BIOLOGICAL_AGE == 24 * 3600

    def test_adaptive_nutrition_ttl_is_6h(self):
        assert TTL.ADAPTIVE_NUTRITION == 6 * 3600

    def test_motion_ttl_is_6h(self):
        assert TTL.MOTION == 6 * 3600

    def test_home_summary_ttl_is_5min(self):
        assert TTL.HOME_SUMMARY == 5 * 60


# ── CacheService (graceful degradation without Redis) ─────────────────────────

class TestCacheServiceDegradation:
    """
    Tests the graceful degradation behavior when Redis is unavailable.
    Since Redis is not running in the test environment, all operations
    should return None/False without raising exceptions.
    """

    @pytest.fixture
    def cache(self):
        """Create a CacheService that is not connected (simulating Redis unavailable)."""
        svc = CacheService(redis_url="redis://invalid-host:6379/0")
        return svc

    @pytest.mark.asyncio
    async def test_get_returns_none_when_disconnected(self, cache):
        result = await cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_when_disconnected(self, cache):
        result = await cache.set("test_key", {"data": 1}, ttl=300)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_disconnected(self, cache):
        result = await cache.delete("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_prefix_returns_zero_when_disconnected(self, cache):
        result = await cache.invalidate_prefix("user:123")
        assert result == 0

    @pytest.mark.asyncio
    async def test_no_exception_on_get(self, cache):
        # Should not raise
        await cache.get("any_key")

    @pytest.mark.asyncio
    async def test_no_exception_on_set(self, cache):
        # Should not raise
        await cache.set("any_key", {"value": "test"}, ttl=60)
