/// Constantes d'API SOMA.
///
/// Centralise tous les endpoints et la configuration réseau.
/// En développement local, utiliser l'IP de la machine hôte (pas localhost)
/// pour accéder au backend FastAPI depuis l'émulateur.
library;

class ApiConstants {
  ApiConstants._();

  // ── Base URL ──────────────────────────────────────────────────────────────
  /// URL de base du backend SOMA.
  /// - Émulateur Android : http://10.0.2.2:8000
  /// - Simulateur iOS    : http://localhost:8000
  /// - Appareil physique : http://<IP_machine>:8000
  static const String baseUrl = 'http://10.0.2.2:8000';

  static const String apiPrefix = '/api/v1';

  // ── Auth ──────────────────────────────────────────────────────────────────
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String refresh = '/auth/refresh';

  // ── Profile ───────────────────────────────────────────────────────────────
  static const String profile = '$apiPrefix/profile';

  // ── Dashboard ─────────────────────────────────────────────────────────────
  static const String dashboardToday = '$apiPrefix/dashboard/today';

  // ── Metrics ───────────────────────────────────────────────────────────────
  static const String metricsDaily = '$apiPrefix/metrics/daily';
  static const String metricsHistory = '$apiPrefix/metrics/history';

  // ── Health Plan ───────────────────────────────────────────────────────────
  static const String healthPlanToday = '$apiPrefix/health/plan/today';

  // ── Scores ────────────────────────────────────────────────────────────────
  static const String readinessToday = '$apiPrefix/scores/readiness/today';
  static const String readinessHistory = '$apiPrefix/scores/readiness/history';
  static const String longevity = '$apiPrefix/scores/longevity';

  // ── Home Summary ──────────────────────────────────────────────────────────
  static const String homeSummary = '$apiPrefix/home/summary';

  // ── Insights ──────────────────────────────────────────────────────────────
  static const String insights = '$apiPrefix/insights';
  static const String insightsRun = '$apiPrefix/insights/run';

  // ── Nutrition ─────────────────────────────────────────────────────────────
  static const String nutritionTargets = '$apiPrefix/nutrition/targets';
  static const String nutritionMicronutrients = '$apiPrefix/nutrition/micronutrients';
  static const String nutritionSupplements =
      '$apiPrefix/nutrition/supplements/recommendations';

  // ── Nutrition CRUD ────────────────────────────────────────────────────────
  static const String foodItems = '$apiPrefix/food-items';
  static const String nutritionEntries = '$apiPrefix/nutrition/entries';
  static const String nutritionDailySummary = '$apiPrefix/nutrition/daily-summary';
  static const String nutritionPhotos = '$apiPrefix/nutrition/photos';

  // ── Workout ───────────────────────────────────────────────────────────────
  static const String sessions = '$apiPrefix/sessions';
  static const String exercises = '$apiPrefix/exercises';

  // ── Hydratation ───────────────────────────────────────────────────────────
  static const String hydrationLog = '$apiPrefix/hydration/log';
  static const String hydrationToday = '$apiPrefix/hydration/today';

  // ── Sommeil ───────────────────────────────────────────────────────────────
  static const String sleepLog = '$apiPrefix/sleep';
  static const String sleepAnalysis = '$apiPrefix/sleep/analysis';

  // ── Corps ─────────────────────────────────────────────────────────────────
  static const String bodyMetrics = '$apiPrefix/body-metrics';

  // ── Computer Vision (LOT 7) ───────────────────────────────────────────────
  static const String visionSessions = '$apiPrefix/vision/sessions';

  // ── Coach IA (LOT 9) ──────────────────────────────────────────────────────
  static const String coachAsk = '$apiPrefix/coach/ask';
  static const String coachThread = '$apiPrefix/coach/thread';
  static const String coachHistory = '$apiPrefix/coach/history';

  // ── Jumeau Numérique (LOT 11) ─────────────────────────────────────────────
  static const String twinToday = '$apiPrefix/twin/today';
  static const String twinHistory = '$apiPrefix/twin/history';
  static const String twinSummary = '$apiPrefix/twin/summary';

  // ── Âge Biologique (LOT 11) ───────────────────────────────────────────────
  static const String biologicalAge = '$apiPrefix/longevity/biological-age';
  static const String biologicalAgeHistory = '$apiPrefix/longevity/history';
  static const String biologicalAgeLevers = '$apiPrefix/longevity/levers';

  // ── Nutrition Adaptative (LOT 11) ─────────────────────────────────────────
  static const String adaptiveNutritionTargets =
      '$apiPrefix/nutrition/adaptive-targets';
  static const String adaptiveNutritionPlan =
      '$apiPrefix/nutrition/adaptive-plan';
  static const String adaptiveNutritionRecompute =
      '$apiPrefix/nutrition/adaptive-plan/recompute';

  // ── Motion Intelligence (LOT 11) ──────────────────────────────────────────
  static const String motionSummary = '$apiPrefix/vision/motion-summary';
  static const String motionHistory = '$apiPrefix/vision/motion-history';
  static const String motionAsymmetryRisk = '$apiPrefix/vision/asymmetry-risk';

  // ── Profil Appris (LOT 13) ────────────────────────────────────────────────
  static const String learningProfile = '$apiPrefix/learning/profile';
  static const String learningRecompute = '$apiPrefix/learning/recompute';
  static const String learningInsights = '$apiPrefix/learning/insights';

