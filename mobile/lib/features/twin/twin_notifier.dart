/// Digital Twin Notifier — SOMA LOT 11.
///
/// LOT 12 : Cache local TTL 4h + dégradation offline gracieuse.
/// Providers :
///   twinProvider         → état courant du jumeau (aujourd'hui)
///   twinHistoryProvider  → liste des snapshots historiques
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/cache/cache_config.dart';
import '../../core/cache/local_cache.dart';
import '../../core/models/digital_twin.dart';

// ── Provider état courant ─────────────────────────────────────────────────────

final twinProvider =
    AsyncNotifierProvider<TwinNotifier, DigitalTwinState?>(TwinNotifier.new);

// ── Notifier ─────────────────────────────────────────────────────────────────

class TwinNotifier extends AsyncNotifier<DigitalTwinState?> {
  static const _cacheKey = 'twin_today_default';

  @override
  Future<DigitalTwinState?> build() async {
    final cache = ref.read(localCacheProvider);

    // Cache frais → retour immédiat + refresh background.
    final cached = await cache.get(_cacheKey);
    if (cached != null) {
      Future.microtask(_backgroundRefresh);
      return DigitalTwinState.fromJson(cached);
    }

    return _fetchAndStore();
  }

  Future<DigitalTwinState?> _fetchAndStore() async {
    final client = ref.read(apiClientProvider);
    final cache = ref.read(localCacheProvider);

    try {
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.twinToday,
      );
      final data = responseJson(response);
      await cache.set(_cacheKey, data, ttl: CacheTTL.twinToday);
      return DigitalTwinState.fromJson(data);
    } catch (e) {
      final stale = await cache.get(
        _cacheKey,
        ignoreExpiry: true,
      );
      if (stale != null) return DigitalTwinState.fromJson(stale);
      rethrow;
    }
  }

  Future<void> _backgroundRefresh() async {
    try {
      final fresh = await _fetchAndStore();
      state = AsyncData(fresh);
    } catch (_) {}
  }

  /// Recharge l'état du jumeau depuis l'API.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchAndStore);
  }
}

// ── Provider historique ───────────────────────────────────────────────────────

final twinHistoryProvider =
    AsyncNotifierProvider<TwinHistoryNotifier, DigitalTwinHistory>(
  TwinHistoryNotifier.new,
);

class TwinHistoryNotifier extends AsyncNotifier<DigitalTwinHistory> {
  @override
  Future<DigitalTwinHistory> build() => _fetchHistory();

  Future<DigitalTwinHistory> _fetchHistory({int days = 30}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.twinHistory,
      queryParameters: {'days': days},
    );
    final data = responseJson(response);
    return DigitalTwinHistory.fromJson(data);
  }

  Future<void> refresh({int days = 30}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchHistory(days: days));
  }
}
