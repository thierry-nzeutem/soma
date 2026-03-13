/// Briefing Notifier — LOT 18.
///
/// Fournit le briefing matinal quotidien via GET /api/v1/daily/briefing.
/// Cache local TTL 4h + dégradation offline gracieuse (pattern identique à
/// [TwinNotifier]).
///
/// Provider :
///   briefingProvider → [DailyBriefing?] (null tant que pas de données)
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/cache/cache_config.dart';
import '../../core/cache/local_cache.dart';
import '../../core/models/daily_briefing.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final briefingProvider =
    AsyncNotifierProvider<BriefingNotifier, DailyBriefing?>(
  BriefingNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class BriefingNotifier extends AsyncNotifier<DailyBriefing?> {
  static const _cacheKey = 'briefing_today_default';

  @override
  Future<DailyBriefing?> build() async {
    final cache = ref.read(localCacheProvider);

    // Cache frais → retour immédiat + refresh background silencieux.
    final cached = await cache.get(_cacheKey);
    if (cached != null) {
      Future.microtask(_backgroundRefresh);
      return DailyBriefing.fromJson(cached);
    }

    return _fetchAndStore();
  }

  // ── Fetch + mise en cache ─────────────────────────────────────────────────

  Future<DailyBriefing?> _fetchAndStore() async {
    final client = ref.read(apiClientProvider);
    final cache = ref.read(localCacheProvider);

    try {
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.dailyBriefing,
      );
      final data = responseJson(response);
      await cache.set(_cacheKey, data, ttl: CacheTTL.dailyBriefing);
      return DailyBriefing.fromJson(data);
    } catch (e) {
      // Dégradation gracieuse : retourner données périmées si disponibles.
      final stale = await cache.get(
        _cacheKey,
        ignoreExpiry: true,
      );
      if (stale != null) return DailyBriefing.fromJson(stale);
      rethrow;
    }
  }

  // ── Refresh background ────────────────────────────────────────────────────

  Future<void> _backgroundRefresh() async {
    try {
      final fresh = await _fetchAndStore();
      state = AsyncData(fresh);
    } catch (_) {
      // Silencieux — l'UI affiche déjà les données du cache.
    }
  }

  // ── API publique ──────────────────────────────────────────────────────────

  /// Force le rechargement depuis l'API.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchAndStore);
  }

  /// Invalide le cache local (utile après saisie de données journalières).
  Future<void> invalidateCache() async {
    final cache = ref.read(localCacheProvider);
    await cache.remove(_cacheKey);
  }
}
