# SOMA — Changelog

## [1.9.0] — 2026-03-08 — LOT 19 : Product Validation, Retention & Internal Analytics

### Créé — Backend Infrastructure Monitoring
- `app/models/api_metrics.py` — `ApiMetricDB` (endpoint, method, response_time_ms, status_code, created_at + 4 index)
- `app/db/migrations/versions/V010_api_metrics.py` — Migration V010 : table `api_metrics` + index composites, `down_revision = "V009"`
- `app/middleware/__init__.py` + `app/middleware/metrics_middleware.py` — `MetricsMiddleware` buffer deque 10 000 entrées, `MetricRecord`, `get_buffered_metrics()`

### Créé — Backend Analytics Dashboard Service + Endpoints
- `app/services/analytics_dashboard_service.py` — 7 fonctions async : get_summary, get_events, get_funnel_onboarding, get_cohort_retention, get_feature_usage, get_coach_analytics, get_performance_stats. 8 dataclasses + helpers `_has_event_in_window()` (D1/D7/D30)
- `app/schemas/analytics_dashboard.py` — 8 schémas Pydantic v2 réponses analytics
- `app/api/v1/endpoints/analytics_dashboard.py` — 7 endpoints GET `/analytics/*` (summary, events, funnel/onboarding, retention/cohorts, features, coach, performance)

### Modifié — Backend Router + App
- `app/api/v1/router.py` — + `analytics_dashboard_router`
- `app/main.py` — + `MetricsMiddleware` (fire-and-forget, non bloquant)

### Créé — Tests Backend (58 nouveaux tests purs)
- `tests/test_analytics_summary.py` — 15 tests (AnalyticsSummary dataclass, ratio DAU/MAU, onboarding rate, schema Pydantic)
- `tests/test_analytics_retention.py` — 18 tests (`_has_event_in_window` D1/D7/D30, CohortRetention, CohortRetentionResponse)
- `tests/test_analytics_funnels.py` — 13 tests (_FUNNEL_STEPS ordre, calcul conversion/drop-off, div/0 sûre, schemas Pydantic)
- `tests/test_feature_usage.py` — 12 tests (FeatureUsage, CoachAnalytics, EventCount, `get_performance_stats()` mock buffer, ApiMetricDB)

### Modifié — Flutter Tracking & Navigation
- `lib/core/analytics/analytics_service.dart` — +6 events LOT 19 : briefingOpened, briefingCardView, briefingCtaClick, journalOpen, journalActionSubmitted, journalActionCancelled
- `lib/features/briefing/morning_briefing_screen.dart` — tracking `briefing_opened` (postFrameCallback) + `briefing_cta_click` sur CTAs ; `_BottomCTAs` → ConsumerWidget
- `lib/features/quick_journal/quick_journal_screen.dart` — tracking `journal_open` dans chaque `_showXXXSheet`
- `lib/core/api/api_constants.dart` — +7 endpoints analytics dashboard
- `lib/main.dart` — +1 route `/admin/analytics`

### Créé — Flutter Admin Dashboard Screen
- `lib/features/admin/analytics_dashboard_screen.dart` — `AnalyticsDashboardScreen` : 6 FutureProvider.autoDispose, 6 sections (Summary, FeatureUsage, Funnel, Retention, Coach, Performance), RefreshIndicator, color-coding vert/orange/rouge

---

## [1.8.0] — 2026-03-08 — LOT 18 : Productization & Daily Experience Engine

### Créé — Backend Analytics
- `app/models/analytics.py` — `AnalyticsEventDB` (user_id, event_name, properties JSONB, created_at + 4 index)
- `app/core/analytics/__init__.py` + `app/core/analytics/tracker.py` — `track_event()` fire-and-forget, 9 events constants
- `app/db/migrations/versions/V009_analytics_events.py` — Migration V009 : table `analytics_events` + 4 index
- `app/api/v1/endpoints/analytics_events.py` — `POST /analytics/event` (201, TrackEventRequest → TrackEventResponse)

### Créé — Backend Daily Briefing
- `app/services/daily_briefing_service.py` — `compute_daily_briefing()` agrégateur 5 sources DB. `DailyBriefing` dataclass 19 champs. `_readiness_level/color()`, `_extract_coach_tip()`
- `app/schemas/briefing.py` — `DailyBriefingResponse` Pydantic v2
- `app/api/v1/endpoints/daily.py` — `GET /daily/briefing`

### Créé — Backend Onboarding
- `app/schemas/onboarding.py` — `OnboardingRequest` (12 champs), `OnboardingInitialTargets`, `OnboardingResponse`
- `app/api/v1/endpoints/onboarding.py` — `POST /profile/onboarding` idempotent : PATCH profil + POST BodyMetric + calculs BMR/TDEE + analytics + message bienvenue

### Modifié — Backend Coach IA
- `app/schemas/coach.py` — + `QuickAdviceRequest`, `QuickAdviceResponse`
- `app/api/v1/endpoints/coach.py` — + `POST /coach/quick-advice` (no DB persistence)
- `app/services/context_builder.py` — `_MAX_CONTEXT_CHARS` 5 500 → 6 000, + `twin_key_signals` section
- `app/api/v1/router.py` — + `daily_router`, `onboarding_router`, `analytics_router`

### Créé — Tests Backend (102 nouveaux)
- `tests/test_analytics.py` — 21 tests
- `tests/test_onboarding.py` — 26 tests
- `tests/test_daily_briefing.py` — 33 tests
- `tests/test_coach_quick_advice.py` — 22 tests

### Créé — Flutter Widgets Partagés (5)
- `ReadinessGauge` — Arc 240° CustomPainter couleur dynamique
- `HealthScoreRing` — Anneau 360° couleur dynamique
- `InsightCard` — Sévérité + catégorie chip + border-left
- `CoachTipCard` — Icon robot SOMA + CTA optionnel
- `AlertBanner` + `DismissibleAlertBanner` — Dismissible animée

### Créé — Flutter Onboarding Flow
- `lib/core/models/onboarding.dart` — `OnboardingData`, `OnboardingInitialTargets`, `OnboardingResult`
- `lib/features/onboarding/onboarding_notifier.dart` — `OnboardingNotifier extends StateNotifier`
- `lib/features/onboarding/onboarding_screen.dart` — PageView 7 pages (Welcome → Summary)

### Créé — Flutter Morning Briefing
- `lib/core/models/daily_briefing.dart` — `DailyBriefing` @immutable 19 champs + helpers
- `lib/features/briefing/briefing_notifier.dart` — `BriefingNotifier` AsyncNotifier, cache 4h
- `lib/features/briefing/morning_briefing_screen.dart` — ReadinessGauge + 5 cartes + alertes + insights

### Créé — Flutter Quick Journal
- `lib/features/quick_journal/quick_journal_screen.dart` — Grille 5 actions + ModalBottomSheet par action (<10s)

### Créé — Flutter Analytics
- `lib/core/analytics/analytics_service.dart` — `AnalyticsEvents` (9 constantes) + `AnalyticsService.track()` fire-and-forget

### Modifié — Flutter Navigation & Config
- `lib/core/api/api_constants.dart` — +4 endpoints LOT 18
- `lib/core/cache/cache_config.dart` — + `CacheTTL.dailyBriefing = Duration(hours: 4)`
- `lib/main.dart` — +3 routes (`/onboarding`, `/briefing`, `/quick-journal`)
- `lib/features/dashboard/dashboard_screen.dart` — +`_BriefingCTA` + `_QuickJournalCTA`
- `lib/core/notifications/notification_scheduler.dart` — payload briefing → `/briefing`

---

## [1.5.0] — 2026-03-08 — LOT 17 : Product Consolidation & End-to-End Reliability

### Créé — Persistence PostgreSQL (suppression stores in-memory)

**Backend — DB Models :**
- `app/domains/coach_platform/models.py` — 6 modèles SQLAlchemy : `CoachProfileDB`, `AthleteProfileDB`, `CoachAthleteLinkDB`, `TrainingProgramDB`, `AthleteNoteDB`, `AthleteAlertDB` (UUIDMixin + TimestampMixin + JSONB + UniqueConstraints)
- `app/domains/biomarkers/models.py` — `LabResultDB` (user_id, marker_name, value, unit, test_date, notes + index composite user_date)
- `app/db/migrations/versions/V008_coach_platform_biomarkers.py` — Migration V008 : 7 tables créées, `down_revision = "V007"`, index composites sur (coach_id, athlete_id) et (user_id, test_date)

**Backend — Refactoring endpoints :**
- `app/domains/coach_platform/endpoints.py` — Suppression de 5 stores in-memory (`_coach_profiles`, `_athletes`, `_links`, `_programs`, `_notes`) → AsyncSession + `select()` + `db.add()` + `db.commit()`. Ajout `GET /coach-platform/dashboard` agrégateur.
- `app/domains/biomarkers/endpoints.py` — Suppression `_lab_store` → AsyncSession + `LabResultDB`. Cache invalidation sur POST /labs/result.

### Créé — Module d'Explainabilité Transverse

- `app/core/explainability/__init__.py` — Package marker + re-exports
- `app/core/explainability/labels.py` — `risk_label()` (5 niveaux), `trend_label()`, `day_type_label()`, `biomarker_status_label()` (11 statuts), `risk_level_label()` — labels French purs
- `app/core/explainability/confidence.py` — `confidence_tier()` (high/medium/low seuils 0.7/0.4), `confidence_tier_label()`, `format_confidence()` ("73% (élevée)")
- `app/core/explainability/severity.py` — `SEVERITY_COLORS`, `SEVERITY_ICONS`, `severity_color()`, `severity_icon()`, `alert_severity()` — mapping alertes → sévérités

### Créé — Tests E2E Integration (5 fichiers)

- `tests/integration/test_e2e_coach_athlete.py` — Coach registration + training programs + notes/alerts
- `tests/integration/test_e2e_biomarker_longevity.py` — Lab result model + biomarker analysis pipeline + longevity modifier
- `tests/integration/test_e2e_learning_injury.py` — Learning profile service + injury prevention ACWR monotonicity
- `tests/integration/test_e2e_full_context.py` — CoachContext ≤5500 chars (all fields / minimal / adversarial)
- `tests/integration/test_e2e_coach_platform_persistence.py` — Model independence, absence forbidden in-memory patterns, V008 migration existence

### Créé — Tests unitaires explainabilité

- `tests/test_explainability.py` — ~20 tests : TestRiskLabel (5), TestTrendLabel (4), TestDayTypeLabel (2), TestBiomarkerStatusLabel (1), TestRiskLevelLabel (1), TestConfidenceTier (3), TestFormatConfidence (5), TestSeverityColor (4), TestSeverityIcon (4), TestAlertSeverity (5), TestSeverityConstants (2)

### Créé — Flutter Coach Platform

- `lib/core/models/coach_platform.dart` — 8 classes Dart immutables avec `fromJson`/`toJson` : `CoachProfile`, `CoachProfileCreate`, `AthleteProfile`, `AthleteCreate`, `AthleteDashboardSummary`, `CoachAthletesOverview`, `TrainingProgram`, `AthleteNote`, `AthleteNoteCreate`, `AthleteAlert`
- `lib/features/coach_platform/coach_platform_notifier.dart` — `CoachDashboardNotifier` (AsyncNotifier), `CoachProfileNotifier`, `AthleteAlertsNotifier` (family), `AthleteNotesNotifier` (family)
- `lib/features/coach_platform/coach_dashboard_screen.dart` — Dashboard coach : stats globales + alertes actives + liste athlètes triée par risque + FAB ajout athlète + onboarding (no profile)
- `lib/features/coach_platform/athlete_detail_screen.dart` — Détail athlète : header + grille scores + alertes + notes coach (+ dialog ajout note)

### Créé — Flutter Biomarkers Screens

- `lib/features/biomarkers/biomarker_analysis_screen.dart` — Analyse : confiance + 3 scores de santé (barres) + LongevityImpactCard + actions prioritaires + BiomarkerMarkerRow × N + recommandations
- `lib/features/biomarkers/biomarker_results_screen.dart` — Liste résultats groupés par date + BottomSheet ajout résultat (14 marqueurs dropdown + valeur + unité + date)