  // ── Prédictions Santé V2 (LOT 14) ────────────────────────────────────────
  static const String healthPredictions = '$apiPrefix/health/predictions';
  static const String injuryRiskPrediction = '$apiPrefix/health/injury-risk';
  static const String overtrainingPrediction = '$apiPrefix/health/overtraining';
  static const String weightPrediction = '$apiPrefix/health/weight-prediction';

  // ── Risque Blessure Avancé (LOT 15) ──────────────────────────────────────
  static const String injuryRisk = '$apiPrefix/injury/risk';
  static const String injuryRiskHistory = '$apiPrefix/injury/risk/history';
  static const String injuryRiskZones = '$apiPrefix/injury/zones';

  // ── Biomarqueurs (LOT 16) ─────────────────────────────────────────────────
  static const String labsAnalysis = '$apiPrefix/labs/analysis';
  static const String labsResult = '$apiPrefix/labs/result';
  static const String labsHistory = '$apiPrefix/labs/history';
  static const String labsMarkers = '$apiPrefix/labs/markers';

  // ── Daily Briefing (LOT 18) ───────────────────────────────────────────────
  static const String dailyBriefing = '$apiPrefix/daily/briefing';
  static const String profileOnboarding = '$apiPrefix/profile/onboarding';
  static const String coachQuickAdvice = '$apiPrefix/coach/quick-advice';
  static const String analyticsEvent = '$apiPrefix/analytics/event';

  // ── Coach Platform (LOT 17) ───────────────────────────────────────────────
  static const String coachDashboard = '$apiPrefix/coach-platform/dashboard';
  static const String coachProfile = '$apiPrefix/coach-platform/coach/profile';
  static const String coachAthletes = '$apiPrefix/coach-platform/athletes';
  static const String coachPrograms = '$apiPrefix/coach-platform/programs';
  static const String coachNotes = '$apiPrefix/coach-platform/notes';
  static const String coachAlerts = '$apiPrefix/coach-platform/alerts';
  static const String labsResults = '$apiPrefix/labs/results';
  static const String labsLongevityImpact = '$apiPrefix/labs/longevity-impact';

  // ── Analytics Dashboard (LOT 19) ──────────────────────────────────────────
  static const String analyticsSummary = '$apiPrefix/analytics/summary';
  static const String analyticsEvents = '$apiPrefix/analytics/events';
  static const String analyticsFunnelOnboarding = '$apiPrefix/analytics/funnel/onboarding';
  static const String analyticsRetentionCohorts = '$apiPrefix/analytics/retention/cohorts';
  static const String analyticsFeatures = '$apiPrefix/analytics/features';
  static const String analyticsCoach = '$apiPrefix/analytics/coach';
  static const String analyticsPerformance = '$apiPrefix/analytics/performance';


  // Body Composition Enriched (Withings-inspired)
  static const String bodyCompositionTrend = '$apiPrefix/body/composition/trend';
  static const String bodyCompositionAllData = '$apiPrefix/body/composition/all-data';
  static const String bodyWeightTrend = '$apiPrefix/body/weight/trend';

  // Cardio Fitness (VO2max)
  static const String cardioFitness = '$apiPrefix/fitness/cardio-fitness';
  static const String cardioFitnessHistory = '$apiPrefix/fitness/cardio-fitness/history';

  // Activity Analytics
  static const String activityDay = '$apiPrefix/activity/day';
  static const String activityPeriod = '$apiPrefix/activity/period';

  // Heart Rate Analytics
  static const String hrAnalytics = '$apiPrefix/heart-rate/analytics';
  static const String hrTimeline = '$apiPrefix/heart-rate/timeline';
  static const String hrAllData = '$apiPrefix/heart-rate/all-data';

  // Sleep Quality Score
  static const String sleepQualityScore = '$apiPrefix/sleep/quality-score';

  // Health Report PDF
  static const String healthReport = '$apiPrefix/reports/health';

  // ── HRV & Stress (V2) ─────────────────────────────────────────────────────
  static const String hrvScore = '$apiPrefix/hrv/score';
  static const String hrvHistory = '$apiPrefix/hrv/history';

  // ── Gamification (V2) ─────────────────────────────────────────────────────
  static const String gamificationStreaks = '$apiPrefix/gamification/streaks';
  static const String gamificationAchievements = '$apiPrefix/gamification/achievements';
  static const String gamificationProfile = '$apiPrefix/gamification/profile';

  // ── Cycle Menstruel (V2) ──────────────────────────────────────────────────
  static const String cycleEntry = '$apiPrefix/cycle/entry';
  static const String cycleEntries = '$apiPrefix/cycle/entries';
  static const String cycleSummary = '$apiPrefix/cycle/summary';

  // ── Subscription & Entitlements (V2) ──────────────────────────────────────
  static const String meEntitlements = '$apiPrefix/me/entitlements';

  // Stripe billing (Android + Web ONLY — guarded by BillingContext.canShowCheckout).
  // iOS clients calling these receive HTTP 451 from the backend.
  static const String billingCheckout = '$apiPrefix/billing/checkout';
  static const String billingPortal = '$apiPrefix/billing/portal';

  // Apple IAP billing (iOS ONLY — backend rejects non-iOS clients with HTTP 403).
  static const String appleVerify = '$apiPrefix/billing/apple/verify';
  static const String appleRestore = '$apiPrefix/billing/apple/restore';

  // ── Timeouts ──────────────────────────────────────────────────────────────
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 15);
}
