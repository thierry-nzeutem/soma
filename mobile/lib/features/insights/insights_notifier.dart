/// InsightsNotifier — gestion des insights SOMA (LOT 5).
///
/// LOT 12 : Cache local TTL 3h + dégradation offline gracieuse.
/// Expose [insightsProvider] qui consomme GET /api/v1/insights.
/// Supporte : filtrage, mark as read, dismiss.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/cache/cache_config.dart';
import '../../core/cache/local_cache.dart';
import '../../core/models/insight.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final insightsProvider =
    AsyncNotifierProvider<InsightsNotifier, InsightList>(InsightsNotifier.new);

// ── Notifier ──────────────────────────────────────────────────────────────────

class InsightsNotifier extends AsyncNotifier<InsightList> {
  static const _cacheKey = 'insights_default';

  @override
  Future<InsightList> build() async {
    final cache = ref.read(localCacheProvider);

    // 1. Cache frais → retour immédiat + refresh background.
    final cached = await cache.get(_cacheKey);
    if (cached != null) {
      Future.microtask(_backgroundRefresh);
      return InsightList.fromJson(cached);
    }

    // 2. Fetch réseau.
    return _fetchAndStore();
  }

  Future<InsightList> _fetchAndStore({bool unreadOnly = false}) async {
    final client = ref.read(apiClientProvider);
    final cache = ref.read(localCacheProvider);
    final queryParams = <String, dynamic>{};
    if (unreadOnly) queryParams['is_read'] = false;

    try {
      final response = await client.get(
        ApiConstants.insights,
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );
      final json = responseJson(response);
      // Ne pas cacher les requêtes filtrées.
      if (!unreadOnly) {
        await cache.set(_cacheKey, json, ttl: CacheTTL.insights);
      }
      return InsightList.fromJson(json);
    } catch (e) {
      if (unreadOnly) rethrow;
      // Offline : stale cache.
      final stale = await cache.get(
        _cacheKey,
        ignoreExpiry: true,
      );
      if (stale != null) return InsightList.fromJson(stale);
      rethrow;
    }
  }

  Future<void> _backgroundRefresh() async {
    try {
      final fresh = await _fetchAndStore();
      state = AsyncData(fresh);
    } catch (_) {}
  }

  /// Recharge la liste depuis l'API.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchAndStore);
  }

  /// Marque un insight comme lu.
  Future<void> markAsRead(String insightId) async {
    final client = ref.read(apiClientProvider);
    try {
      await client.patch('${ApiConstants.insights}/$insightId/read');
      // Optimistic update : mettre à jour l'état local
      state.whenData((list) {
        final updated = list.insights.map((i) {
          return i.id == insightId
              ? Insight(
                  id: i.id,
                  category: i.category,
                  severity: i.severity,
                  title: i.title,
                  message: i.message,
                  action: i.action,
                  isRead: true,
                  isDismissed: i.isDismissed,
                  detectedAt: i.detectedAt,
                  expiresAt: i.expiresAt,
                )
              : i;
        }).toList();
        state = AsyncData(InsightList(
          insights: updated,
          totalCount: list.totalCount,
          unreadCount: (list.unreadCount - 1).clamp(0, list.totalCount),
        ));
      });
    } catch (_) {
      // Ignorer les erreurs de mise à jour du statut
    }
  }

  /// Dismiss un insight (ne plus l'afficher).
  Future<void> dismiss(String insightId) async {
    final client = ref.read(apiClientProvider);
    try {
      await client.patch('${ApiConstants.insights}/$insightId/dismiss');
      // Retirer de la liste locale
      state.whenData((list) {
        final updated =
            list.insights.where((i) => i.id != insightId).toList();
        final waUnread = list.insights
            .where((i) => i.id == insightId && !i.isRead)
            .isNotEmpty;
        state = AsyncData(InsightList(
          insights: updated,
          totalCount: (list.totalCount - 1).clamp(0, list.totalCount),
          unreadCount: waUnread
              ? (list.unreadCount - 1).clamp(0, list.totalCount)
              : list.unreadCount,
        ));
      });
    } catch (_) {
      // Ignorer les erreurs
    }
  }

  Future<void> invalidateCache() async {
    final cache = ref.read(localCacheProvider);
    await cache.remove(_cacheKey);
  }
}