### Créé — Widgets partagés Flutter

- `lib/shared/widgets/risk_level_badge.dart` — Badge coloré green/yellow/orange/red avec icône + label French
- `lib/shared/widgets/athlete_alert_card.dart` — Carte alerte : bordure gauche colorée + severity badge + message + chevron optionnel
- `lib/shared/widgets/biomarker_marker_row.dart` — Ligne biomarqueur : nom + valeur + score + barre + StatusBadge + interprétation
- `lib/shared/widgets/longevity_impact_card.dart` — Card longévité : ±N ans + % optimal + trending icon + stats marqueurs
- `lib/shared/widgets/confidence_badge.dart` — Badge confiance : ≥70% élevée (vert) / ≥40% moyenne (jaune) / <40% faible (gris)

### Modifié — Navigation Flutter (CTAs)

- `lib/main.dart` — +4 routes : `/coach-platform`, `/coach-platform/athlete/:id`, `/biomarkers`, `/biomarkers/results` + imports LOT 17
- `lib/core/api/api_constants.dart` — +8 endpoints : `coachDashboard`, `coachProfile`, `coachAthletes`, `coachPrograms`, `coachNotes`, `coachAlerts`, `labsResults`, `labsLongevityImpact`
- `lib/features/dashboard/dashboard_screen.dart` — `_QuickAccessRow` : 2 CTAs "Coach" et "Biomarqueurs" sous les métriques
- `lib/features/profile/profile_screen.dart` — +2 entrées rapides : Biomarqueurs + Coach Platform
- `lib/features/journal/journal_hub_screen.dart` — +1 card "Biomarqueurs" dans section "Santé avancée"
- `lib/features/biological_age/biological_age_screen.dart` — CTA Biomarqueurs avec lien explicite vers `/biomarkers`

---

## [1.4.0] — 2026-03-08 — LOT 13–16 : Personalized Intelligence + Coach Platform + Injury Prevention + Longevity Lab

### Créé — LOT 13 : Personalized Learning Engine

**Backend — `app/domains/learning/` (4 fichiers) :**
- `service.py` — `UserLearningResult` dataclass + 7 fonctions pures : `_estimate_true_tdee()` (bilan énergétique réel = calories_moy - déficit_pondéral×7700), `_compute_metabolic_efficiency()` (ratio TDEE_réel/Mifflin), `_analyze_recovery_profile()`, `_analyze_training_tolerance()`, `_analyze_nutrition_response()`, `_analyze_sleep_recovery()`, `_generate_insights()`. Constantes : `KCAL_PER_KG_FAT = 7700`, `MIN_DAYS_FOR_TDEE = 14`.
- `schemas.py` — `UserLearningProfileResponse`, `LearningInsightResponse`, `LearningInsightsResponse`, `LearningRecomputeResponse`.
- `endpoints.py` — `GET /learning/profile`, `GET /learning/insights`, `POST /learning/recompute`. Helper `_load_learning_inputs()` lit DailyMetrics, ReadinessScore, WorkoutSession, FoodEntry (90j).
- `__init__.py` — Package marker.

### Créé — LOT 14 : Coach Pro / Multi-Athletes Platform

**Backend — `app/domains/coach_platform/` (4 fichiers) :**
- `service.py` — 9 dataclasses : `CoachProfile`, `AthleteProfile`, `CoachAthleteLink`, `AthleteDashboardSummary`, `TrainingProgram`, `ProgramWeek`, `ProgramWorkout`, `AthleteNote`, `AthleteAlert`. Fonctions pures : `_determine_risk_level()` (green/yellow/orange/red), `_generate_athlete_alerts()` (5 types), `compute_athlete_dashboard_summary()`. Stores in-memory : `_coach_profiles`, `_athletes`, `_links`, `_programs`, `_notes`.
- `schemas.py` — 13 schémas Pydantic v2.
- `endpoints.py` — 9 endpoints : `POST /coach-platform/coach/register`, `GET /coach-platform/coach/profile`, `GET /coach-platform/athletes`, `POST /coach-platform/athletes`, `GET /coach-platform/athlete/{id}/dashboard`, `POST /coach-platform/programs`, `GET /coach-platform/programs`, `POST /coach-platform/notes`, `GET /coach-platform/athlete/{id}/notes`.
- `__init__.py` — Package marker.

### Créé — LOT 15 : Injury Prevention Engine

**Backend — `app/domains/injury/` (4 fichiers) :**
- `service.py` — `InjuryPreventionResult` + `RiskZone` dataclasses. Pondération : ACWR 30%, Fatigue 25%, Asymétrie 20%, Sommeil 15%, Monotonie 10%. Fonctions pures : `_score_acwr_risk()`, `_score_fatigue_risk()`, `_score_asymmetry_risk()`, `_score_sleep_risk()`, `_score_monotony_risk()` (Foster 1998 : moy/std), `_determine_risk_category()` (minimal/low/moderate/high/critical), `_identify_risk_zones()`, `_detect_compensation_patterns()`, `_generate_recommendations()`. Constantes ACWR : CRITICAL=1.8, HIGH=1.5, MODERATE=1.3.
- `schemas.py` — 5 schémas : `RiskZoneResponse`, `InjuryRiskResponse`, `InjuryHistoryItem`, `InjuryHistoryResponse`, `InjuryRecommendationsResponse`.
- `endpoints.py` — `GET /injury/risk` (cache 4h), `GET /injury/history`, `GET /injury/recommendations`. Helper `_load_injury_inputs()` lit DailyMetrics, ReadinessScore, WorkoutSession, MotionIntelligenceSnapshot, DigitalTwinSnapshot.
- `__init__.py` — Package marker.

### Créé — LOT 16 : Longevity Lab Biomarkers

**Backend — `app/domains/biomarkers/` (4 fichiers) :**
- `service.py` — `REFERENCE_RANGES` pour 14 biomarqueurs (vitamin_d, ferritin, crp, testosterone_total, hba1c, fasting_glucose, cholesterol_total, hdl, ldl, triglycerides, cortisol, homocysteine, magnesium, omega3_index). `BiomarkerResult` + `BiomarkerAnalysis` + `BiomarkerAnalysisResult` dataclasses. Scores : `metabolic_health_score`, `inflammation_score`, `cardiovascular_risk`, `longevity_modifier` (= `(75 - longevity_score) × 0.2`, clampé ±10 ans). Store in-memory `_lab_store: dict[str, list[dict]]`.
- `schemas.py` — 7 schémas incluant `LabResultCreate`, `BiomarkerDetailedResponse`, `LongevityImpactResponse`.
- `endpoints.py` — `POST /labs/result`, `GET /labs/results`, `GET /labs/analysis` (cache 24h), `GET /labs/longevity-impact`.
- `__init__.py` — Package marker.

### Modifié — Intégration globale

- `app/api/v1/router.py` — +4 routers enregistrés (learning, injury, biomarkers, coach_platform).
- `app/services/context_builder.py` — +4 champs `CoachContext` (learning_summary, injury_risk_summary, biomarker_summary, athlete_context), +4 sections `to_prompt_text()`, +3 blocs de chargement dans `build_coach_context()` (LOT 13, 15, 16).

### Créé — Flutter Mobile (LOT 13–16)

**Modèles Dart :**
- `lib/core/models/learning_profile.dart` — `LearningProfile` + `LearningInsight`, getters `isFastMetabolizer`, `metabolicEfficiencyLabel`, `recoveryProfileLabel`.
- `lib/core/models/injury_risk.dart` — `RiskZone` + `InjuryRisk`, labels français, `isHighRisk`, `categoryLabel`.
- `lib/core/models/biomarker.dart` — `BiomarkerMarker` + `BiomarkerAnalysis` + `LabResultCreate`, switch 14 marqueurs.

**Notifiers Riverpod :**
- `lib/features/learning/learning_notifier.dart` — `LearningProfileNotifier` (AsyncNotifier), méthode `recompute()`.
- `lib/features/injury/injury_notifier.dart` — `InjuryRiskNotifier` (AsyncNotifier), méthode `refresh()`.
- `lib/features/biomarkers/biomarker_notifier.dart` — `BiomarkerAnalysisNotifier`, méthode `addLabResult()`.

**Écrans :**
- `lib/features/learning/learning_profile_screen.dart` — Bandeau confiance, cartes métabolisme/récupération/tolérance/réponse nutritionnelle, cartes insights. Guard `EmptyState.insufficientData()`.
- `lib/features/injury/injury_risk_screen.dart` — Anneau score, alertes actions immédiates (rouge), 5 barres composantes, zones à risque, recommandations.

**Navigation :**
- `lib/main.dart` — +2 routes : `/learning` → `LearningProfileScreen`, `/injury` → `InjuryRiskScreen`.
- `lib/core/api/api_constants.dart` — +12 endpoints LOT 13–16.

### Tests backend LOT 13–16 (~110 nouveaux tests)
- `tests/test_learning_engine.py` — ~30 tests (7 classes : TrueTdee, MetabolicEfficiency, RecoveryProfile, TrainingTolerance, NutritionResponse, SleepRecovery, LearningProfile).
- `tests/test_injury_prevention.py` — ~35 tests (7 classes : ScoreAcwr, ScoreFatigue, ScoreAsymmetry, ScoreSleep, ScoreMonotony, RiskCategory, InjuryAnalysis).
- `tests/test_coach_platform.py` — ~20 tests (3 classes : RiskLevel, AthleteAlerts, AthleteDashboard).
- `tests/test_biomarker_analysis.py` — ~25 tests (3 classes : SingleMarker, CompositeScores, BiomarkerAnalysis).

---

## [1.3.0] — 2026-03-08 — LOT 12 : Mobile Reliability & Daily Usage Excellence

### Créé — Infrastructure Mobile (15 fichiers)

**Cache local (SharedPreferences + TTL) :**
- `lib/core/cache/cache_config.dart` — `CacheTTL` (homeSummary 4h, healthPlan 6h, twinToday 4h, biologicalAge 24h, insights 3h, motion/nutrition 6h) + `CacheKeys` builders.
- `lib/core/cache/local_cache.dart` — `LocalCache` : set/get/has/hasStale/remove/purgeExpired/purgeAll/estimatedSizeBytes/activeEntryCount. Stockage JSON avec clés `_expiry` + `_updated_at`.
- `lib/core/cache/cached_notifier.dart` — `CachedAsyncNotifier<T>` abstrait + `CachedData<T>` (source: network/cache/stale) + `DataSource` enum.

**Connectivité & Sync différée :**
- `lib/core/offline/connectivity_service.dart` — `ConnectivityService` (connectivity_plus), `isOnlineProvider` (StateNotifier), `connectivityStreamProvider`.
- `lib/core/sync/sync_models.dart` — `SyncAction` (9 types), `SyncStatus` (pending/syncing/synced/failed), `SyncResult`.
- `lib/core/sync/sync_queue.dart` — `SyncQueue` SharedPreferences JSON array, idempotent enqueue.
- `lib/core/sync/sync_manager.dart` — `SyncManager` (processPending + _executeAction), `SyncStatusNotifier`, reconnection auto-trigger.
- `lib/core/background/background_refresh_service.dart` — `BackgroundRefreshService` singleton (WidgetsBindingObserver), TTL 15min, register/unregister pattern.

**Notifications intelligentes :**
- `lib/core/notifications/notification_models.dart` — `NotificationCategory` (6 cats), `NotificationPreference`, `NotificationIds`, `NotificationChannels`.
- `lib/core/notifications/notification_service.dart` — `NotificationService` singleton (flutter_local_notifications), show/scheduleDaily/cancel/requestPermissions. `NotificationPreferencesNotifier`.
- `lib/core/notifications/notification_scheduler.dart` — `NotificationScheduler` : briefing 7h30, hydration 15h00, sleep 22h00, recovery alerts, safety alerts, sync complete.

**Widgets partagés LOT 12 :**
- `lib/shared/widgets/offline_banner.dart` — `OfflineBanner`, `OfflineBannerWrapper`, `OfflineChip`.
- `lib/shared/widgets/cache_badge.dart` — `CacheBadge` (source + age), `WithCacheBadge`.
- `lib/shared/widgets/empty_state.dart` — `EmptyState` + constructeurs nommés (noNutritionData, noWorkouts, noVisionData, noHistory, noInsights, insufficientData).
- `lib/shared/widgets/error_state.dart` — `ErrorState` + constructeurs (loading, offline, server, timeout) + `InlineErrorWidget`.

