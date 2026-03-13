/// ConnectivityService — détection réseau temps réel.
///
/// Expose [connectivityProvider] (Stream-based) et
/// [isOnlineProvider] (bool synchrone).
///
/// Basé sur connectivity_plus. Polling toutes les 5s en fallback.
library;

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ── Provider stream ───────────────────────────────────────────────────────────

/// Stream des changements de connectivité.
final connectivityStreamProvider =
    StreamProvider<List<ConnectivityResult>>((ref) {
  return Connectivity().onConnectivityChanged;
});

// ── Provider bool synchrone ───────────────────────────────────────────────────

/// `true` si le device est connecté à un réseau (wifi ou mobile).
///
/// Se met à jour automatiquement via [connectivityStreamProvider].
final isOnlineProvider = StateNotifierProvider<ConnectivityNotifier, bool>(
  (ref) => ConnectivityNotifier(ref),
);

class ConnectivityNotifier extends StateNotifier<bool> {
  final Ref _ref;

  ConnectivityNotifier(this._ref) : super(true) {
    _init();
  }

  Future<void> _init() async {
    // Vérification initiale
    final results = await Connectivity().checkConnectivity();
    state = _isConnected(results);

    // Écoute des changements
    _ref.listen<AsyncValue<List<ConnectivityResult>>>(
      connectivityStreamProvider,
      (_, next) {
        next.whenData((results) {
          final online = _isConnected(results);
          if (online != state) state = online;
        });
      },
    );
  }

  static bool _isConnected(List<ConnectivityResult> results) {
    return results.any((r) =>
        r == ConnectivityResult.wifi ||
        r == ConnectivityResult.mobile ||
        r == ConnectivityResult.ethernet);
  }
}

// ── Provider type de connexion ────────────────────────────────────────────────

/// Type de connexion actuelle. `null` si offline.
final connectionTypeProvider = Provider<ConnectivityResult?>((ref) {
  final stream = ref.watch(connectivityStreamProvider);
  return stream.when(
    data: (results) {
      if (results.contains(ConnectivityResult.wifi)) {
        return ConnectivityResult.wifi;
      }
      if (results.contains(ConnectivityResult.mobile)) {
        return ConnectivityResult.mobile;
      }
      return null;
    },
    loading: () => null,
    error: (_, __) => null,
  );
});
