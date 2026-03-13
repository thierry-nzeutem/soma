/// Configuration de l'app SOMA par environnement (LOT 5).
///
/// Permet de switcher entre dev/prod sans modifier le code.
/// Définir SOMA_ENV=prod en variable d'environnement pour la production.
library;

enum AppEnvironment { dev, prod }

class AppConfig {
  AppConfig._();

  static final AppConfig _instance = AppConfig._();
  static AppConfig get instance => _instance;

  AppEnvironment _env = AppEnvironment.dev;

  /// Initialise la config selon la variable d'environnement SOMA_ENV.
  static void init({AppEnvironment env = AppEnvironment.dev}) {
    _instance._env = env;
  }

  // ── Environnement ──────────────────────────────────────────────────────────

  bool get isDev => _env == AppEnvironment.dev;
  bool get isProd => _env == AppEnvironment.prod;
  String get envName => _env.name;

  // ── URLs ────────────────────────────────────────────────────────────────────

  /// URL de base du backend selon l'environnement.
  String get baseUrl {
    switch (_env) {
      case AppEnvironment.dev:
        // Émulateur Android : 10.0.2.2 → machine hôte
        return 'http://10.0.2.2:8000';
      case AppEnvironment.prod:
        return 'https://api.soma-health.app';
    }
  }

  // ── Logging ─────────────────────────────────────────────────────────────────

  bool get enableHttpLogs => isDev;
  bool get enableVerboseLogs => isDev;

  // ── Timeouts ────────────────────────────────────────────────────────────────

  Duration get connectTimeout =>
      isDev ? const Duration(seconds: 10) : const Duration(seconds: 15);

  Duration get receiveTimeout =>
      isDev ? const Duration(seconds: 30) : const Duration(seconds: 60);
}