### Modifié — Notifiers (cache offline-first)
- `dashboard_notifier.dart` — Cache 4h + stale fallback si offline.
- `health_plan_notifier.dart` — Cache 6h + stale fallback.
- `insights_notifier.dart` — Cache 3h + stale fallback.
- `twin_notifier.dart` — Cache 4h + stale fallback.

### Créé — Settings Control Center (2 fichiers)
- `lib/features/settings/notification_preferences_screen.dart` — Config notifications par catégorie + sélecteur heure + test envoi.
- `lib/features/settings/cache_management_screen.dart` — Stats cache (entries/taille), purge sélective, file sync, sync manuelle.

### Modifié — Navigation
- `lib/main.dart` — +2 routes `/settings/notifications` + `/settings/cache`. Init `NotificationService` + `BackgroundRefreshService` au démarrage.
- `lib/features/settings/settings_screen.dart` — Section Fiabilité & Données avec liens Control Center + badge sync en attente.

### Ajouté — Dépendances (pubspec.yaml)
- `connectivity_plus: ^6.0.2`
- `flutter_local_notifications: ^17.2.2`

### Tests Dart LOT 12 (~55 nouveaux tests)
- `test/core/local_cache_test.dart` — ~20 tests (set/get/TTL/stale/purge/size).
- `test/core/sync_queue_test.dart` — ~20 tests (enqueue/idempotence/pending/update/remove/purge).
- `test/core/notification_models_test.dart` — ~10 tests (categories/preferences/serialization).
- `test/core/cache_config_test.dart` — ~10 tests (TTL constants/key builders).

---

## [1.2.0] — 2026-03-08 — LOT 11 : Advanced Intelligence + Scale-Ready Architecture

### Créé — Infrastructure Backend

- **`app/cache/`** — `CacheService` Redis async avec graceful degradation, `CacheKeys` TTLs (Twin 4h, Bio Age 24h, Nutrition/Motion 6h).
- **`app/events/`** — `EventBus` asyncio in-process (subscribe/publish/dispatch), 9 types d'événements (`SomaEvent`, `MealLogged`, `WorkoutCompleted`, `SleepLogged`, `VisionSessionSaved`, `MetricsComputed`, `ReadinessUpdated`, `MetabolicStateUpdated`, `DigitalTwinComputed`, `BiologicalAgeUpdated`).
- **`app/storage/`** — `StorageService` abstrait + `LocalStorage` impl. Interface S3-ready pour LOT 12.
- **`app/observability/logging_config.py`** — `setup_logging()` : DevFormatter coloré + JsonFormatter JSON structuré avec `request_id`.

### Créé — DB

- **`app/models/advanced.py`** — `DigitalTwinSnapshot`, `BiologicalAgeSnapshot`, `MotionIntelligenceSnapshot` (SQLAlchemy, JSONB components).
- **`app/db/migrations/versions/V007_advanced_health_engines.py`** — 3 nouvelles tables + index composites (`vision_sessions`, `daily_metrics`, `conversation_messages`).

### Créé — Domaines Backend (12 fichiers)

- **`app/domains/twin/`** — `service.py` : `compute_digital_twin_state()` + 12 fonctions pures (energy_balance, glycogen, carb_availability, protein_status, hydration, fatigue, sleep_debt, inflammation, recovery_capacity, training_readiness, stress_load, metabolic_flexibility). `TwinComponent` : value, status, confidence, explanation, variables_used (explainabilité totale). `schemas.py`, `endpoints.py` (GET /twin/today, /twin/history, /twin/summary).
- **`app/domains/biological_age/`** — `service.py` : `compute_biological_age()` sur 7 composantes pondérées (cardiovascular 20%, metabolic 20%, body_composition 15%, sleep 15%, activity 15%, recovery 10%, consistency 5%). Formule : `bio_age = chrono + Σ(weight × (75 - score) × 0.2)`, clampé ±15 ans. 7 `BiologicalAgeLever` sélectionnés si score < 65. `schemas.py`, `endpoints.py` (GET /longevity/biological-age, /longevity/history, /longevity/levers).
- **`app/domains/adaptive_nutrition/`** — `service.py` : `compute_adaptive_plan()` stateless. `DayType` enum (REST/TRAINING/INTENSE_TRAINING/RECOVERY/DELOAD). Règles protéines (1.6–2.2 g/kg) et glucides (2.5–5.5 g/kg) par type de journée. `schemas.py`, `endpoints.py` (GET /nutrition/adaptive-targets, /nutrition/adaptive-plan, POST /recompute).
- **`app/domains/motion/`** — `service.py` : `compute_motion_intelligence()`. `_trend()` regression linéaire. `asymmetry_score = min(100, mean([std_stability, std_amplitude]) × 3)`. `movement_health = 0.4×stability + 0.4×mobility + 0.2×(100-asymmetry)`. Profils par exercice. `schemas.py`, `endpoints.py` (GET /vision/motion-summary, /motion-history, /asymmetry-risk).

### Modifié — Backend

- **`app/api/v1/router.py`** — +4 routers de domaine (twin, bio_age, adaptive_nutrition, motion).
- **`app/main.py`** — Intégration `setup_logging()` + `init_cache()`/`close_cache()` dans lifespan.
- **`app/services/scheduler_service.py`** — +4 steps (6: digital_twin, 7: bio_age, 8: motion_intelligence, 9: adaptive_nutrition_log). Pipeline 5→9 étapes.
- **`app/services/context_builder.py`** — +4 sections coach (Jumeau Numérique, Âge Biologique, Nutrition Adaptative, Mouvement). Limite ≤5500 chars maintenue.

### Créé — Tests Backend (~200 nouveaux tests)

- **`tests/test_digital_twin_service.py`** — ~50 tests purs (TwinComponent, 12 fonctions _score_*, compute_digital_twin_state, build_twin_summary).
- **`tests/test_biological_age_service.py`** — ~40 tests purs (composantes, levers, delta, clamping, trend).
- **`tests/test_adaptive_nutrition_engine.py`** — ~50 tests purs (day_type, chaque règle macro, fasting, edge cases).
- **`tests/test_motion_intelligence_service.py`** — ~40 tests purs (trend, asymmetry, profiles, scores).
- **`tests/test_cache_service.py`** — ~15 tests (CacheKeys, graceful degradation Redis).
- **`tests/test_event_bus.py`** — ~15 tests (subscribe, publish, dispatch, singleton).

### Créé — Flutter Mobile (27 fichiers)

**Modèles** : `digital_twin.dart` (TwinComponent + DigitalTwinState + History), `biological_age.dart` (BiologicalAgeResult + Component + Lever), `adaptive_nutrition.dart` (DayType + NutritionTarget + AdaptiveNutritionPlan), `motion_intelligence.dart` (MotionIntelligenceResult + ExerciseMotionProfile + MotionHistoryItem).

**Features** : `twin/twin_notifier.dart` + `twin_status_screen.dart` + `twin_history_screen.dart`, `biological_age/biological_age_notifier.dart` + `biological_age_screen.dart` + `biological_age_history_screen.dart`, `adaptive_nutrition/adaptive_nutrition_notifier.dart` + `adaptive_nutrition_screen.dart`, `motion/motion_notifier.dart` + `motion_summary_screen.dart` + `motion_history_screen.dart`.

**Widgets partagés** : `glycogen_gauge.dart`, `twin_component_card.dart`, `biological_age_delta_card.dart`, `longevity_lever_card.dart`, `adaptive_macro_card.dart`, `movement_health_ring.dart`, `day_type_badge.dart`.

### Modifié — Flutter Mobile

- **`main.dart`** — +7 routes GoRouter (twin, twin/history, biological-age, biological-age/history, adaptive-nutrition, motion, motion/history).
- **`api_constants.dart`** — +10 endpoints (twinToday, twinHistory, twinSummary, biologicalAge, biologicalAgeHistory, biologicalAgeLevers, adaptiveNutritionTargets, adaptiveNutritionPlan, adaptiveNutritionRecompute, motionSummary, motionHistory, motionAsymmetryRisk).

### Créé — Tests Dart (~65 nouveaux tests)

- **`test/models/digital_twin_model_test.dart`** — ~20 tests
- **`test/models/biological_age_model_test.dart`** — ~15 tests
- **`test/models/adaptive_nutrition_model_test.dart`** — ~15 tests
- **`test/models/motion_model_test.dart`** — ~15 tests

**Total LOT 11** : **~265 nouveaux tests** (200 backend + 65 Dart) — ~58 nouveaux fichiers — 11 nouveaux endpoints API.

---

## [1.1.0] — 2026-03-08 — LOT 10 : Predictive Health Engine

### Créé — Backend (moteurs prédictifs)

- **`app/services/injury_risk_engine.py`** — `InjuryRiskResult` dataclass + 5 fonctions pures : `_compute_acwr()`, `_score_acwr_risk()` (zones 0.8–1.3 safe, >2.0 critique), `_score_fatigue_risk()` (0–100), `_score_biomechanics_risk()` (qualité mouvement inversée), `_score_readiness_risk()` (readiness faible = risque élevé). Pondération ACWR 35%/Fatigue 25%/Biomécanique 25%/Readiness 15%. `compute_injury_risk()` : risque blessure, risk_level, risk_area, recommandations contextualisées, confidence.
- **`app/services/overtraining_engine.py`** — `OvertrainingResult` dataclass + `_compute_acwr()` (7d / (28d/4), normalisation hebdo), `_acwr_zone()` (5 zones : undertraining/optimal/moderate_risk/high_risk/overreaching), `_score_acwr_overtraining()`, `_score_wellbeing()` (sommeil + fatigue combinés), `_score_readiness_overtraining()`. Pondération ACWR 40%/Bien-être 35%/Readiness 25%. `compute_overtraining_risk()` : ACWR, zone, recommandation principale.
- **`app/services/weight_prediction_engine.py`** — `WeightPredictionResult` dataclass + `_compute_tdee()` (préfère TDEE MetabolicTwin, fallback active_calories), `_compute_delta_kg()` (modèle : balance × jours × adaptation / 7700), `_trend_direction()` (±300g/sem = stable). Facteurs d'adaptation : 1.0/0.90/0.80 pour 7/14/30j. `compute_weight_predictions()` : 3 prédictions, bilan énergétique, tendance, hypothèses.
- **`app/schemas/predictions.py`** — Schémas Pydantic v2 : `InjuryRiskResponse`, `OvertrainingResponse`, `WeightPredictionResponse`, `HealthPredictionsResponse` (agrégée).
- **`app/api/v1/endpoints/predictions.py`** — 3 endpoints auth-requis : `GET /health/predictions` (combiné), `GET /health/injury-risk`, `GET /health/overtraining`. Helper `_load_all_inputs()` charge MetabolicStateSnapshot + ReadinessScore + DailyMetrics(7j) + VisionSessions(7j). avg_vision_quality = moyenne(stability, amplitude) des VisionSessions.

### Modifié — Backend

- **`app/api/v1/router.py`** — `predictions_router` inclus : `GET /health/predictions`, `/health/injury-risk`, `/health/overtraining`.

### Créé — Tests

- **`tests/test_injury_risk_engine.py`** — 47 tests purs (6 classes) : `TestComputeAcwr` (6), `TestScoreAcwrRisk` (9), `TestScoreFatigueRisk` (8), `TestScoreBiomecanicsRisk` (7), `TestScoreReadinessRisk` (6), `TestComputeInjuryRisk` (12), `TestInjuryRiskRecommendations` (3).
- **`tests/test_overtraining_engine.py`** — 38 tests purs (5 classes) : `TestComputeAcwr` (5), `TestAcwrZone` (8), `TestScoreAcwrOvertraining` (8), `TestScoreWellbeing` (6), `TestComputeOvertrainingRisk` (11).
- **`tests/test_weight_prediction_engine.py`** — 33 tests purs (4 classes) : `TestComputeTdee` (5), `TestComputeDeltaKg` (6), `TestTrendDirection` (7), `TestComputeWeightPredictions` (15).

