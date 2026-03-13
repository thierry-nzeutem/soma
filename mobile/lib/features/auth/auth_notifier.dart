/// AuthNotifier — gestion de l'état d'authentification SOMA (LOT 5).
///
/// Expose [authProvider] qui centralise login / logout / restore session.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/auth/token_storage.dart';
import 'auth_state.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(apiClientProvider));
});

// ── Notifier ──────────────────────────────────────────────────────────────────

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _client;
  final TokenStorage _storage = TokenStorage.instance;

  AuthNotifier(this._client) : super(const AuthStateInitial()) {
    _restoreSession();
  }

  /// Restaure la session depuis SharedPreferences (appelé au démarrage).
  void _restoreSession() {
    if (_storage.isAuthenticated) {
      state = AuthStateAuthenticated(accessToken: _storage.accessToken!);
    } else {
      state = const AuthStateUnauthenticated();
    }
  }

  /// Authentifie l'utilisateur avec email + mot de passe.
  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = const AuthStateLoading();
    try {
      final response = await _client.post(
        ApiConstants.login,
        data: {
          'username': email,   // FastAPI OAuth2 utilise 'username'
          'password': password,
        },
      );
      final data = responseJson(response);
      final accessToken = data['access_token'] as String;
      final refreshToken = data['refresh_token'] as String? ?? '';

      await _storage.setTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
      state = AuthStateAuthenticated(accessToken: accessToken);
    } catch (e) {
      final msg = _parseError(e);
      state = AuthStateError(message: msg);
    }
  }

  /// Déconnecte l'utilisateur et efface les tokens.
  Future<void> logout() async {
    await _storage.clear();
    state = const AuthStateUnauthenticated();
  }

  /// Réinitialise l'état d'erreur pour permettre une nouvelle tentative.
  void clearError() {
    state = const AuthStateUnauthenticated();
  }

  String _parseError(Object e) {
    // DioException retourne parfois le detail du backend
    final str = e.toString();
    if (str.contains('401') || str.contains('Unauthorized')) {
      return 'Email ou mot de passe incorrect.';
    }
    if (str.contains('SocketException') || str.contains('connection')) {
      return 'Impossible de contacter le serveur. Vérifiez votre connexion.';
    }
    return 'Erreur de connexion. Veuillez réessayer.';
  }
}
