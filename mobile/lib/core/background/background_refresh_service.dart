/// BackgroundRefreshService — Refresh opportuniste à l'ouverture de l'app.
///
/// Stratégie pragmatique et réaliste :
///   - iOS/Android : pas de background tasks garantis sans plugin dédié
///   - On se concentre sur le refresh au "foreground" (WidgetsBindingObserver)
///   - Min interval : 15 min entre deux refreshs automatiques
///   - Pull-to-refresh manuel disponible sur tous les écrans
///
/// Ce service :
///   1. Écoute le cycle de vie (AppLifecycleState.resumed)
///   2. Si >15 min depuis le dernier refresh → déclenche le refresh
///   3. Expose [shouldRefreshOnOpen] pour les notifiers
///
/// Les notifiers (CachedAsyncNotifier) ne dépendent PAS de ce service —
/// ils ont leur propre logique de cache/refresh. Ce service est une couche
/// d'optimisation supplémentaire.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Intervalle minimum entre deux refreshs auto.
const _kMinRefreshInterval = Duration(minutes: 15);

/// Clé SharedPreferences pour le timestamp du dernier refresh.
const _kLastRefreshKey = 'soma_last_background_refresh';

class BackgroundRefreshService with WidgetsBindingObserver {
  BackgroundRefreshService._();
  static final instance = BackgroundRefreshService._();

  /// Callbacks enregistrés par les écrans/notifiers.
  final _callbacks = <String, VoidCallback>{};

  bool _initialized = false;

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  void initialize() {
    if (_initialized) return;
    _initialized = true;
    WidgetsBinding.instance.addObserver(this);
    debugPrint('[BackgroundRefresh] service initialisé');
  }

  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _callbacks.clear();
    _initialized = false;
  }

  @override
  Future<void> didChangeAppLifecycleState(AppLifecycleState state) async {
    if (state == AppLifecycleState.resumed) {
      final should = await shouldRefreshNow();
      if (should) {
        debugPrint('[BackgroundRefresh] app resumed → refresh déclenché');
        await _triggerRefresh();
        await _updateLastRefreshTimestamp();
      }
    }
  }

  // ── API publique ───────────────────────────────────────────────────────────

  /// Enregistre un callback de refresh pour [id].
  /// Sera appelé lors des refreshs automatiques.
  void register(String id, VoidCallback callback) {
    _callbacks[id] = callback;
  }

  /// Désenregistre un callback.
  void unregister(String id) {
    _callbacks.remove(id);
  }

  /// Vérifie si un refresh automatique est nécessaire.
  Future<bool> shouldRefreshNow() async {
    final prefs = await SharedPreferences.getInstance();
    final lastMs = prefs.getInt(_kLastRefreshKey);
    if (lastMs == null) return true;
    final last = DateTime.fromMillisecondsSinceEpoch(lastMs);
    return DateTime.now().difference(last) >= _kMinRefreshInterval;
  }

  /// Forcer un refresh manuel (pull-to-refresh global).
  Future<void> forceRefresh() async {
    await _triggerRefresh();
    await _updateLastRefreshTimestamp();
  }

  // ── Privé ──────────────────────────────────────────────────────────────────

  Future<void> _triggerRefresh() async {
    for (final cb in _callbacks.values) {
      try {
        cb();
      } catch (e) {
        debugPrint('[BackgroundRefresh] callback error: $e');
      }
    }
  }

  Future<void> _updateLastRefreshTimestamp() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(
      _kLastRefreshKey,
      DateTime.now().millisecondsSinceEpoch,
    );
  }
}