Total LOT 10 : **118 nouveaux tests** — 118/118 ✅

---

## [1.0.0] — 2026-03-08 — LOT 9 : Coach IA + Jumeau Métabolique

### Créé — Backend

- **`app/models/coach.py`** — Modèles SQLAlchemy `ConversationThread` + `ConversationMessage` (UUID PK, JSONB metadata, timestamps). Relation thread → messages via FK CASCADE.
- **`app/db/migrations/versions/V006_coach_models.py`** — Migration : tables `conversation_threads` + `conversation_messages` + 5 colonnes sur `metabolic_state_snapshots` (protein_status, hydration_status, stress_load, plateau_risk, metabolic_age).
- **`app/services/metabolic_twin_service.py`** — `MetabolicState` dataclass (24 champs) + 9 fonctions pures : `_estimate_bmr()` (Mifflin-St Jeor), `_estimate_tdee()` (5 facteurs), `_estimate_glycogen()` (15g/kg max, 4 statuts), `_compute_fatigue()` (0–100, 4 composantes), `_compute_protein_status()` (4 statuts), `_compute_hydration_status()` (4 statuts), `_compute_stress_load()` (0–100), `_detect_plateau()` (écart-type 14j), `_estimate_metabolic_age()` (delta longévité). Fonctions DB : `save_metabolic_state()` (upsert), `get_or_compute_metabolic_state()` (façade).
- **`app/services/context_builder.py`** — `CoachContext` dataclass (8 sous-contextes) + `to_prompt_text()` (sérialisation structurée ≤5500 chars ≈1500 tokens, troncature sécurisée). `build_coach_context()` lit DailyMetrics, ReadinessScore, LongevityScore, VisionSession (7j), Insight (top 3 non lus), MetabolicTwin.
- **`app/services/claude_client.py`** — `generate_coach_reply()` : `CLAUDE_COACH_MOCK_MODE=True` → réponse simulée par mot-clé (fatigue/nutrition/entraînement/bilan/générique) ; `False` → `anthropic.AsyncAnthropic().messages.create()`. Prompt système SOMA 7 règles + structure 4 sections.
- **`app/services/coach_service.py`** — `CoachAnswer` dataclass + `_parse_coach_reply()` (regex Synthèse/Recommandations/⚠) + `ask_coach()` flow complet (contexte → thread → historique → Claude → parsing → persistance 2 messages). CRUD : `create_thread()`, `get_threads()`, `get_messages()`.
- **`app/schemas/coach.py`** — Schémas Pydantic v2 : `AskCoachRequest` (question 3–2000 chars, thread_id?), `CoachAnswerResponse`, `ConversationThreadResponse`, `ConversationMessageResponse`, `ConversationThreadDetailResponse`, `ThreadListResponse`.
- **`app/api/v1/endpoints/coach.py`** — 4 endpoints auth-requis : `POST /coach/ask`, `POST /coach/thread` (201), `GET /coach/history` (limit), `GET /coach/history/{id}` (403 si mauvais user).

### Modifié — Backend

- **`app/core/config.py`** — +5 settings : `CLAUDE_COACH_MOCK_MODE`, `CLAUDE_COACH_MODEL` (claude-sonnet-4-5), `CLAUDE_COACH_MAX_TOKENS` (1024), `CLAUDE_COACH_TIMEOUT_S` (45), `CLAUDE_COACH_TEMPERATURE` (0.3).
- **`app/api/v1/router.py`** — `coach_router` inclus : `POST /coach/ask`, `POST /coach/thread`, `GET /coach/history`, `GET /coach/history/{id}`.
- **`app/api/v1/endpoints/health_plan.py`** — Morning briefing IA : appel `build_coach_context()` + `generate_coach_reply()` après génération plan, stocké dans `DailyRecommendation.morning_briefing`. Non-bloquant (try/except + log warning).
- **`requirements.txt`** — `anthropic>=0.40.0` + `aiosqlite>=0.20.0`.

### Créé — Mobile Flutter

- **`lib/core/models/coach.dart`** — `CoachAnswer`, `CoachThread` (displayTitle getter), `CoachMessage` (isUser/isCoach getters), `CoachQuickPrompt`, `kCoachQuickPrompts` (4 prompts rapides).
- **`lib/features/coach/coach_notifier.dart`** — `CoachChatState` (lastAnswer, messages, currentThreadId, isLoading, error). `CoachChatNotifier` (ask, loadThread, newConversation) — `StateNotifierProvider.autoDispose`. `CoachThreadsNotifier` (AsyncNotifier, build + refresh).
- **`lib/features/coach/coach_chat_screen.dart`** — Chat UI complet : `_WelcomeView` (4 quick prompt cards), `_MessagesList` (ListView + typing indicator), `CoachMessageBubble` (user right / coach left avec avatar), `_CoachResponseContent` (parse Markdown **gras** / • bullet / ⚠ warning box), `_InputBar` (multiline + send button).
- **`lib/features/coach/coach_conversation_list_screen.dart`** — Historique fils : `_ThreadCard` (icon + titre + date + arrow), vues vide/chargement/erreur, FAB nouvelle conversation.

### Modifié — Mobile Flutter

- **`lib/core/api/api_constants.dart`** — +3 constantes : `coachAsk`, `coachThread`, `coachHistory`.
- **`lib/main.dart`** — +2 imports coach + 2 routes : `/coach` (CoachChatScreen, extra=threadId?) + `/coach/history` (CoachConversationListScreen).

### Créé — Tests

- **`tests/test_metabolic_twin.py`** — 43 tests unitaires (purs, sans DB) : `TestEstimateBmr` (6), `TestEstimateTdee` (5), `TestEstimateGlycogen` (5), `TestComputeFatigue` (5), `TestComputeProteinStatus` (5), `TestComputeHydrationStatus` (5), `TestComputeStressLoad` (4), `TestDetectPlateau` (4), `TestEstimateMetabolicAge` (6), `TestComputeMetabolicState` (4).
- **`tests/test_context_builder.py`** — 28 tests : structure globale (7), profil (5), récupération (5), sommeil (3), nutrition (4), longévité (3), alertes/insights (5), troncature (3).
- **`tests/test_coach_service.py`** — 33 tests : `_parse_coach_reply` (9), `_build_mock_reply` (8), `generate_coach_reply` mock (3), `create_thread` (4), `get_threads` (3), `get_messages` (3), `ask_coach` (10).
- **`tests/test_coach_api.py`** — 25 tests API : `POST /coach/ask` (9), `POST /coach/thread` (5), `GET /coach/history` (5), `GET /coach/history/{id}` (6 dont isolation user 403).

---

## [0.9.0] — 2026-03-07 — LOT 8 : Vision Integration + History + Hardening

### Modifié — Bugfix critique

- **`features/vision/models/vision_session.dart`** — Bugfix `toJson()` : `replaceAll('-', '_')` → `replaceAll(RegExp(r'[-\s]'), '_')`. "Jumping Jack" → `"jumping_jack"` (espace était non remplacé → backend 422). Même correctif dans `fromJson()`. Ajout fallback `created_at` si `started_at` absent (compatibilité backend qui retourne `created_at`).

### Créé — Historique Vision

- **`features/vision/providers/vision_history_notifier.dart`** — `VisionHistoryPeriod` enum (week/month/quarter), `VisionHistoryState` (period, exerciseFilter nullable, AsyncValue\<List\<VisionSession\>\>), `VisionHistoryNotifier` (load GET /vision/sessions avec filtres), `visionHistoryProvider` StateNotifierProvider.autoDispose. Extension `SupportedExerciseApiKey.toApiKey()` réutilise la regex corrigée.
- **`features/vision/screens/vision_history_screen.dart`** — Écran historique : `_PeriodSelector` (7j/30j/90j), `_ExerciseFilterChips` (horizontal scroll, Tous + 6 exercices), `_ProgressionChart` (fl_chart LineChart hauteur 130, belowBarData 8% opacité — si ≥3 sessions), `_VisionSessionCard` (exercice + date + score badge + stats ligne 2 — onTap detail). Vues: loading/erreur/vide.
- **`features/vision/screens/vision_session_history_detail_screen.dart`** — Détail session read-only. Reçoit `VisionSession` via GoRouter extra. Header exercice (icon cloud_done), stats (reps/durée), `_GlobalScoreCard` (QualityScoreWidget), `_DetailScoresCard` (barres amplitude/stabilité/régularité), `_RecommendationsCard`, `_MetadataCard` (date, algorithme v1.0, frames/reps analysés, workoutSessionId si présent).

### Modifié — Intégration Workout + Feedback V2

- **`features/workout/workout_session_detail_screen.dart`** — `_BottomActions` : Row existante (Exercice | Terminer) transformée en Column + nouvelle 2ème ligne bouton "Analyser avec Computer Vision" (vert, `context.push('/vision/setup?sessionId=$sessionId')`) visible si `session.isInProgress`.
- **`features/vision/screens/vision_workout_screen.dart`** — Feedback V2 : imports `exercise_frame.dart` + `rep_counter_state.dart`. `_ClassificationFeedback` modifié : si `cl.isValid && status == running` → affiche `_PhaseTip` (tips coaching par phase). `_PhaseTip` : Map\<(SupportedExercise, ExercisePhase), String\> — 20 tips couvrant les 6 exercices × 5 phases (record Dart 3). Fallback "✓ Bonne position".
- **`features/vision/screens/vision_exercise_setup_screen.dart`** — Ajout bouton "Historique" (icône bar_chart) dans AppBar actions → `context.push('/vision/history')`.

### Modifié — Routes GoRouter

- **`lib/main.dart`** — 4 nouveaux imports (`vision_session.dart`, `vision_history_screen.dart`, `vision_session_history_detail_screen.dart`) + 2 routes : `/vision/history` et `/vision/history/detail` (extra `VisionSession`).

### Créé — Tests Dart

- **`test/vision/vision_session_model_test.dart`** — +15 tests groupe "JumpingJack Bugfix (LOT 8)" : toJson 6 exercices snake_case, fromJson jumping_jack ✓, fromJson "jumping jack" → fallback squat (bug documenté), round-trip toJson/fromJson × 6 exercices, fallback created_at, fallback DateTime.now().
- **`test/vision/vision_history_notifier_test.dart`** — 20 tests : `VisionHistoryPeriod` (valeurs + labels × 3), `SupportedExerciseApiKey.toApiKey()` × 6 exercices, `VisionHistoryState` (construction, copyWith × 4, sentinel null), parsing JSON backend (5 sessions, round-trip exercise, id, isSaved, jumping_jack), provider existence + état initial.

---

## [0.8.0] — 2026-03-07 — LOT 7 : Computer Vision V1

### Créé

#### Services Computer Vision — Dart purs (features/vision/services/)
- **`angle_calculator.dart`** — Calcul angles articulaires 2D (hanche-genou-cheville, épaule-coude-poignet, tronc-hanche) + ratios ouverture (bras/jambes jumping jack). API publique `angleBetween(a,b,c)` pour tests. Service pur sans dépendance Flutter.
- **`rep_counter.dart`** — Interface `RepCounter` + 6 automates finis concrets : `SquatRepCounter` (seuils 155°/115°), `PushUpRepCounter` (150°/90°), `PlankRepCounter` (timer 300 frames = 1 compte), `JumpingJackRepCounter` (ratio ouverture bras+jambes 0.5/0.3), `LungeRepCounter` (155°/110°), `SitUpRepCounter` (70°/40°). Factory `RepCounterFactory.create()`. Compte au passage peak→ascending pour feedback immédiat.
- **`quality_scorer.dart`** — Score qualité biomécanique (0–100) en 3 composantes : amplitude (angle atteint vs référence par exercice), stabilité (déviation alignement vs 180°), régularité (coefficient de variation intervalles inter-rep). Pondération 40/35/25. `syncFromRepState()` pour sync incrémentale depuis `RepCounterState`.
- **`exercise_classifier.dart`** — Validation position initiale : couverture pose, landmarks requis, vue (profil squat/lunge, horizontal push-up/plank, frontal jumping jack, couché sit-up). Retourne `ClassificationResult` avec `isValid`, `confidence`, `feedback` localisé.

