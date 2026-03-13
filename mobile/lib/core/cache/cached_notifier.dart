/// CachedAsyncNotifier — Base class pour les notifiers avec cache local.
///
/// Pattern :
///   1. build() retourne immédiatement les données cachées si disponibles
///   2. Déclenche un refresh réseau en arrière-plan
///   3. Si réseau échoue → garde les données cachées (stale)
///   4. refresh() force la recharge réseau
///
/// Usage :
/// ```dart
/// class DashboardNotifier extends CachedAsyncNotifier<DailyMetrics> {
///   @override String get cacheKey => CacheKeys.homeSummary(userId);
///   @override Duration get cacheTTL => CacheTTL.homeSummary;
///   @override DailyMetrics fromJson(json) => DailyMetrics.fromJson(json);
///   @override Map<String, dynamic> toJson(data) => data.toJson();
///   @override Future<DailyMetrics> fetchFromNetwork() async { ... }
/// }
/// ```
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'local_cache.dart';

/// Statut de la source de données.
enum DataSource {
  /// Données chargées depuis le réseau.
  network,

  /// Données chargées depuis le cache local (dans le TTL).
  cache,

  /// Données chargées depuis le cache local (périmé — réseau indisponible).
  stale,
}

/// Enveloppe les données d'un CachedAsyncNotifier.
class CachedData<T> {
  final T data;
  final DataSource source;
  final DateTime? updatedAt;

  const CachedData({
    required this.data,
    required this.source,
    this.updatedAt,
  });

  bool get isFromNetwork => source == DataSource.network;
  bool get isFromCache => source == DataSource.cache;
  bool get isStale => source == DataSource.stale;

  /// Label de fraîcheur, utilisé dans les [CacheBadge].
  String get freshnessLabel {
    if (updatedAt == null) return '';
    final mins = DateTime.now().difference(updatedAt!).inMinutes;
    if (mins < 1) return 'À l\'instant';
    if (mins < 60) return 'il y a $mins min';
    final hrs = mins ~/ 60;
    if (hrs < 24) return 'il y a ${hrs}h';
    return 'il y a ${hrs ~/ 24}j';
  }
}

/// Abstract class — étendre pour un notifier avec cache local.
abstract class CachedAsyncNotifier<T> extends AsyncNotifier<CachedData<T>> {
  // ── À implémenter ──────────────────────────────────────────────────────────

  /// Clé unique de cache pour cet utilisateur / cette donnée.
  String get cacheKey;

  /// Durée de vie des données en cache.
  Duration get cacheTTL;

  /// Désérialise les données depuis le JSON local.
  T fromJson(Map<String, dynamic> json);

  /// Sérialise les données vers le JSON local.
  Map<String, dynamic> toJson(T data);

  /// Charge les données depuis le réseau.
  Future<T> fetchFromNetwork();

  // ── Implémentation ─────────────────────────────────────────────────────────

  @override
  Future<CachedData<T>> build() async {
    final cache = ref.read(localCacheProvider);

    // 1. Essayer le cache frais
    final fresh = await cache.get(cacheKey);
    if (fresh != null) {
      final updatedAt = await cache.updatedAt(cacheKey);
      // Refresh réseau en arrière-plan sans bloquer l'UI
      _backgroundRefresh();
      return CachedData(
        data: fromJson(fresh),
        source: DataSource.cache,
        updatedAt: updatedAt,
      );
    }

    // 2. Pas de cache → charger depuis le réseau
    return await _fetchAndStore();
  }

  /// Recharge depuis le réseau et met à jour le state.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchAndStore);
  }

  // ── Privé ──────────────────────────────────────────────────────────────────

  Future<CachedData<T>> _fetchAndStore() async {
    final cache = ref.read(localCacheProvider);
    try {
      final data = await fetchFromNetwork();
      await cache.set(cacheKey, toJson(data), ttl: cacheTTL);
      return CachedData(
        data: data,
        source: DataSource.network,
        updatedAt: DateTime.now(),
      );
    } catch (e) {
      // Réseau échoué → chercher en cache périmé
      final stale = await cache.get(cacheKey, ignoreExpiry: true);
      if (stale != null) {
        final updatedAt = await cache.updatedAt(cacheKey);
        return CachedData(
          data: fromJson(stale),
          source: DataSource.stale,
          updatedAt: updatedAt,
        );
      }
      rethrow;
    }
  }

  void _backgroundRefresh() {
    Future.microtask(() async {
      try {
        final fresh = await _fetchAndStore();
        // Mettre à jour le state seulement si le notifier est toujours actif
        state = AsyncData(fresh);
      } catch (_) {
        // Ignorer silencieusement — le cache frais est déjà retourné
      }
    });
  }
}
