/// Notifier Riverpod pour le Dashboard — métriques journalières.
///
/// LOT 12 : Offline-first avec cache local (TTL 4h).
///   - build() : cache immédiat + refresh background
///   - refresh() : force réseau + mise à jour cache
///   - Dégradation gracieuse si offline : stale cache plutôt qu'erreur
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/cache/cache_config.dart';
import '../../core/cache/local_cache.dart';
import '../../core/models/daily_metrics.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final dashboardProvider =
    AsyncNotifierProvider<DashboardNotifier, DailyMetrics>(
  DashboardNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class DashboardNotifier extends AsyncNotifier<DailyMetrics> {
  static const _cacheKey = 'home_summary_default';

  @override
  Future<DailyMetrics> build() async {
    final cache = ref.read(localCacheProvider);

    // 1. Cache frais disponible → retour immédiat + refresh background.
    final cached = await cache.get(_cacheKey);
    if (cached != null) {
      Future.microtask(_backgroundRefresh);
      return DailyMetrics.fromJson(cached);
    }

    // 2. Pas de cache → fetch réseau.
    return _fetchAndStore();
  }

  /// Force le rechargement des métriques (pull-to-refresh).
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchAndStore);
  }

  // ── Privé ──────────────────────────────────────────────────────────────────

  Future<DailyMetrics> _fetchAndStore() async {
    final client = ref.read(apiClientProvider);
    final cache = ref.read(localCacheProvider);

    try {
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.metricsDaily,
      );
      final json = responseJson(response);
      await cache.set(_cacheKey, json, ttl: CacheTTL.homeSummary);
      return DailyMetrics.fromJson(json);
    } catch (e) {
      // Offline : essayer le stale cache plutôt que propager l'erreur.
      final stale = await cache.get(
        _cacheKey,
        ignoreExpiry: true,
      );
      if (stale != null) return DailyMetrics.fromJson(stale);
      rethrow;
    }
  }

  Future<void> _backgroundRefresh() async {
    try {
      final fresh = await _fetchAndStore();
      state = AsyncData(fresh);
    } catch (_) {
      // Silencieux : le cache valide est déjà affiché.
    }
  }

  /// Invalide le cache (utilisé lors du logout).
  Future<void> invalidateCache() async {
    final cache = ref.read(localCacheProvider);
    await cache.remove(_cacheKey);
  }
}