#### Platform bridge + Orchestration (features/vision/)
- **`services/pose_detector_service.dart`** — Pont ML Kit : `CameraImage` → `InputImage` (NV21 Android / BGRA8888 iOS) → `PoseDetector(stream, accurate)` → `DetectedPose` normalisé [0,1]. Mapping complet 33 landmarks ML Kit → `VisionLandmarkType`.
- **`providers/vision_notifier.dart`** — `VisionNotifier` (StateNotifierProvider.autoDispose). Cycle de vie : idle → initializing → ready → running → paused → finished → error. Throttle 1 frame sur 2 (_kFrameSkip). Pipeline : PoseDetectorService → ExerciseClassifier → AngleCalculator → RepCounter → QualityScorer. Timer interne pour durée session.

#### Écrans (features/vision/screens/)
- **`vision_exercise_setup_screen.dart`** — Sélection exercice (grille 2×3), guide positionnement caméra (dialog), initialisation notifier, navigation vers /vision/workout. Accepte `workoutSessionId?` pour rattacher à une session.
- **`vision_workout_screen.dart`** — Preview caméra scale-to-fill + `CustomPaint(PoseOverlayPainter)`. Barre top : timer badge, nom exercice, bouton fermer. Feedback classification (vert=valide, orange=invalide). Contrôles : Démarrer / Pause+Arrêter / Reprendre. Dialog confirmation avant arrêt. Navigation auto vers /vision/summary quand status==finished.
- **`vision_session_summary_screen.dart`** — Résumé session : en-tête exercice, stats (reps + durée totale), anneau score global, barres détail (amplitude/stabilité/régularité), recommandations contextuelles. Bouton sauvegarde POST /vision/sessions avec indicateur loading + confirmation.

#### Widgets (features/vision/widgets/)
- **`pose_overlay_painter.dart`** — `CustomPainter` : 12 connexions osseuses (épaule-coude-poignet, hanche-genou-cheville…) + 12 cercles articulaires. Coloris vert (pose valide) ou orange (invalide). Landmarks non fiables ignorés.
- **`rep_counter_widget.dart`** — Compteur animé (AnimatedSwitcher + ScaleTransition, fontSize 48). Badge phase coloré (ExercisePhase → couleur). Affiche durée formatée pour exercices timer (plank).
- **`quality_score_widget.dart`** — Anneau de score CustomPainter. Arc de progression coloré (vert ≥80, orange ≥60, rouge <60). Score numérique + label centré.

#### Modèle Dart (features/vision/models/)
- **`vision_session.dart`** — `VisionSession` (données session locale), `MovementQuality` (4 scores + labels + `hasEnoughData`). Méthodes : `durationLabel`, `isSaved`, `toJson()` (snake_case exercice), `fromJson()`. Labels `overallLabel` : Excellent ≥80, Bon ≥65, Correct ≥50, À améliorer ≥35, Insuffisant <35.
- **`exercise_frame.dart`** — `ExerciseAngles`, `SupportedExercise` (enum avec `nameEn`, `nameFr`, `iconAsset`), `ExercisePhase`, `RepCounterState`.
- **`pose_landmark.dart`** — `VisionLandmarkType` (enum 33 landmarks), `VisionLandmarkPoint` (x, y, z, score, `isReliable`), `DetectedPose` (getters landmarks nommés).

#### Backend (Python)
- **`app/db/migrations/versions/V005_vision_sessions.py`** — Migration Alembic : table `vision_sessions` (id UUID PK, user_id FK cascade, exercise_type, rep_count, duration_seconds, 4 score FLOAT nullable, workout_session_id FK SET NULL nullable, metadata JSONB, algorithm_version, session_date, created_at). Index composé user+date + index workout_session.
- **`app/models/vision_session.py`** — Modèle SQLAlchemy `VisionSession`. Colonne `metadata_` mappée → "metadata" (évite conflit avec `DeclarativeBase.metadata`).
- **`app/schemas/vision.py`** — `VisionSessionCreate` : validation `exercise_type` contre ensemble autorisé, alias `reps`, scores Optional[float] 0–100. `VisionSessionResponse` : `from_attributes=True`.
- **`app/api/v1/endpoints/vision.py`** — `POST /vision/sessions` (201 CREATED, extrait `algorithm_version` depuis metadata) + `GET /vision/sessions` (filtres : exercise_type, from_date, limit 1–200).

#### Tests (Dart + Python)
- **`test/vision/angle_calculator_test.dart`** — 8 tests : angle 90°, 180°, 45°, 120°, vecteurs nuls → 0, bornes [0°, 180°].
- **`test/vision/rep_counter_test.dart`** — 36 tests : cycles complets (1 rep, 2 reps), abandon sans peak, tracking angle peak, angles null ignorés, reset état, factory, PlankRepCounter (timer), JumpingJackRepCounter (ratio).
- **`test/vision/quality_scorer_test.dart`** — 18 tests : amplitude (parfait/insuffisant/zéro), stabilité (parfait/déviation/couverture ignorée), régularité (régulière/irrégulière/< 3 reps neutre=60), score global pondéré, syncFromRepState, reset.
- **`test/vision/vision_session_model_test.dart`** — 28 tests : construction, `durationLabel`, `isSaved`, `toJson` (snake_case, scores, metadata conditionnels), `fromJson` (tous champs, mapping exercice, fallback), `MovementQuality` (labels, `hasEnoughData`, `copyWith`).
- **`test/vision/exercise_classifier_test.dart`** — 14 tests : pose vide (noPose), coverage insuffisante, squat profil valide, JJ vue frontale, mauvaise vue JJ, `ClassificationResult.noPose`.
- **`tests/test_vision.py`** — 28 tests : `TestVisionSessionCreate` (types valides/invalides, reps/durée négatifs, scores hors bornes, champs optionnels, metadata), `TestVisionSessionResponse` (construction, nullable), `TestExerciseTypeValidator` (parametrize 6 valides + 8 invalides).

### Modifié
- **`lib/main.dart`** — Imports 3 écrans vision + 3 nouvelles routes GoRouter (`/vision/setup`, `/vision/workout`, `/vision/summary`)
- **`core/api/api_constants.dart`** — Ajout `visionSessions = '$apiPrefix/vision/sessions'`
- **`app/api/v1/router.py`** — `include_router(vision_router)`
- **`pubspec.yaml`** — Ajout `google_mlkit_pose_detection: ^0.11.0`, `permission_handler: ^11.3.0`

### Notes techniques
- **100% on-device** : aucune vidéo transmise au serveur — seul le résumé JSON (scores + reps + durée) est envoyé en POST
- **Bug connu** : `VisionSession.toJson()` encode "Jumping Jack" → "jumping jack" (espace non remplacé par `_`). Le backend rejette cette valeur. Correctif : `exercise.nameFr` ou remplacement explicite des espaces dans `toJson()` (LOT 8)

---

## [0.7.0] — 2026-03-07 — LOT 6 : Mobile Features Complètes

### Créé

#### Modèles Dart (core/models/)
- **`nutrition.dart`** — `FoodItem`, `NutritionEntry`, `MacroTotals`, `MacroGoals`, `DailyNutritionSummary`, `DetectedFood`, `NutritionPhoto` (avec booleans `isAnalyzed`, `isFailed`, `isPending`)
- **`workout.dart`** — `ExerciseLibrary` (+ `categoryLabel`, `displayName`), `WorkoutSet` (+ `display`), `ExerciseEntry` (+ `tonnage`, `totalSets`, `totalReps`, filtre `isDeleted`), `WorkoutSession` (+ `typeLabel`, `statusLabel`, `locationLabel`, `isCompleted`, `isInProgress`)
- **`hydration.dart`** — `HydrationLog` (+ `beverageLabel`, `beverageEmoji`), `HydrationSummary` (+ `progress`, `remainingMl`)
- **`sleep_log.dart`** — `SleepSession` (+ `qualityLabel`, `durationLabel`, `qualityEmoji`)
- **`profile.dart`** — `ComputedMetrics` (+ `toJson()`), `UserProfile` (+ `displayName`, `goalLabel`, `activityLabel`, `fitnessLabel`)

#### Notifiers Riverpod (features/)
- **`nutrition/nutrition_notifier.dart`** — `NutritionSummaryNotifier`, `FoodSearchNotifier`, `PhotoAnalysisNotifier` (polling 2s, timeout 30s)
- **`workout/workout_notifier.dart`** — `WorkoutSessionsNotifier`, `sessionDetailProvider.family`, `ExercisesNotifier`, helpers `addExerciseToSession` / `addSetToExercise`
- **`hydration/hydration_notifier.dart`** — `HydrationNotifier` (addEntry avec type boisson)
- **`sleep/sleep_notifier.dart`** — `SleepNotifier` (logSleep avec ISO-8601)
- **`profile/profile_notifier.dart`** — `ProfileNotifier` (update PATCH partiel)
- **`history/history_notifier.dart`** — `MetricsHistoryNotifier` + enum `HistoryPeriod` (7/30/90 jours)

#### Écrans Journal (features/journal/ + features/nutrition/ + features/workout/)
- **`journal/journal_hub_screen.dart`** — Hub 4 cartes avec résumés temps réel
- **`nutrition/nutrition_home_screen.dart`** — Résumé macros + liste repas groupés par type + FAB
- **`nutrition/nutrition_entry_form_screen.dart`** — Formulaire saisie + picker type + photo
- **`nutrition/food_search_screen.dart`** — Recherche temps réel, sélection via pop
- **`nutrition/photo_review_screen.dart`** — Revue analyse IA (confidence bar + aliments + macros estimées)
- **`workout/workout_sessions_screen.dart`** — Liste sessions + statut badge + FAB
- **`workout/workout_session_create_screen.dart`** — Grid type + lieu + date/heure picker
- **`workout/workout_session_detail_screen.dart`** — Exercices + séries + dialog +série + compléter
- **`workout/exercise_picker_screen.dart`** — Bibliothèque searchable (cache client)

#### Écrans Données Simples
- **`hydration/hydration_screen.dart`** — Anneau progression + boutons rapides +250/500/750/1000 ml
- **`sleep/sleep_screen.dart`** — Time pickers + sélecteur qualité ★ 1-5 + historique 14j
- **`settings/settings_screen.dart`** — Logout confirmé + version + serveur + lien édition profil

#### Écrans Profil & Historique
- **`profile/profile_screen.dart`** — Profil complet + métriques calculées + liens rapides
- **`profile/edit_profile_screen.dart`** — Formulaire PATCH partiel (prénom, poids, régime, IF, repas/jour)
- **`history/metrics_history_screen.dart`** — 5 graphiques `LineChart` fl_chart (poids, calories, protéines, hydratation, HRV) + sélecteur période

#### Tests Flutter
- **`test/models/nutrition_model_test.dart`** — 18 tests (FoodItem, NutritionEntry, MacroTotals, DailyNutritionSummary, NutritionPhoto)
- **`test/models/workout_model_test.dart`** — 17 tests (ExerciseLibrary, WorkoutSet, ExerciseEntry, WorkoutSession)
- **`test/models/profile_model_test.dart`** — 18 tests (UserProfile, ComputedMetrics, HydrationSummary, HydrationLog, SleepSession)

### Modifié
- **`lib/main.dart`** — Navigation restructurée : 5 onglets (Dashboard | Journal | Plan | Insights | Profil) + 12 nouvelles routes hors ShellRoute
- **`core/api/api_client.dart`** — Ajout `delete<T>()` et `postFile<T>()` (FormData multipart)
- **`core/api/api_constants.dart`** — 10 nouveaux endpoints (foodItems, nutritionEntries, nutritionDailySummary, nutritionPhotos, sessions, exercises, hydrationLog, hydrationToday, sleepLog, bodyMetrics)
- **`pubspec.yaml`** — Ajout `image_picker: ^1.1.2`

---

## [0.6.0] — 2026-03-07 — LOT 5 : Stabilisation + Mobile MVP Extended

### Créé

#### Backend — Stabilisation (LOT 5A)

- **`app/db/migrations/versions/V004_algorithm_version.py`** — Migration V004 :
  - Colonne `algorithm_version VARCHAR(10) DEFAULT 'v1.0'` sur `daily_metrics`, `readiness_scores`, `longevity_scores`

