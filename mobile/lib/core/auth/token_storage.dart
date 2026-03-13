/// Stockage des tokens JWT avec SharedPreferences (LOT 5).
///
/// Persiste les tokens entre les sessions pour éviter de se reconnecter
/// à chaque lancement de l'app.
library;

import 'package:shared_preferences/shared_preferences.dart';

const _kAccessToken = 'soma_access_token';
const _kRefreshToken = 'soma_refresh_token';

/// Singleton pour accès synchrone depuis l'intercepteur Dio.
///
/// Utiliser [TokenStorage.load] au démarrage de l'app pour initialiser
/// les tokens depuis SharedPreferences.
class TokenStorage {
  TokenStorage._();
  static final TokenStorage _instance = TokenStorage._();
  static TokenStorage get instance => _instance;

  String? _accessToken;
  String? _refreshToken;

  // ── Accesseurs synchrones (pour l'intercepteur Dio) ───────────────────────

  String? get accessToken => _accessToken;
  String? get refreshToken => _refreshToken;
  bool get isAuthenticated => _accessToken != null;

  // ── Initialisation depuis SharedPreferences ───────────────────────────────

  /// Charge les tokens persistés depuis SharedPreferences.
  /// À appeler dans `main()` avant `runApp()`.
  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _instance._accessToken = prefs.getString(_kAccessToken);
    _instance._refreshToken = prefs.getString(_kRefreshToken);
  }

  // ── Mutations ─────────────────────────────────────────────────────────────

  Future<void> setTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kAccessToken, accessToken);
    await prefs.setString(_kRefreshToken, refreshToken);
  }

  Future<void> setAccessToken(String token) async {
    _accessToken = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kAccessToken, token);
  }

  Future<void> clear() async {
    _accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kAccessToken);
    await prefs.remove(_kRefreshToken);
  }
}
