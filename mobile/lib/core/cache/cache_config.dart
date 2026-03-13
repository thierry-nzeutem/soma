/// Configuration du cache local SOMA — LOT 12.
///
/// Centralise les clés de cache et les durées de vie (TTL).
/// Politique de purge : données expirées supprimées au lancement
/// ou à la demande explicite via [CacheManagementScreen].
library;

/// Durées de vie des caches locaux.
class CacheTTL {
  CacheTTL._();

  /// Home summary + daily metrics — fraîcheur journalière.
  static const homeSummary = Duration(hours: 4);

  /// Plan santé journalier — valide toute la journée.
  static const healthPlan = Duration(hours: 6);

  /// Insights — refresh modéré, changent peu souvent.
  static const insights = Duration(hours: 3);

  /// Twin numérique — calculé chaque matin.
  static const twinToday = Duration(hours: 4);

  /// Âge biologique — change très lentement.
  static const biologicalAge = Duration(hours: 24);

  /// Plan nutritionnel adaptatif — journalier.
  static const adaptiveNutrition = Duration(hours: 6);

  /// Motion summary — hebdomadaire.
  static const motionSummary = Duration(hours: 6);

  /// Score longévité — change lentement.
  static const longevity = Duration(hours: 12);

  /// Briefing matinal — fraîcheur demi-journée (LOT 18).
  static const dailyBriefing = Duration(hours: 4);

  /// Score récupération — journalier.
  static const readiness = Duration(hours: 4);

  /// Résumé nutrition journalier — court (saisies fréquentes).
  static const nutritionSummary = Duration(hours: 1);

  /// Historique hydratation — journalier.
  static const hydrationToday = Duration(hours: 2);

  /// Logs sommeil récents — changent rarement.
  static const sleepLogs = Duration(hours: 6);

  /// Sessions workout récentes — court (séances créées souvent).
  static const workoutSessions = Duration(hours: 2);
}

/// Clés de cache. Toutes préfixées `soma_cache_`.
class CacheKeys {
  CacheKeys._();

  static const _prefix = 'soma_cache_';

  static String homeSummary(int userId) => '${_prefix}home_$userId';
  static String healthPlan(int userId) => '${_prefix}plan_$userId';
  static String insights(int userId) => '${_prefix}insights_$userId';
  static String twinToday(int userId) => '${_prefix}twin_$userId';
  static String biologicalAge(int userId) => '${_prefix}bio_age_$userId';
  static String adaptiveNutrition(int userId) =>
      '${_prefix}adaptive_nutrition_$userId';
  static String motionSummary(int userId) => '${_prefix}motion_$userId';
  static String longevity(int userId) => '${_prefix}longevity_$userId';
  static String readiness(int userId) => '${_prefix}readiness_$userId';
  static String nutritionSummary(int userId) =>
      '${_prefix}nutrition_summary_$userId';
  static String hydrationToday(int userId) =>
      '${_prefix}hydration_$userId';
  static String sleepLogs(int userId) => '${_prefix}sleep_$userId';
  static String workoutSessions(int userId) =>
      '${_prefix}workouts_$userId';

  /// Clé d'expiry pour une donnée.
  static String expiry(String dataKey) => '${dataKey}_expiry';

  /// Clé de timestamp pour une donnée (pour l'affichage "X min ago").
  static String updatedAt(String dataKey) => '${dataKey}_updated_at';

  /// Toutes les clés connues — pour audit cache.
  static const Set<String> allPrefixes = {
    '${_prefix}home_',
    '${_prefix}plan_',
    '${_prefix}insights_',
    '${_prefix}twin_',
    '${_prefix}bio_age_',
    '${_prefix}adaptive_nutrition_',
    '${_prefix}motion_',
    '${_prefix}longevity_',
    '${_prefix}readiness_',
    '${_prefix}nutrition_summary_',
    '${_prefix}hydration_',
    '${_prefix}sleep_',
    '${_prefix}workouts_',
  };
}