- **`app/schemas/home.py`** — Schémas agrégateur home :
  - `HomeSummaryResponse` — réponse principale (metrics + readiness + insights + plan + longevity)
  - `HomeSummaryMetrics`, `HomeSummaryReadiness`, `HomeSummaryInsight`, `HomeSummaryPlan`, `HomeSummaryLongevity`

- **`app/api/v1/endpoints/home.py`** — `home_router` (prefix `/home`) :
  - `GET /home/summary` — agrégateur de démarrage mobile (lazy compute déclenché, 5 SELECT, pas de compute lourd)

#### Tests intégration PostgreSQL (3 nouveaux fichiers — skip auto sans `SOMA_TEST_DATABASE_URL`)

- **`tests/integration/test_daily_metrics_pipeline.py`** — `TestDailyMetricsPersistence` (5 tests), `TestLazyEnsureTodayMetrics` (2 tests), `TestMetricsHistory` (3 tests)
- **`tests/integration/test_insights_integration.py`** — `TestInsightPersistence` (3 tests), `TestInsightEndpointHTTP` (3 tests)
- **`tests/integration/test_longevity_integration.py`** — `TestLongevityEndpoint` (6 tests), `TestHomeSummaryEndpoint` (5 tests), `TestDailyMetricsEndpoint` (2 tests)

#### Mobile Flutter — Complétion MVP (LOT 5B)

- **`lib/core/config/app_config.dart`** — `AppEnvironment` (dev/prod) + `AppConfig.init()` :
  - `baseUrl` dev → `http://10.0.2.2:8000`, prod → `https://api.soma-health.app`

- **`lib/core/errors/api_error.dart`** — Gestion erreurs structurée :
  - `ApiErrorType` enum : `network`, `unauthorized`, `notFound`, `validation`, `server`, `unknown`
  - `ApiError.fromDioException()` — mapping `DioException` → `ApiError`
  - `ApiError.fromException()` — wrapper générique

- **`lib/core/models/insight.dart`** — `Insight` + `InsightList` + `fromJson` + helper `categoryLabel`

- **`lib/features/auth/auth_state.dart`** — Sealed class hierarchy :
  - `AuthStateInitial`, `AuthStateLoading`, `AuthStateAuthenticated`, `AuthStateUnauthenticated`, `AuthStateError`

- **`lib/features/auth/auth_notifier.dart`** — `authProvider = StateNotifierProvider<AuthNotifier, AuthState>` :
  - `_restoreSession()` — vérifie SharedPreferences au démarrage
  - `login(email, password)` — POST `/auth/login` → tokens → state Authenticated
  - `logout()` — clear storage + state Unauthenticated

- **`lib/features/auth/login_screen.dart`** — Écran de connexion :
  - Logo SOMA gradient + champs email/password + loading indicator + SnackBar erreur
  - `ref.listen<AuthState>` pour réagir aux changements d'état

- **`lib/features/insights/insights_notifier.dart`** — `insightsProvider = AsyncNotifierProvider<InsightsNotifier, InsightList>` :
  - `markAsRead(id)` — PATCH + mise à jour optimiste état local
  - `dismiss(id)` — PATCH + suppression optimiste de la liste locale

- **`lib/features/insights/insights_screen.dart`** — 4ème onglet Insights :
  - Filtres chips : Tous / Non lus (N) / Attention / Critique
  - `_InsightCard` : badge sévérité coloré, indicateur non lu, boutons Lu/Ignorer
  - Empty state + error state avec bouton Réessayer

- **`lib/shared/widgets/loading_skeleton.dart`** — Placeholders animés :
  - `SkeletonBox` — animation opacity 0.3→0.7 (1.2s, `easeInOut`, repeat)
  - `MetricCardSkeleton`, `DashboardSkeleton`, `InsightsSkeleton`

### Modifié

#### Backend

- **`app/models/metrics.py`** — `DailyMetrics` : +`algorithm_version: Mapped[str]` (`server_default="v1.0"`)
- **`app/models/scores.py`** — `ReadinessScore` : +`algorithm_version`, +`updated_at` (bug corrigé) ; `LongevityScore` : +`algorithm_version`
- **`app/schemas/metrics.py`** — `DailyMetricsResponse` : +`algorithm_version: str = "v1.0"`
- **`app/schemas/scores.py`** — `ReadinessScoreResponse` : +`algorithm_version`, `updated_at` correctement mappé
- **`app/schemas/insights.py`** — `LongevityScoreResponse` : +`algorithm_version` ; `DailyHealthPlanResponse` : +`from_cache: bool = False`
- **`app/services/daily_metrics_service.py`** — `compute_and_persist_daily_metrics` : set `snapshot.algorithm_version = "v1.0"`
- **`app/services/readiness_service.py`** — `compute_and_persist_readiness` : set `algorithm_version = "v1.0"` + `updated_at = now` (insert et update)
- **`app/api/v1/endpoints/scores.py`** — `GET /scores/longevity` : +`algorithm_version="v1.0"` dans `LongevityScoreResponse`
- **`app/api/v1/endpoints/health_plan.py`** — Cache 6h via `DailyRecommendation` :
  - Vérifie fraîcheur du plan (< 6h) → retourne depuis cache avec `from_cache=True`
  - Sinon génère + upsert `DailyRecommendation.daily_plan` (JSONB)
- **`app/api/v1/router.py`** — +`home_router` (`GET /home/summary`)
- **`tests/integration/conftest_pg.py`** — +import `app.models.metrics`, `app.models.insights`

#### Mobile

- **`lib/core/auth/token_storage.dart`** — Upgrade in-memory → SharedPreferences :
  - `static Future<void> load()` — appelé au démarrage de l'app
  - `setTokens()`, `setAccessToken()`, `clear()` maintenant `async`
  - Clés : `soma_access_token`, `soma_refresh_token`
- **`lib/core/api/api_client.dart`** — `_AuthInterceptor` : `await _tokens.setAccessToken()` et `await _tokens.clear()`
- **`lib/core/api/api_constants.dart`** — +`homeSummary = '$apiPrefix/home/summary'`
- **`lib/main.dart`** — Réécriture complète :
  - `await TokenStorage.load()` au démarrage
  - `SomaApp` → `ConsumerWidget` (router construit avec `ref`)
  - `_buildRouter(ref)` avec `redirect` auth guard + `refreshListenable: _AuthListenable(ref)`
  - Route `/login` hors `ShellRoute`
  - `ShellRoute` : 4 onglets (Dashboard, Plan du Jour, Longévité, Insights)
  - `_AuthListenable` — `ChangeNotifier` lié à `authProvider` pour refresh router

### Corrigé

- **`app/models/scores.py`** — Bug pré-existant : `ReadinessScore` n'avait pas `updated_at` dans le modèle SQLAlchemy bien qu'elle soit présente en DB depuis V002. Colonne `Mapped[datetime]` ajoutée, service et schéma alignés.

### Tests

- **Total : 422 tests passent, 3 skipped** (intégration PostgreSQL nécessitent `SOMA_TEST_DATABASE_URL`)
- 3 nouveaux fichiers tests intégration créés — skip automatique sans Docker/PostgreSQL

---

## [0.5.0] — 2026-03-07 — LOT 4 : Autonomous Health System

### Créé

#### Scheduler (APScheduler)

- **`app/services/scheduler_service.py`** — Orchestrateur du pipeline quotidien :
  - `_run_step(name, coro)` — isolation try/except par étape, retourne `(bool, message)`
  - `_step1_daily_metrics` — `compute_and_persist_daily_metrics(force_recompute=True)`
  - `_step2_readiness` — `build_sleep_summary` + `compute_and_persist_readiness`
  - `_step3_insights` — `run_and_persist_insights`, retourne nombre d'insights générés
  - `_step4_health_plan` — `generate_daily_health_plan` (log seulement, pas de persistance)
  - `_step5_longevity` — `compute_longevity_score` (log seulement, pas de persistance)
  - `run_daily_pipeline_for_user(db, user_id, target_date)` — pipeline complet avec rapport `{step: "ok"|"error: ..."}`
  - `run_daily_pipeline_all_users(target_date)` — boucle tous users actifs, commit après chaque user
  - `daily_pipeline_job()` — point d'entrée APScheduler (cron 5h30 Paris)
  - `create_scheduler()` — factory `AsyncIOScheduler` (non démarré, délégué au lifespan)

#### Fallback lazy computation

- **`app/services/daily_metrics_service.py`** — Ajout de `lazy_ensure_today_metrics(db, user_id, target_date, profile)` :
  - Déclenche `compute_and_persist_daily_metrics(force_recompute=False)`
  - Absorbe toutes les exceptions (log warning, retourne `None`)
  - Cache 2h natif — pas de double calcul si données fraîches

#### Flutter MVP (`mobile/`)

- **`pubspec.yaml`** — Config Flutter + dépendances : `flutter_riverpod ^2.5.1`, `go_router ^13.2.0`, `dio ^5.4.0`, `fl_chart ^0.67.0`
- **`lib/core/api/api_client.dart`** — Client HTTP Dio avec intercepteur JWT (injection token + auto-refresh sur 401)
- **`lib/core/api/api_constants.dart`** — Tous les endpoints API centralisés
- **`lib/core/auth/token_storage.dart`** — Singleton JWT en mémoire
- **`lib/core/models/daily_metrics.dart`** — Modèle `DailyMetrics` + `fromJson` + helpers calculés (caloriePct, proteinPct, hydrationPct, sleepHours)
- **`lib/core/models/health_plan.dart`** — Modèles `DailyHealthPlan`, `WorkoutRecommendation`, `NutritionTargetsSummary`
- **`lib/core/models/longevity.dart`** — Modèles `LongevityScore`, `ImprovementLever` + helper `components` (liste des 7 composantes)
- **`lib/shared/widgets/soma_app_bar.dart`** — AppBar SOMA (fond noir, logo gradient, ligne séparatrice)
- **`lib/shared/widgets/metric_card.dart`** — Card générique avec label, valeur, unité, barre de progression optionnelle
- **`lib/shared/widgets/score_ring.dart`** — Anneau circulaire `CustomPainter` (0-100, couleur dynamique rouge→orange→vert)
- **`lib/features/dashboard/`** — `DashboardNotifier` (AsyncNotifier) + `DashboardScreen` (8 MetricCards, pull-to-refresh)
- **`lib/features/health_plan/`** — `HealthPlanNotifier` + `HealthPlanScreen` (récupération badge, séance, macros, IF, conseils, alertes)
- **`lib/features/longevity/`** — `LongevityNotifier` + `LongevityScreen` (ScoreRing 180px, 7 barres composantes, leviers)
- **`lib/main.dart`** — Entry point : `ProviderScope` + `MaterialApp.router` + GoRouter (`ShellRoute` + `BottomNavigationBar` 3 onglets)

### Modifié

- **`app/main.py`** — Lifespan FastAPI : `create_scheduler().start()` au démarrage, `scheduler.shutdown(wait=False)` à l'arrêt
- **`app/api/v1/endpoints/health_plan.py`** — Ajout appel `lazy_ensure_today_metrics` avant `generate_daily_health_plan`
- **`app/api/v1/endpoints/scores.py`** — Ajout appel `lazy_ensure_today_metrics` avant `get_metrics_history` dans `/longevity`
- **`requirements.txt`** — Ajout `apscheduler==3.10.4`
- **`docs/ARCHITECTURE.md`** — Section 9 "Scheduler & Background Jobs"
- **`docs/ROADMAP.md`** — LOT 4 marqué ✅ complété

### Tests

- **`tests/test_scheduler.py`** — 33 nouveaux tests (5 classes) :
  - `TestRunStep` (6) : isolation exceptions, logging, non-propagation
  - `TestRunDailyPipelineForUser` (8) : pipeline complet, isolation par step, cas limites
  - `TestDailyPipelineAllUsers` (5) : multi-users, commit per user, isolation par user
  - `TestLazyEnsureTodayMetrics` (6) : fallback compute, force_recompute=False, absorb exceptions
  - `TestCreateScheduler` (8) : configuration APScheduler, cron, timezone, misfire_grace_time
