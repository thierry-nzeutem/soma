/// Notifier Riverpod pour le Plan Santé — morning briefing.
///
/// LOT 12 : Offline-first avec cache local (TTL 6h).
///   - build() : cache immédiat + refresh background
///   - refresh() : force réseau + mise à jour cache
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/cache/cache_config.dart';
import '../../core/cache/local_cache.dart';
import '../../core/models/health_plan.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final healthPlanProvider =
    AsyncNotifierProvider<HealthPlanNotifier, DailyHealthPlan>(
  HealthPlanNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class HealthPlanNotifier extends AsyncNotifier<DailyHealthPlan> {
  static const _cacheKey = 'health_plan_default';

  @override
  Future<DailyHealthPlan> build() async {
    final cache = ref.read(localCacheProvider);

    // 1. Cache frais → retour immédiat + refresh background.
    final cached = await cache.get(_cacheKey);
    if (cached != null) {
      Future.microtask(_backgroundRefresh);
      return DailyHealthPlan.fromJson(cached);
    }

    // 2. Pas de cache → fetch réseau.
    return _fetchAndStore();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchAndStore);
  }

  // ── Privé ──────────────────────────────────────────────────────────────────

  Future<DailyHealthPlan> _fetchAndStore() async {
    final client = ref.read(apiClientProvider);
    final cache = ref.read(localCacheProvider);

    try {
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.healthPlanToday,
      );
      final json = responseJson(response);
      await cache.set(_cacheKey, json, ttl: CacheTTL.healthPlan);
      return DailyHealthPlan.fromJson(json);
    } catch (e) {
      // Offline : stale cache si disponible.
      final stale = await cache.get(
        _cacheKey,
        ignoreExpiry: true,
      );
      if (stale != null) return DailyHealthPlan.fromJson(stale);
      rethrow;
    }
  }

  Future<void> _backgroundRefresh() async {
    try {
      final fresh = await _fetchAndStore();
      state = AsyncData(fresh);
    } catch (_) {}
  }

  Future<void> invalidateCache() async {
    final cache = ref.read(localCacheProvider);
    await cache.remove(_cacheKey);
  }
}