- **Total : 422 tests passent, 3 skipped** (3 tests intégration nécessitant PostgreSQL)

---

## [0.4.0] — 2026-03-07 — LOT 3 : Health Intelligence Engine

### Créé

#### Modèles SQLAlchemy (2 nouvelles tables)
- **`app/models/metrics.py`** — `DailyMetrics` : snapshot journalier agrégé de toutes les métriques santé (21 champs : poids, calories, protéines, glucides, lipides, fibres, hydratation, pas, calories actives, distance, FC repos, HRV, sommeil, score sommeil, label qualité, entraînements, tonnage, charge, score récupération, complétude)
- **`app/models/insights.py`** — `Insight` : insights détectés par l'engine (catégorie, sévérité, titre, message, evidence JSONB, is_read, is_dismissed, expiration 7j, contrainte unique user_id+category+period)

#### Schémas Pydantic
- **`app/schemas/metrics.py`** — Schémas metrics :
  - `DailyMetricsResponse`, `DailyMetricsHistoryResponse` (avec tendances sur N jours)
  - `NutritionTargetsResponse`, `MacroBreakdown`, `FastingWindowInfo`
  - `MicronutrientDetail`, `MicronutrientAnalysisResponse`
- **`app/schemas/insights.py`** — Schémas intelligence :
  - `InsightResponse`, `InsightListResponse` (avec compteurs unread/critical, agrégats par catégorie/sévérité)
  - `DailyHealthPlanResponse`, `WorkoutRecommendation`, `EatingWindow`
  - `LongevityScoreResponse`, `LongevityComponentScore`
  - `SupplementSuggestion`, `SupplementRecommendationResponse`, `SupplementRecommendationsResponse`

#### Services — moteurs purs (aucune dépendance DB)

- **`app/services/nutrition_engine.py`** — Calcul besoins nutritionnels personnalisés :
  - `compute_workout_calorie_bonus` — bonus calorique par type/durée/RPE d'entraînement
  - `compute_fat_target_g` — ratio lipides selon objectif (FAT_RATIO_BY_GOAL)
  - `compute_carbs_target_g` — glucides résiduels (calories - protéines - lipides)
  - `compute_fiber_target_g` — 14g / 1000 kcal (recommandation IOM)
  - `compute_macro_percentages` — répartition % énergie
  - `compute_fasting_window` — fenêtre alimentaire IF + heure début jeûne
  - `compute_nutrition_targets` — pipeline complet (BMR → TDEE → bonus → macros → fibres → hydratation)

- **`app/services/micronutrient_engine.py`** — Analyse micronutritionnelle :
  - Suivi 8 micronutriments (vitamine D, magnésium, potassium, sodium, calcium, fer, zinc, oméga-3)
  - `estimate_from_food_group` — estimation par groupe alimentaire (fallback)
  - `extract_micros_from_food_item` — extraction depuis JSONB catalogue (source primaire)
  - `classify_status` — statut sufficient/low/deficient vs AJR
  - `analyze_micronutrients` — analyse complète avec score global et déficits

- **`app/services/supplement_engine.py`** — Recommandations compléments alimentaires :
  - Règles métier pour 5 compléments : vitamine D, magnésium, créatine, protéines, fer
  - `generate_supplement_recommendations` — jusqu'à 5 suggestions triées par confiance
  - `build_analysis_basis` — contexte narratif de l'analyse

- **`app/services/insight_engine.py`** — Détection de patterns sur 7 jours :
  - 7 règles : protéines insuffisantes, déficit calorique excessif, activité faible, fatigue accumulée, dette sommeil, déshydratation chronique, risque surentraînement (ACWR > 1.5)
  - `run_insight_engine` — orchestrateur avec isolation des erreurs par règle

- **`app/services/longevity_engine.py`** — Score longévité multi-dimensionnel (0-100) :
  - 7 composantes : cardio (pas + HRV + calories actives), force (tonnage + fréquence), sommeil (durée + qualité), nutrition (conformité calories + protéines), poids (IMC), composition corporelle (% graisse), consistance (tracking + streak)
  - `compute_longevity_score` — âge biologique estimé, leviers d'amélioration, niveau de confiance

- **`app/services/health_plan_service.py`** — Morning briefing journalier :
  - `get_readiness_level` — excellent/good/fair/poor/unknown depuis score 0-100
  - `build_workout_recommendation` — type, durée, intensité, localisation selon récupération et équipement
  - `build_daily_tips` — 2-4 conseils contextuels prioritaires
  - `build_eating_window` — fenêtre IF avec horaires précis
  - `choose_nutrition_focus` — nutriment à surveiller en priorité
  - `generate_daily_health_plan` — plan complet du jour

#### Services — couche DB

- **`app/services/daily_metrics_service.py`** — Agrégation et persistance DailyMetrics :
  - `compute_and_persist_daily_metrics` — upsert avec cache 2h (freshness check)
  - `get_metrics_history` — historique N jours avec tendances (readiness, sommeil, calories, pas, protéines, poids, fréquence entraînement)

- **`app/services/insight_service.py`** — Couche DB pour le modèle Insight :
  - `get_insights` — liste avec filtres (catégorie, sévérité, include_dismissed)
  - `run_and_persist_insights` — fetch métriques 7j+28j → run_insight_engine → upsert par contrainte unique
  - `mark_read / mark_dismissed` — mise à jour statut avec ownership strict
  - `build_insight_list_response` — agrégation unread_count, critical_count, by_category, by_severity

#### Endpoints API (9 nouveaux endpoints)

- **`app/api/v1/endpoints/metrics.py`** — `metrics_router` (prefix `/metrics`) :
  - `GET /metrics/daily` — snapshot journalier (calcul+persist si nécessaire, `?force_recompute=true`)
  - `GET /metrics/history` — historique 1-90 jours avec tendances

- **`app/api/v1/endpoints/insights.py`** — `insights_router` (prefix `/insights`) :
  - `GET /insights` — liste paginable (filtres : `days`, `category`, `severity`, `include_dismissed`)
  - `POST /insights/run` — déclenche l'analyse + persist, retourne les nouveaux insights
  - `PATCH /insights/{id}/read` — marque lu
  - `PATCH /insights/{id}/dismiss` — marque ignoré

- **`app/api/v1/endpoints/health_plan.py`** — `health_plan_router` (prefix `/health`) :
  - `GET /health/plan/today` — plan santé journalier complet (morning briefing)

- **`app/api/v1/endpoints/scores.py`** — Endpoint ajouté :
  - `GET /scores/longevity` — score longévité multi-dimensionnel avec âge biologique

- **`app/api/v1/endpoints/nutrition.py`** — 3 endpoints ajoutés à `summary_router` :
  - `GET /nutrition/targets` — besoins nutritionnels personnalisés du jour
  - `GET /nutrition/micronutrients` — analyse micronutritionnelle (1-30 jours)
  - `GET /nutrition/supplements/recommendations` — recommandations compléments basées sur les données réelles

#### Tests unitaires (218 nouveaux tests)

- **`tests/test_nutrition_engine.py`** — 35 tests (7 classes)
- **`tests/test_micronutrient_engine.py`** — 28 tests (6 classes)
- **`tests/test_supplement_engine.py`** — 30 tests (8 classes)
- **`tests/test_insight_engine.py`** — 37 tests (8 classes)
- **`tests/test_longevity_engine.py`** — 36 tests (8 classes)
- **`tests/test_health_plan.py`** — 33 tests (6 classes)

### Corrigé (bugs découverts pendant les tests)

- **`app/services/nutrition_engine.py`** — `calculate_calorie_target()` : ajout des args `current_weight_kg` et `goal_weight_kg` manquants dans l'appel
- **`app/services/nutrition_engine.py`** — `calculate_protein_target()` : kwarg `lean_mass_kg` → `body_fat_pct` (la fonction gère la masse maigre en interne)
- **`app/services/micronutrient_engine.py`** — `STATUS_THRESHOLDS` : valeurs corrigées de décimal (`0.80`) vers pourcentage (`80.0`) pour correspondre au format de `pct_of_target` calculé en %

### Modifié

- **`app/api/v1/router.py`** — +`metrics_router`, +`insights_router`, +`health_plan_router`
- **`app/api/v1/endpoints/scores.py`** — +endpoint `GET /scores/longevity`
- **`app/api/v1/endpoints/nutrition.py`** — +3 endpoints LOT 3 (`/nutrition/targets`, `/nutrition/micronutrients`, `/nutrition/supplements/recommendations`)

### Compteur tests

- **389 tests ✅ (3 skipped intégration PostgreSQL)**
  - 171 tests LOT 0/1/2
  - 218 tests LOT 3 (tous passent ✅)
- Couverture : calculs physiologiques, moteurs purs (nutrition, micronutriments, suppléments, insights, longévité, plan santé)

---

## [0.3.0] — 2026-03-07 — LOT 2 : Nutrition + ReadinessScore persistant + Tests intégration

### Créé

#### Migration base de données
- **`app/db/migrations/versions/V002_nutrition_and_scores_addons.py`**
  - `nutrition_entries` : ajout `is_deleted`, `updated_at`, `meal_name` + index partiel actif
  - `nutrition_photos` : ajout `is_deleted`, `updated_at`, `entry_id` (FK vers entries), `file_size_bytes`, `mime_type`
  - `readiness_scores.updated_at` : champ timestamp pour tracking de fraîcheur
  - `food_items` : index trigram GIN sur `name` et `name_fr` (recherche floue)

#### Config
- **`app/core/config.py`** — Ajout : `CLAUDE_VISION_MOCK_MODE`, `CLAUDE_VISION_MODEL`, `CLAUDE_VISION_TIMEOUT_S`, `MAX_FOOD_PHOTO_SIZE_MB`, `ALLOWED_PHOTO_MIME_TYPES`, `TEST_DATABASE_URL`

#### Schémas Pydantic
- **`app/schemas/nutrition.py`** — Schémas complets module nutrition :
  - `FoodItemResponse`, `FoodItemListResponse`
  - `NutritionEntryCreate` (model_validator : source ou macros requises), `NutritionEntryUpdate`, `NutritionEntryResponse`, `NutritionEntryListResponse`
  - `DailyNutritionSummary`, `MacroActuals`, `MacroGoals`, `MacroBalance`, `MealSummaryItem`, `EatingWindow`
  - `NutritionPhotoUploadResponse`, `DetectedFoodItem`, `PhotoAnalysisResult`
  - `PhotoConfirmRequest`, `PhotoConfirmResponse`
- **`app/schemas/scores.py`** — `ReadinessScoreResponse`, `ReadinessScoreHistoryResponse`

#### Services
- **`app/services/nutrition_service.py`** — Logique métier complète :
  - `compute_macros_from_food_item` — calcul pur testable (per_100g × quantity / 100)
  - `compute_eating_window` — fenêtre alimentaire + compatibilité jeûne 16:8
  - `compute_data_completeness` — % entrées avec calories renseignées
  - `search_food_items` — ILIKE multi-champs + filtre food_group + pagination
  - CRUD complet `NutritionEntry` avec soft-delete et ownership strict
  - `get_daily_summary` — totaux, objectifs, balance, fenêtre, repas résumés
  - `confirm_photo_and_create_entry` — pipeline confirmation photo → entrée

- **`app/services/readiness_service.py`** — Persistance quotidienne :
  - `compute_and_persist_readiness` — upsert avec freshness check (< 1h : retourne existant)
  - `get_readiness_score` — lecture par (user_id, score_date)
  - `get_readiness_history` — N jours en ordre décroissant

#### Utilitaires
- **`app/utils/storage.py`** — Stockage local photos :
  - `validate_photo_file` — validation MIME type
  - `save_photo` — streaming + vérification taille (chunks 64Ko)
  - `delete_photo` — suppression best-effort
  - `get_photo_abs_path` — résolution chemin absolu

- **`app/utils/vision_prompt.py`** — Pipeline IA :
  - `MEAL_ANALYSIS_PROMPT` — prompt structuré JSON (EN) pour Claude Vision
  - `parse_vision_response` — parseur 3 tentatives (direct, markdown fence, regex)
  - `build_mock_analysis` — mock déterministe pour développement/CI

- **`app/services/vision_service.py`** — Analyse photo asynchrone :
  - `analyze_photo_background` — BackgroundTask FastAPI : pending → analyzing → analyzed/failed
  - `_call_claude_vision` — appel réel Anthropic API (base64 + prompt structuré)
  - Toggle `CLAUDE_VISION_MOCK_MODE` pour CI sans API key

#### Endpoints API
- **`app/api/v1/endpoints/nutrition.py`** — Module nutrition complet :
  - `GET /food-items` — recherche floue + filtrage food_group
  - `GET /food-items/{id}` — détail aliment
  - `POST /nutrition/entries` — création (3 modes : food_item, photo, macros directes)
  - `GET /nutrition/entries` — liste avec filtre date + pagination
  - `GET /nutrition/entries/{id}` — détail
  - `PATCH /nutrition/entries/{id}` — mise à jour partielle
  - `DELETE /nutrition/entries/{id}` — soft-delete → 204
  - `GET /nutrition/daily-summary` — résumé journalier complet
  - `POST /nutrition/photos` — upload + analyse IA asynchrone
  - `GET /nutrition/photos/{id}` — polling statut analyse
  - `POST /nutrition/photos/{id}/confirm` — confirmation + création entrée

- **`app/api/v1/endpoints/scores.py`** — Scores persistants :
  - `GET /scores/readiness/today` — score du jour (404 si non calculé)
  - `GET /scores/readiness/history` — historique N jours (1-365)

#### Intégration dashboard
- **`app/services/dashboard_service.py`** — `build_dashboard()` appelle `compute_and_persist_readiness()` (lazy import pour éviter dépendance circulaire). Fallback silencieux vers `compute_recovery_score_v1` si la persistance échoue.

#### Tests
- **`tests/test_nutrition_service.py`** — 33 tests unitaires (macros, fenêtre alimentaire, complétude, schémas)
- **`tests/test_vision_service.py`** — 20 tests unitaires (mock analysis, parse, populate, prompt)
- **`tests/test_readiness_service.py`** — 19 tests unitaires (freshness, score computation, mapping)
- **`tests/integration/`** — Structure tests d'intégration PostgreSQL :
  - `conftest_pg.py` — fixtures engine/session/client, skip auto si `SOMA_TEST_DATABASE_URL` absent
  - `test_auth_flow.py` — flux complet register → login → refresh → protected
  - `test_nutrition_integration.py` — CRUD entrées, résumé, pipeline photo, isolation ownership
  - `test_readiness_integration.py` — persistance via dashboard, freshness, historique, isolation

### Modifié
- **`app/models/nutrition.py`** — `NutritionEntry` : +`meal_name`, +`is_deleted`, +`updated_at` ; `NutritionPhoto` : +`file_size_bytes`, +`mime_type`, +`entry_id`, +`is_deleted`, +`updated_at`
- **`app/api/v1/router.py`** — +`food_router`, +`entries_router`, +`summary_router`, +`photos_router`, +`scores_router`

### Compteur tests
- **171 tests unitaires ✅** (99 LOT 0/1 + 72 LOT 2)
- **Tests d'intégration** : structure créée, nécessitent `SOMA_TEST_DATABASE_URL`

---

## [0.2.0] — 2026-03-07 — LOT 1 : Dashboard + Module Sport

### Créé

#### Migration base de données
- **`app/db/migrations/versions/V001_initial_schema.py`** — Migration Alembic complète
  - 20 tables créées dans le bon ordre de dépendance FK
  - Extensions PostgreSQL : `uuid-ossp`, `pg_trgm`, `pgcrypto`
  - Champs ajoutés sur `workout_sessions` : `status`, `is_deleted`
  - Champs ajoutés sur `exercise_library` : `slug`, `subcategory`, `format_type`, `rep_detection_model`
  - Soft delete sur `workout_exercises` et `workout_sets`

#### Dashboard journalier — GET /api/v1/dashboard/today
- **`app/services/dashboard_service.py`** — Service d'agrégation journalière :
  - `build_weight_summary` — dernier poids, delta 7j, BMI, écart au goal
  - `build_hydration_summary` — volume du jour vs objectif dynamique
  - `build_sleep_summary` — nuit précédente (fenêtre hier 12h → aujourd'hui 12h)
  - `build_activity_summary` — health_samples + séance du jour
  - `build_nutrition_summary` — calories, protéines, balance énergétique, détection jeûne
  - `compute_recovery_score_v1` — score pondéré : sommeil 40%, HRV 20%, FC repos 20%, charge 20%
  - `generate_alerts` — alertes hydratation / sommeil / récupération / nutrition
  - `generate_recommendations` — recommandations priorisées (séance, protéines, hydratation, pas)
- **`app/schemas/dashboard.py`** — Schémas Pydantic complets (DashboardResponse, 6 sections + méta)
- **`app/api/v1/endpoints/dashboard.py`** — Endpoint `GET /api/v1/dashboard/today?date=YYYY-MM-DD`

#### Module Sport (Module G)
- **`app/schemas/workout.py`** — Schémas complets :
  - `SessionCreate/Update/Response/DetailResponse/ListResponse`
  - `ExerciseEntryCreate/Update/Response` (avec champs calculés : tonnage, total_sets, total_reps)
  - `SetCreate/Update/Response`
  - `SessionSummary`, `MuscleGroupVolume`
  - `ExerciseResponse`, `ExerciseListResponse`
- **`app/services/workout_service.py`** — Service métier :
  - `create_session / get_session / list_sessions / update_session / delete_session`
  - `get_session_detail` — session avec exercices et séries imbriqués
  - `add_exercise_to_session / update_exercise_entry / remove_exercise_from_session`
  - `add_set / update_set / delete_set` — avec détection PR automatique (formule d'Epley)
  - `_recalculate_session_totals` — recalcul tonnage/sets/reps/charge interne après chaque set
  - `get_session_summary` — tonnage, volume par groupe musculaire, PRs, summary_text
  - `list_exercises` — bibliothèque avec filtres (catégorie, difficulté, recherche textuelle)
- **`app/api/v1/endpoints/workouts.py`** — 14 endpoints :
  - `GET /exercises` + `GET /exercises/{id}`
  - `POST/GET/GET{id}/PATCH/DELETE /sessions`
  - `GET /sessions/{id}/summary`
  - `POST/PATCH/DELETE /sessions/{id}/exercises/{ex_id}`
  - `POST/PATCH/DELETE /sessions/{id}/exercises/{ex_id}/sets/{set_id}`

#### Seed data
- **`data/exercises_seed.json`** — 55 exercices couvrant :
  - Musculation libre (squat, deadlift, bench, OHP, row, pull-up, dip, hip thrust…)
  - Isolation (curl, tricep pushdown, lateral raise, fly, leg curl, calf raise…)
  - Cardio (marche, marche nordique, elliptique, course, vélo, natation, rameur, corde)
  - HIIT (burpee, mountain climber, box jump, kettlebell swing)
  - Mobilité / core (plank, side plank, dead bug, russian twist, world's greatest stretch…)
  - Yoga (salutation au soleil)
- **`scripts/seed_exercises.py`** — Script idempotent (upsert par slug), compatible `.env`

#### Tests
- **`tests/test_dashboard.py`** — 35 tests :
  - `_day_bounds` (bornes UTC, années bissextiles)
  - `compute_recovery_score_v1` (toutes composantes, cas limites, intensités recommandées)
  - `generate_alerts` (hydratation, sommeil, récupération, nutrition)
  - `generate_recommendations` (séance, protéines, hydratation, pas, tri par priorité)
  - Schémas dashboard (sommeil sans données, hydratation pct/status)
- **`tests/test_workout.py`** — 33 tests :
  - `_compute_tonnage` (warmup exclus, deleted exclus, None exclus, mixed weights)
  - Schémas `SessionCreate/Update` (validation status, location, RPE bounds)
  - Schémas `SetCreate` (validation set_number, weight, RPE, data_source)
  - `ExerciseEntryResponse` (computed fields tonnage, total_sets, total_reps)
  - `SessionSummary`, `MuscleGroupVolume`
  - Formule d'Epley (1RM estimé)
  - `ExerciseResponse`, `ExerciseListResponse`

#### Infrastructure
- **`app/api/v1/router.py`** — Mis à jour avec dashboard_router, exercises_router, sessions_router
- **`app/db/migrations/script.py.mako`** — Template Alembic

### Modifié
- **`app/models/workout.py`** — Ajout `status`, `is_deleted` sur `WorkoutSession` ; `is_deleted` sur `WorkoutExercise` et `WorkoutSet` ; `slug`, `subcategory`, `format_type`, `rep_detection_model` sur `ExerciseLibrary` ; relations soft-delete avec `primaryjoin`
- **`app/schemas/user.py`** — Migration vers Pydantic v2 `ConfigDict` (dépréciation `class Config`)
- **`tests/test_calculations.py`** — Mis à jour (31 tests → tous passent)

### Statistiques tests
- **99 tests** au total — **99 passent** ✅ — 0 échec

### À faire ensuite (LOT 2)
- Endpoints CRUD workout sessions (integration tests avec PostgreSQL)
- Module nutrition : journal alimentaire + analyse photo (Claude API)
- Score de récupération stocké (vs calculé à la volée)
- Jumeau métabolique (snapshot quotidien)

---

## [0.1.0] — 2026-03-07 — LOT 0/1 : Fondations backend

### Créé
- Structure monorepo complète (backend/, mobile/, services/, docs/, docker/)
- **Documentation**: ARCHITECTURE.md, DATA_MODEL.md, ROADMAP.md, RISKS.md, API_CONTRACTS.md
- **Docker**: docker-compose.yml (PostgreSQL 15 + Redis 7)
- **Backend FastAPI**:
  - `app/main.py` — Application principale avec middleware CORS, logging
  - `app/core/config.py` — Settings pydantic-settings
  - `app/core/security.py` — JWT (access + refresh tokens), bcrypt
  - `app/core/deps.py` — Dependency injection (get_current_user)
  - `app/db/base.py` — Base SQLAlchemy + mixins UUID/Timestamp
  - `app/db/session.py` — AsyncSession factory
  - `app/db/migrations/env.py` — Alembic configuration async
- **Modèles SQLAlchemy** (5 modules, 15+ tables):
  - `models/user.py` — User, UserProfile, BodyMetric
  - `models/health.py` — HealthDataSource, HealthImportJob, HealthSample, SleepSession, HydrationLog
  - `models/workout.py` — ExerciseLibrary, WorkoutSession, WorkoutExercise, WorkoutSet
  - `models/nutrition.py` — FoodItem, NutritionPhoto, NutritionEntry, SupplementRecommendation
  - `models/scores.py` — MetabolicStateSnapshot, ReadinessScore, LongevityScore, DailyRecommendation
- **Endpoints API**:
  - `POST /auth/register` — Inscription + création profil vide
  - `POST /auth/login` — Authentification JWT
  - `POST /auth/refresh` — Renouvellement token
  - `GET/PUT /api/v1/profile` — Profil complet avec métriques calculées
  - `POST/GET /api/v1/body-metrics` — Métriques corporelles + tendance poids
  - `POST /api/v1/health/sync` — Import données santé (async)
  - `GET /api/v1/health/summary` — Résumé métriques journalières
  - `POST /api/v1/health/samples` — Ajout manuel données santé
  - `POST/GET /api/v1/sleep` — Journal sommeil
  - `POST /api/v1/hydration/log` — Log hydratation
  - `GET /api/v1/hydration/today` — Résumé hydratation journalier
- **Service calculs physiologiques** (`services/calculations.py`):
  - BMR: formule Mifflin-St Jeor + Katch-McArdle
  - TDEE: multiplicateurs d'activité
  - IMC + catégorisation
  - Besoins protéiques selon objectif (ISSN guidelines)
  - Objectif calorique adaptatif
  - Objectif hydratation
  - Score complétude profil
  - Charge d'entraînement (Session RPE method)
  - ACWR (ratio aigu/chronique)
- **Tests unitaires** (`tests/test_calculations.py`):
  - 25 tests couvrant tous les calculs physiologiques

### À faire ensuite (LOT 1 suite)
- Migration Alembic V001
- Tests intégration auth
- Seed data exercices
- Dashboard endpoint
