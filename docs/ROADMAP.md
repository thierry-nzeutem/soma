# SOMA — Roadmap de Développement

## LOT 0 — Fondations ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Structure du projet, tooling, infrastructure locale

### Livrables
- [x] Structure monorepo
- [x] Documents de cadrage (ARCHITECTURE, DATA_MODEL, ROADMAP, RISKS)
- [x] Docker Compose (PostgreSQL 15 + Redis 7)
- [x] Backend FastAPI skeleton
- [x] Migrations Alembic (tables core)
- [x] Tests infrastructure (pytest)

---

## LOT 1 — Backend Core + Auth + Profil ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Base fonctionnelle du backend avec authentification et profil utilisateur

### Module A — Profil utilisateur
- [x] Modèles SQLAlchemy: `users`, `user_profiles`, `body_metrics`
- [x] Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- [x] Endpoints: `GET/PUT /api/v1/profile`
- [x] Endpoints: `POST /api/v1/body-metrics`
- [x] Service: calcul BMI, BMR (Mifflin-St Jeor), TDEE, besoins protéines, hydratation
- [x] Tests unitaires: calculs physiologiques (31 tests)
- [x] Dashboard journalier `GET /api/v1/dashboard/today`
- [x] Module Sport : sessions, exercices, séries (55 exercices seed)

---

## LOT 2 — Health Sync + Nutrition + Scores ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Connexion sources de données santé + nutrition + scores persistants

### Module B — Intégrations santé
- [x] Modèles: `health_data_sources`, `health_import_jobs`, `health_samples`
- [x] Endpoints: `POST /api/v1/health/sync`, `GET /api/v1/health/summary`
- [x] Service: normalisation unités, déduplication

### Module H/I — Nutrition
- [x] Modèles: `food_items`, `nutrition_photos`, `nutrition_entries`
- [x] Endpoints: CRUD journal, résumé journalier, upload photo, analyse Claude Vision
- [x] Pipeline: photo → analyse IA → confirmation → entrée

### Module N — Sommeil & Récupération
- [x] Modèles: `sleep_sessions`, `readiness_scores`
- [x] Score récupération persistant avec freshness check
- [x] Endpoints: log sommeil, score du jour, historique

---

## LOT 3 — Health Intelligence Engine ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Moteurs d'intelligence santé (7 modules)

### ✅ Module J — Moteur nutritionnel (nutrition_engine.py)
- [x] Calcul besoins journaliers adaptatifs (BMR → TDEE → bonus entraînement → objectif)
- [x] Répartition macros cohérente (protéines → lipides → glucides résiduels)
- [x] Support jeûne intermittent (fenêtre de consommation + heure début jeûne)
- [x] Cibles fibres (14g/1000 kcal, IOM) + hydratation (33ml/kg + activité)
- [x] Endpoint `GET /nutrition/targets`

### ✅ Module K — Micronutrition (micronutrient_engine.py)
- [x] Suivi 8 micronutriments (vitamine D, magnésium, potassium, sodium, calcium, fer, zinc, oméga-3)
- [x] Source primaire : données JSONB du catalogue alimentaire
- [x] Fallback : estimation par groupe alimentaire
- [x] Score micronutritionnel global (0-100), détection déficits
- [x] Endpoint `GET /nutrition/micronutrients`

### ✅ Module L — Complémentation (supplement_engine.py)
- [x] Règles métier pour vitamine D, magnésium, créatine, protéines, fer
- [x] Recommandations triées par confiance (high/medium/low), basées sur données réelles
- [x] Endpoint `GET /nutrition/supplements/recommendations`

### ✅ Agrégateur métriques quotidiennes (daily_metrics_service.py)
- [x] Modèle `daily_metrics` : 21 champs, snapshot toutes sources
- [x] Upsert avec cache 2h (évite recalcul inutile)
- [x] Historique N jours avec tendances (readiness, sommeil, calories, pas, protéines, poids, fréquence entraînement)
- [x] Endpoints `GET /metrics/daily`, `GET /metrics/history`

### ✅ Module R — Insight Engine (insight_engine.py)
- [x] 7 règles de détection (protéines, calories, activité, fatigue, sommeil, hydratation, surentraînement ACWR)
- [x] Modèle `insights` avec catégorie, sévérité, evidence JSONB, expiration 7j
- [x] Upsert par contrainte unique (user + catégorie + période)
- [x] Endpoints `GET /insights`, `POST /insights/run`, `PATCH /insights/{id}/read|dismiss`

### ✅ Plan santé journalier (health_plan_service.py)
- [x] Morning briefing : séance recommandée, cibles nutritionnelles, alertes, conseils du jour
- [x] Adaptation selon score de récupération, équipement, objectif
- [x] Fenêtre alimentaire IF, focus nutritionnel
- [x] Endpoint `GET /health/plan/today`

### ✅ Module Q — Score longévité (longevity_engine.py)
- [x] 7 composantes : cardio, force, sommeil, nutrition, poids, composition corporelle, consistance
- [x] Âge biologique estimé, leviers d'amélioration, niveau de confiance
- [x] Endpoint `GET /scores/longevity`

### Tests LOT 3
- [x] 218 tests unitaires (tous passent ✅)
- [x] Couverture : 6 fichiers test, tous les moteurs purs

---

## LOT 4 — Scheduler + Tests intégration + Mobile MVP ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Automatisation + qualité + première app mobile

### Scheduler (LOT 4A) ✅
- [x] APScheduler AsyncIOScheduler — pipeline quotidien 5h30 Europe/Paris
- [x] Pipeline 5 étapes : DailyMetrics → Readiness → Insights → HealthPlan → Longevity
- [x] Isolation par step (erreur = log + continue) et par user (commit après chaque user)
- [x] Fallback lazy computation : `lazy_ensure_today_metrics()` dans 3 endpoints critiques
- [x] Intégration lifespan FastAPI (`main.py`) : start au démarrage, shutdown propre

### Tests scheduler (LOT 4A) ✅
- [x] 33 tests unitaires scheduler (tous passent ✅) — `tests/test_scheduler.py`
  - TestRunStep (6), TestRunDailyPipelineForUser (8), TestDailyPipelineAllUsers (5)
  - TestLazyEnsureTodayMetrics (6), TestCreateScheduler (8)
- [x] **Total général : 422 tests passent, 3 skipped**

### Tests intégration (LOT 4B)
- [ ] Tests PostgreSQL réels : metrics pipeline, insight upsert, longevity endpoint
- [ ] Tests intégration nutrition : targets, micronutriments, suppléments
- [ ] Coverage > 80% backend

### Mobile Flutter MVP (LOT 4C) ✅
- [x] Structure projet Flutter créée manuellement (`mobile/`)
- [x] `pubspec.yaml` : flutter_riverpod 2.5, go_router 13, dio 5, fl_chart 0.67
- [x] Architecture feature-first : core/ + features/ + shared/
- [x] Modèles Dart : `DailyMetrics`, `DailyHealthPlan`, `LongevityScore`
- [x] Client HTTP `ApiClient` (Dio + intercepteur JWT + auto-refresh)
- [x] `ApiConstants` — tous les endpoints centralisés
- [x] 3 écrans fonctionnels consommant l'API :
  - **Dashboard** : 8 MetricCards (poids, calories, protéines, hydratation, pas, sommeil, HRV, séances)
  - **Health Plan** : récupération, séance du jour, macros, fenêtre IF, conseils, alertes
  - **Longevity** : ScoreRing global, 7 composantes, leviers d'amélioration
- [x] Widgets partagés : `SomaAppBar`, `MetricCard`, `ScoreRing` (CustomPainter)
- [x] Navigation GoRouter (ShellRoute + BottomNavigationBar 3 onglets)
- [x] Design system dark : fond #0A0A0A, accent #00E5A0 (vert menthe)

---

## LOT 5 — Stabilisation + Mobile MVP Extended ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Qualité production-interne + mobile complet de base

### Backend — Stabilisation (LOT 5A) ✅
- [x] `algorithm_version` sur DailyMetrics, ReadinessScore, LongevityScore (migration V004)
- [x] Persistance Health Plan dans `DailyRecommendation` (cache 6h, `from_cache` flag dans réponse)
- [x] Endpoint `GET /home/summary` (agrège métriques + readiness + insights + plan + longevity en 1 appel)
- [x] 3 nouveaux fichiers tests intégration PostgreSQL (daily_metrics, insights, longevity)
- [x] Bug fix : `ReadinessScore.updated_at` manquant dans modèle SQLAlchemy (présent en DB depuis V002)

### Mobile Flutter — Complétion MVP (LOT 5B) ✅
- [x] Auth : écran login, SharedPreferences token, redirect GoRouter, logout
- [x] Insights : 4ème onglet, liste filtrée (all/unread/warning/critical), mark read / dismiss
- [x] Hardening : AppConfig dev/prod, gestion erreurs structurée (ApiError), loading skeleton animé

---

## LOT 6 — Mobile Features Complètes ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Mobile parité fonctionnelle avec les endpoints backend existants

### Modèles & API ✅
- [x] `core/models/nutrition.dart` — FoodItem, NutritionEntry, MacroTotals, MacroGoals, DailyNutritionSummary, DetectedFood, NutritionPhoto
- [x] `core/models/workout.dart` — ExerciseLibrary, WorkoutSet, ExerciseEntry, WorkoutSession
- [x] `core/models/hydration.dart` — HydrationLog, HydrationSummary
- [x] `core/models/sleep_log.dart` — SleepSession
- [x] `core/models/profile.dart` — ComputedMetrics, UserProfile
- [x] `ApiClient` : méthodes `delete<T>()` et `postFile<T>()` (FormData multipart)
- [x] `ApiConstants` : 10 nouveaux endpoints (foodItems, nutritionEntries, sessions, exercises, hydrationLog/Today, sleepLog, bodyMetrics, nutritionDailySummary, nutritionPhotos)

### Notifiers Riverpod ✅
- [x] `NutritionSummaryNotifier` — résumé journalier + CRUD (addEntry / deleteEntry)
- [x] `FoodSearchNotifier` — recherche aliments côté serveur, StateNotifier.autoDispose
- [x] `PhotoAnalysisNotifier` — upload + polling IA (max 30s, toutes les 2s)
- [x] `WorkoutSessionsNotifier` — liste sessions + createSession + completeSession
- [x] `sessionDetailProvider` — FutureProvider.autoDispose.family par sessionId
- [x] `ExercisesNotifier` — bibliothèque d'exercices en cache + filtre local
- [x] `HydrationNotifier` — résumé du jour + addEntry
- [x] `SleepNotifier` — sessions récentes + logSleep
- [x] `ProfileNotifier` — profil complet + update (PATCH partiel)
- [x] `MetricsHistoryNotifier` — historique avec sélecteur de période (7/30/90 jours)

### Journal alimentaire ✅
- [x] `NutritionHomeScreen` — résumé macros, barre calories, liste par repas, suppression
- [x] `NutritionEntryFormScreen` — saisie manuelle + type repas + bouton recherche + bouton photo
- [x] `FoodSearchScreen` — recherche temps réel, sélection aliment retournée via pop
- [x] `PhotoReviewScreen` — polling analyse IA, confidence bar, aliments détectés, enregistrement

### Journal entraînement ✅
- [x] `WorkoutSessionsScreen` — liste sessions, badges statut, pull-to-refresh, FAB
- [x] `WorkoutSessionCreateScreen` — grid type séance, lieu, date/heure picker
- [x] `WorkoutSessionDetailScreen` — exercices + séries + bouton +série (dialog) + compléter
- [x] `ExercisePickerScreen` — bibliothèque searchable, cache client, retour via pop

### Journal hub & Saisies simples ✅
- [x] `JournalHubScreen` — 4 cartes (Nutrition, Entraînement, Hydratation, Sommeil)
- [x] `HydrationScreen` — anneau de progression, boutons rapides +250/500/750/1000 ml
- [x] `SleepScreen` — time pickers coucher/réveil, sélecteur qualité ★ 1-5, historique
- [x] `SettingsScreen` — version app, serveur, lien profil, déconnexion confirmée

### Profil & Historique ✅
- [x] `ProfileScreen` — avatar, informations, métriques calculées, liens rapides
- [x] `EditProfileScreen` — formulaire PATCH (prénom, poids, régime, IF, repas/jour)
- [x] `MetricsHistoryScreen` — 5 graphiques fl_chart (poids, calories, protéines, hydratation, HRV), sélecteur période

### Navigation & Architecture ✅
- [x] `main.dart` restructuré : 5 onglets (Dashboard | Journal | Plan | Insights | Profil)
- [x] Sous-routes hors ShellRoute pour les écrans de saisie (plein écran, bouton retour)
- [x] Routes GoRouter pour toutes les nouvelles fonctionnalités
- [x] `image_picker: ^1.1.2` ajouté à pubspec.yaml

### Tests Flutter ✅
- [x] `test/models/nutrition_model_test.dart` — 18 tests (FoodItem, NutritionEntry, MacroTotals, DailyNutritionSummary, NutritionPhoto)
- [x] `test/models/workout_model_test.dart` — 17 tests (ExerciseLibrary, WorkoutSet, ExerciseEntry, WorkoutSession)
- [x] `test/models/profile_model_test.dart` — 18 tests (UserProfile, ComputedMetrics, HydrationSummary, HydrationLog, SleepSession)

---

## LOT 7 — Computer Vision V1 ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Analyse vidéo exercices en temps réel — 100% on-device (ML Kit Pose Detection)

### Architecture retenue : traitement local sur le device mobile

| Décision | Choix LOT 7 | Raison |
|---|---|---|
| Moteur CV | ML Kit Pose Detection (`google_mlkit_pose_detection`) | Gratuit, on-device, 33 landmarks, pas de latence réseau |
| Backend | Minimal (résumé JSON seulement) | Aucune vidéo transmise — respect vie privée + bande passante |
| Traitement | Dart pur (AngleCalculator, RepCounter, QualityScorer) | Testable sans plateforme, performances suffisantes |
| Comptage | Automates finis par exercice (FSM) | Robuste, déterministe, facilement extensible |

### Module F — Comptage répétitions ✅
- [x] `AngleCalculator` — angles articulaires 2D (genou, coude, tronc-hanche, alignement corps, ratios jumping jack)
- [x] `RepCounter` — 6 automates finis : squat (155°/115°), push-up (150°/90°), plank (timer 300 frames), jumping jack (ratio 0.5/0.3), lunge (155°/110°), sit-up (70°/40°)
- [x] `PoseDetectorService` — pont ML Kit : CameraImage (NV21/BGRA8888) → DetectedPose normalisé [0,1]
- [x] `VisionNotifier` — orchestration Riverpod : initialisation caméra, traitement frame throttlé, cycle de vie complet

### Module P — Score biomécanique ✅
- [x] `QualityScorer` — 3 dimensions : amplitude (angle atteint vs référence), stabilité (alignement corps), régularité (intervalles inter-rep)
- [x] Pondération 40/35/25 → score global 0–100
- [x] Labels : Excellent ≥80, Bon ≥65, Correct ≥50, À améliorer ≥35, Insuffisant <35
- [x] `ExerciseClassifier` — validation position initiale (couverture, landmarks requis, vue caméra)
- [x] Recommandations contextuelles selon scores en écran résumé

### Screens & Widgets ✅
- [x] `VisionExerciseSetupScreen` — sélection exercice + guide positionnement
- [x] `VisionWorkoutScreen` — preview caméra + overlay squelette + compteur + contrôles
- [x] `VisionSessionSummaryScreen` — résumé + scores + sauvegarde API
- [x] `PoseOverlayPainter` — 12 connexions osseuses + 12 articulations (CustomPainter)
- [x] `RepCounterWidget` — animé (AnimatedSwitcher + ScaleTransition)
- [x] `QualityScoreWidget` — anneau de score CustomPainter

### Backend ✅
- [x] Migration V005 : table `vision_sessions` (exercice, reps, durée, 4 scores, metadata JSONB)
- [x] `POST /vision/sessions` — enregistrement résumé session
- [x] `GET /vision/sessions` — historique filtrable (exercice, date, limit)
- [x] Schéma Pydantic avec validation `exercise_type` contre ensemble autorisé

### Tests LOT 7 ✅
- [x] `test/vision/angle_calculator_test.dart` — 8 tests angles
- [x] `test/vision/rep_counter_test.dart` — 36 tests FSM (cycles, peak tracking, reset, factory)
- [x] `test/vision/quality_scorer_test.dart` — 18 tests (amplitude, stabilité, régularité, sync)
- [x] `test/vision/vision_session_model_test.dart` — 28 tests (construction, JSON, labels)
- [x] `test/vision/exercise_classifier_test.dart` — 14 tests (couverture, vue, landmarks)
- [x] `backend/tests/test_vision.py` — 28 tests (schémas Pydantic, validation, response)

### Limites connues (LOT 8+)
- [x] Bug `toJson()` : Jumping Jack → "jumping jack" ~~au lieu de "jumping_jack"~~ — **RÉSOLU LOT 8** (regex `[-\s]`)
- [x] Pas d'historique visuel des sessions CV dans l'app — **RÉSOLU LOT 8** (VisionHistoryScreen)
- [x] Feedback temps réel limité au positionnement — **RÉSOLU LOT 8** (tips coaching par phase)
- [ ] Tests d'intégration caméra réelle non réalisés (mock ML Kit uniquement)
- [ ] Feedback profondeur avancé (heatmap, flèches directionnelles)

---

## LOT 8 — Vision Integration + History + Hardening ✅ COMPLÉTÉ (2026-03-07)
**Objectif**: Stabilisation CV, historique sessions, intégration workout, feedback V2

### Bugfix critique
- [x] `vision_session.dart` toJson/fromJson : regex `[-\s]` → "jumping_jack" correct
- [x] Fallback `created_at` si `started_at` absent (compatibilité backend)

### Historique Vision
- [x] `vision_history_notifier.dart` — StateNotifier avec filtres période (7/30/90j) + exercice
- [x] `vision_history_screen.dart` — Liste + graphique progression fl_chart + chips filtres
- [x] `vision_session_history_detail_screen.dart` — Détail read-only avec métadonnées

### Intégration Workout
- [x] `workout_session_detail_screen.dart` — Bouton "Analyser avec CV" si session en cours

### Feedback V2
- [x] `vision_workout_screen.dart` — `_PhaseTip` : 20 tips coaching par (exercice, phase)
- [x] `vision_exercise_setup_screen.dart` — Bouton "Historique" dans AppBar

### Tests LOT 8
- [x] `test/vision/vision_session_model_test.dart` — +15 tests bugfix JumpingJack (toJson × 6, fromJson, round-trip × 6, created_at fallback)
- [x] `test/vision/vision_history_notifier_test.dart` — 20 tests (enum, toApiKey × 6, state, copyWith, parsing JSON)

---

## LOT 9 — IA Conversationnelle + Jumeau Métabolique ✅ COMPLÉTÉ (2026-03-08)
**Objectif**: Intelligence adaptative et prédictive

### Module O — Jumeau métabolique ✅
- [x] Service multi-signal (sommeil + sport + nutrition + HRV) — `metabolic_twin_service.py`
- [x] BMR Mifflin-St Jeor + TDEE dynamique (5 niveaux d'activité)
- [x] Estimation glycogène (15g/kg, 4 statuts), fatigue accumulée (0–100), disponibilité énergétique
- [x] Détection plateau (écart-type poids + calories sur 14j)
- [x] Âge métabolique estimé (delta score longévité)
- [x] Persistence upsert `metabolic_state_snapshots` (V006)

### Module R+ — Coach IA Claude API ✅
- [x] `claude_client.py` — wrapper `anthropic.AsyncAnthropic` avec mock mode (CLAUDE_COACH_MOCK_MODE)
- [x] `coach_service.py` — `ask_coach()` flow complet : contexte → Claude → parsing → persistance
- [x] `context_builder.py` — assemblage contexte ≤1500 tokens (8 sections physiologiques)
- [x] Q&A santé personnalisé avec historique de conversation (10 échanges window)
- [x] Morning briefing IA généré lors de `GET /health/plan/today` (non-bloquant)
- [x] Persistance dans `conversation_threads` + `conversation_messages` (V006)

### Module S — Détection stagnation (partiel) ✅
- [x] Détection plateau poids/calories (14 jours, écart-type poids <0.5 kg et cal <200 kcal)
- [ ] Détection plateau performance (progression séances) — LOT 10
- [ ] Propositions adaptation programme (périodisation) — LOT 10

### Module T — Prédictions physiologiques (partiel)
- [ ] Estimation glycémie proxy (HRV + nutrition + activité) — LOT 10
- [ ] Score risque blessure (ACWR avancé + données biomécanique) — LOT 10
- [ ] Optimisation zone 2 cardio personnalisée — LOT 10

### Tests LOT 9 ✅
- [x] `tests/test_metabolic_twin.py` — 43 tests unitaires (9 classes, purs sans DB)
- [x] `tests/test_context_builder.py` — 28 tests (to_prompt_text, sections, troncature)
- [x] `tests/test_coach_service.py` — 33 tests (parsing, mock reply, CRUD, ask_coach flow)
- [x] `tests/test_coach_api.py` — 25 tests API (4 endpoints, isolation user, validation)
- [x] Total backend : **~551 tests** (422 précédents + 129 nouveaux)

---

## LOT 10 — Predictive Health Engine ✅ COMPLÉTÉ (2026-03-08)
**Objectif**: Rendre SOMA prédictif — 3 moteurs déterministes, testables, indépendants du LLM

### Module T+ — InjuryRiskEngine ✅
- [x] `injury_risk_engine.py` — `InjuryRiskResult` dataclass + 5 fonctions pures
- [x] `_compute_acwr()` : ACWR = charge_7j / (charge_28j / 4)
- [x] `_score_acwr_risk()` : zones de risque (safe 0.8–1.3, warning >1.5, critical >2.0)
- [x] `_score_fatigue_risk()` : score fatigue 0–100 → risque blessure
- [x] `_score_biomechanics_risk()` : qualité mouvement (VisionSessions) inversée en risque
- [x] `_score_readiness_risk()` : readiness faible = récupération incomplète = risque élevé
- [x] Pondération ACWR 35% / Fatigue 25% / Biomécanique 25% / Readiness 15%
- [x] Niveaux : low (<25) / moderate (25–49) / high (50–74) / critical (≥75)
- [x] Recommandations contextualisées selon risk_area et risk_level

### Module T+ — OvertrainingEngine ✅
- [x] `overtraining_engine.py` — `OvertrainingResult` dataclass + 4 fonctions pures
- [x] `_compute_acwr()` : normalisation hebdomadaire de la charge chronique
- [x] `_acwr_zone()` : 5 zones (undertraining / optimal / moderate_risk / high_risk / overreaching)
- [x] `_score_wellbeing()` : score combiné sommeil + fatigue
- [x] Pondération ACWR 40% / Bien-être 35% / Readiness 25%
- [x] Recommandation principale contextualisée par zone ACWR

### Module T+ — WeightPredictionEngine ✅
- [x] `weight_prediction_engine.py` — `WeightPredictionResult` dataclass + 3 fonctions pures
- [x] `_compute_tdee()` : préfère TDEE MetabolicTwin, fallback active_calories
- [x] `_compute_delta_kg()` : modèle linéaire delta = balance × jours × adaptation / 7700
- [x] Facteurs d'adaptation : 1.0 (7j) / 0.90 (14j) / 0.80 (30j) — adaptation métabolique progressive
- [x] `_trend_direction()` : loss / gain / stable (seuil ±300g/sem)
- [x] Hypothèses du modèle exposées pour transparence

### API Endpoints ✅
- [x] `schemas/predictions.py` — 4 schémas Pydantic v2 : InjuryRiskResponse, OvertrainingResponse, WeightPredictionResponse, HealthPredictionsResponse
- [x] `GET /health/predictions` — 3 prédictions combinées en 1 appel
- [x] `GET /health/injury-risk` — risque de blessure seul
- [x] `GET /health/overtraining` — risque de surentraînement seul
- [x] Helper `_load_all_inputs()` : charge MetabolicStateSnapshot + ReadinessScore + DailyMetrics(7j) + VisionSessions(7j)

### Tests LOT 10 ✅
- [x] `tests/test_injury_risk_engine.py` — 47 tests purs (6 classes)
- [x] `tests/test_overtraining_engine.py` — 38 tests purs (5 classes)
- [x] `tests/test_weight_prediction_engine.py` — 33 tests purs (4 classes)
- [x] **Total : 118 nouveaux tests — 118/118 ✅**
- [x] Suite totale backend : **~669 tests** (~551 précédents + 118 nouveaux)

---

## LOT 11 — Advanced Intelligence + Scale-Ready Architecture ✅ COMPLÉTÉ (2026-03-08)
**Objectif**: SOMA physiologiquement intelligent — 4 moteurs avancés + infrastructure scalable

### Infrastructure Scale-Ready ✅
- [x] `app/cache/` — CacheService Redis async, graceful degradation, TTLs configurés (Twin 4h, Bio Age 24h, Adaptive Nutrition/Motion 6h)
- [x] `app/events/` — EventBus asyncio in-process (subscribe/publish/dispatch), 9 types d'événements
- [x] `app/storage/` — StorageService abstrait + LocalStorage (interface S3 pour LOT 12)
- [x] `app/observability/` — setup_logging() DevFormatter + JsonFormatter (request_id)

### Module B — Digital Twin V2 ✅
- [x] `app/domains/twin/service.py` — 12 composantes physiologiques + `TwinComponent` (value, status, confidence, explanation, variables_used) — explainabilité totale
- [x] Formules : inflammation (fatigue + sleep_debt + ACWR), sleep_debt (7j), metabolic_flexibility (consistency + IF + plateau)
- [x] `DigitalTwinSnapshot` table (JSONB components), cache 4h, 3 endpoints

### Module C — Biological Age Engine ✅
- [x] `app/domains/biological_age/service.py` — 7 composantes pondérées, formule `bio_age = chrono + Σ(weight × (75-score) × 0.2)`, clampé ±15 ans
- [x] 7 `BiologicalAgeLever` sélectionnés si composante < 65, triés par potential_years_gained
- [x] `BiologicalAgeSnapshot` table, cache 24h, 3 endpoints

### Module D — Adaptive Nutrition Engine ✅
- [x] `app/domains/adaptive_nutrition/service.py` — stateless, `DayType` enum (5 types)
- [x] Règles protéines (1.6–2.2 g/kg) et glucides (2.5–5.5 g/kg) par type de journée
- [x] Logique fasting compatible (glycogène + fatigue + type journée), 3 endpoints

### Module E — Motion Intelligence Engine ✅
- [x] `app/domains/motion/service.py` — _trend() regression linéaire, asymmetry_score (std × 3)
- [x] movement_health = 0.4×stability + 0.4×mobility + 0.2×(100-asymmetry), profils par exercice
- [x] `MotionIntelligenceSnapshot` table, cache 6h, 3 endpoints

### Enrichissement Backend ✅
- [x] Scheduler 5 → 9 étapes (digital_twin, bio_age, motion_intelligence, adaptive_nutrition_log)
- [x] Context builder enrichi (+4 sections coach ≤5500 chars)
- [x] Migration V007 : 3 nouvelles tables + index composites

### Flutter LOT 11 ✅
- [x] 4 modèles Dart (digital_twin, biological_age, adaptive_nutrition, motion_intelligence)
- [x] 4 features complètes avec notifiers + screens (Jumeau, Âge Bio, Nutrition Adaptative, Motion)
- [x] 7 widgets partagés (glycogen_gauge, twin_component_card, biological_age_delta_card, longevity_lever_card, adaptive_macro_card, movement_health_ring, day_type_badge)
- [x] +7 routes GoRouter + +12 endpoints ApiConstants

### Tests LOT 11 ✅
- [x] ~200 nouveaux tests backend (digital_twin, bio_age, adaptive_nutrition, motion, cache, event_bus)
- [x] ~65 nouveaux tests Dart (4 fichiers modèles)
- [x] **Suite totale backend : ~870+ tests** | **Suite totale Dart : ~204+ tests**

---

## LOT 12 ✅ COMPLÉTÉ — Mobile Reliability & Daily Usage Excellence (2026-03-08)
**Objectif**: Cache local, connectivité offline, sync différée, notifications intelligentes, fiabilité quotidienne

### Module V — Notifications intelligentes
- [ ] Notifications contextuelles (insight critique, objectif atteint)
- [ ] Configuration per-type utilisateur
- [ ] Rappels adaptatifs (heure optimale selon habitudes)

### Module W — Rapports
- [ ] Rapport hebdomadaire auto-généré (PDF ou in-app)
- [ ] Rapport mensuel avec tendances
- [ ] Export données (CSV / JSON)

### Tests + Qualité
- [ ] Couverture backend > 80% (pytest-cov)
- [ ] Tests widget Flutter (golden tests)
- [ ] Tests end-to-end (Patrol ou integration_test)

### Performance & Déploiement
- [ ] Optimisation requêtes PostgreSQL (EXPLAIN ANALYZE)
- [ ] Cache Redis stratégique (scores populaires, nutrition targets)
- [ ] Configuration production (Docker Swarm ou Kubernetes)
- [ ] CI/CD pipeline (GitHub Actions)

---


## LOT 13 ✅ COMPLÉTÉ — Personalized Learning Engine (2026-03-08)
**Objectif**: Apprendre du comportement utilisateur pour personnaliser les recommandations

### Module Learning ✅
- [x] `app/domains/learning/service.py` — Estimation TDEE réel (bilan énergétique 7700 kcal/kg), efficacité métabolique (ratio TDEE_réel/Mifflin), profil récupération, tolérance entraînement, réponse nutritionnelle, récupération sommeil
- [x] 7 fonctions pures stateless, `UserLearningResult` dataclass, `build_learning_summary()` ≤200 chars
- [x] 3 endpoints : `GET /learning/profile`, `GET /learning/insights`, `POST /learning/recompute`
- [x] Flutter : `learning_profile.dart`, `LearningProfileNotifier`, `LearningProfileScreen`
- [x] ~30 tests purs backend (`tests/test_learning_engine.py`)

---

## LOT 14 ✅ COMPLÉTÉ — Coach Pro / Multi-Athletes Platform (2026-03-08)
**Objectif**: Plateforme multi-locataire pour coachs professionnels gérant plusieurs athlètes

### Module Coach Platform ✅
- [x] `app/domains/coach_platform/service.py` — 9 dataclasses (CoachProfile, AthleteProfile, CoachAthleteLink, AthleteDashboardSummary, TrainingProgram, ProgramWeek, ProgramWorkout, AthleteNote, AthleteAlert)
- [x] `_determine_risk_level()` (green/yellow/orange/red), `_generate_athlete_alerts()` (5 types), `compute_athlete_dashboard_summary()`
- [x] 9 endpoints `/coach-platform/*` : gestion coach, athlètes, programmes, notes, dashboard
- [x] Stores in-memory (prévus pour migration DB future)
- [x] ~20 tests purs backend (`tests/test_coach_platform.py`)

---

## LOT 15 ✅ COMPLÉTÉ — Injury Prevention Engine (2026-03-08)
**Objectif**: Prévention blessures par analyse composite multi-sources

### Module Injury ✅
- [x] `app/domains/injury/service.py` — Score composite : ACWR 30% + Fatigue 25% + Asymétrie 20% + Sommeil 15% + Monotonie 10% (Foster 1998)
- [x] Zones ACWR : critical >1.8, high >1.5, moderate >1.3 (Hulin 2016, Foster 2001)
- [x] Identification zones à risque corporelles, détection patterns de compensation, recommandations immédiates
- [x] 3 endpoints : `GET /injury/risk` (cache 4h), `GET /injury/history`, `GET /injury/recommendations`
- [x] Contexte coach : `build_injury_summary()` ≤200 chars
- [x] Flutter : `injury_risk.dart`, `InjuryRiskNotifier`, `InjuryRiskScreen` (anneau score + composantes)
- [x] ~35 tests purs backend (`tests/test_injury_prevention.py`)

---

## LOT 16 ✅ COMPLÉTÉ — Longevity Lab Biomarkers (2026-03-08)
**Objectif**: Intégration résultats biologiques et impact sur âge biologique

### Module Biomarkers ✅
- [x] `app/domains/biomarkers/service.py` — Références cliniques pour 14 marqueurs (OMS/standards cliniques)
- [x] Scores : `metabolic_health_score`, `inflammation_score`, `cardiovascular_risk`, `longevity_modifier` (= `(75-score)×0.2`, ±10 ans max)
- [x] Store in-memory `_lab_store` (migration DB prévue)
- [x] 4 endpoints : `POST /labs/result`, `GET /labs/results`, `GET /labs/analysis` (cache 24h), `GET /labs/longevity-impact`
- [x] Flutter : `biomarker.dart`, `BiomarkerAnalysisNotifier`
- [x] ~25 tests purs backend (`tests/test_biomarker_analysis.py`)

---

## LOT 17 ✅ COMPLÉTÉ — Product Consolidation & End-to-End Reliability (2026-03-08)
**Objectif**: Éliminer les stores in-memory, ajouter la persistence PostgreSQL, créer le module d'explainabilité transverse, compléter le mobile Flutter avec les écrans coach platform + biomarkers.

### Backend — Persistence DB ✅
- [x] `app/domains/coach_platform/models.py` — 6 modèles SQLAlchemy (CoachProfileDB, AthleteProfileDB, CoachAthleteLinkDB, TrainingProgramDB, AthleteNoteDB, AthleteAlertDB)
- [x] `app/domains/biomarkers/models.py` — `LabResultDB` + index composite user_date
- [x] `app/db/migrations/versions/V008_coach_platform_biomarkers.py` — 7 tables, down_revision=V007
- [x] `app/domains/coach_platform/endpoints.py` refactorisé — 5 stores in-memory → AsyncSession, + `GET /coach-platform/dashboard`
- [x] `app/domains/biomarkers/endpoints.py` refactorisé — `_lab_store` → AsyncSession + LabResultDB

### Backend — Module Explainabilité ✅
- [x] `app/core/explainability/labels.py` — risk_label, trend_label, day_type_label, biomarker_status_label, risk_level_label
- [x] `app/core/explainability/confidence.py` — confidence_tier (0.7/0.4), format_confidence
- [x] `app/core/explainability/severity.py` — SEVERITY_COLORS, SEVERITY_ICONS, alert_severity

### Tests LOT 17 ✅
- [x] `tests/test_explainability.py` — ~20 tests unitaires (labels, confidence, severity)
- [x] `tests/integration/test_e2e_coach_athlete.py` — Persistance coach platform
- [x] `tests/integration/test_e2e_biomarker_longevity.py` — Pipeline biomarqueurs
- [x] `tests/integration/test_e2e_learning_injury.py` — Learning + injury coherence
- [x] `tests/integration/test_e2e_full_context.py` — CoachContext ≤5500 chars
- [x] `tests/integration/test_e2e_coach_platform_persistence.py` — Absence in-memory patterns

### Flutter LOT 17 ✅
- [x] `lib/core/models/coach_platform.dart` — 10 classes Dart (CoachProfile, AthleteProfile, AthleteDashboardSummary, CoachAthletesOverview, TrainingProgram, AthleteNote, AthleteAlert + creates)
- [x] `lib/features/coach_platform/coach_platform_notifier.dart` — CoachDashboardNotifier, CoachProfileNotifier, AthleteAlertsNotifier (family), AthleteNotesNotifier (family)
- [x] `lib/features/coach_platform/coach_dashboard_screen.dart` — Dashboard coach + FAB + onboarding
- [x] `lib/features/coach_platform/athlete_detail_screen.dart` — Détail athlète + notes + alertes
- [x] `lib/features/biomarkers/biomarker_analysis_screen.dart` — Analyse complète + LongevityImpactCard
- [x] `lib/features/biomarkers/biomarker_results_screen.dart` — Liste résultats + BottomSheet ajout
- [x] 5 widgets partagés : RiskLevelBadge, AthleteAlertCard, BiomarkerMarkerRow, LongevityImpactCard, ConfidenceBadge
- [x] Navigation : +4 routes GoRouter, +8 ApiConstants endpoints, +6 CTAs (dashboard, profile, journal, bio_age)

---

## LOT 18 ✅ COMPLÉTÉ — Productization & Daily Experience Engine (2026-03-08)
**Objectif**: Transformer SOMA en application utilisée tous les jours — onboarding intelligent, briefing matinal, journal rapide, coach quick-advice, analytics produit.

### Backend ✅
- [x] `app/models/analytics.py` — `AnalyticsEventDB` (JSONB properties, 4 index composites)
- [x] `app/core/analytics/tracker.py` — `track_event()` fire-and-forget, 9 events, silent on failure
- [x] `app/db/migrations/versions/V009_analytics_events.py` — Migration V009, down_revision=V008
- [x] `app/services/daily_briefing_service.py` — `compute_daily_briefing()` agrégateur 5 sources, `DailyBriefing` dataclass 19 champs
- [x] `app/schemas/briefing.py` — `DailyBriefingResponse` Pydantic v2
- [x] `app/api/v1/endpoints/daily.py` — `GET /daily/briefing`
- [x] `app/schemas/onboarding.py` — `OnboardingRequest`, `OnboardingInitialTargets`, `OnboardingResponse`
- [x] `app/api/v1/endpoints/onboarding.py` — `POST /profile/onboarding` idempotent (PATCH profil + BodyMetric + calculs)
- [x] `app/api/v1/endpoints/analytics_events.py` — `POST /analytics/event`
- [x] `app/schemas/coach.py` — + `QuickAdviceRequest`, `QuickAdviceResponse`
- [x] `app/api/v1/endpoints/coach.py` — + `POST /coach/quick-advice` (no DB, parse regex)
- [x] `app/services/context_builder.py` — MAX_CONTEXT_CHARS 5500→6000 + `twin_key_signals` section
- [x] `app/api/v1/router.py` — +3 routers LOT 18

### Tests Backend LOT 18 ✅ (~102 nouveaux tests purs)
- [x] `tests/test_analytics.py` — 21 tests (EVENTS, TrackEventRequest, AnalyticsEventDB, track_event mock)
- [x] `tests/test_onboarding.py` — 26 tests (validation, defaults, targets)
- [x] `tests/test_daily_briefing.py` — 33 tests (_readiness_level/color, _extract_coach_tip, DailyBriefing, mock DB)
- [x] `tests/test_coach_quick_advice.py` — 22 tests (_parse_quick_reply, QuickAdvice schemas, context 6000)

### Flutter LOT 18 ✅
- [x] 5 widgets partagés : `ReadinessGauge`, `HealthScoreRing`, `InsightCard`, `CoachTipCard`, `AlertBanner`/`DismissibleAlertBanner`
- [x] `lib/core/models/onboarding.dart` — `OnboardingData`, `OnboardingInitialTargets`, `OnboardingResult`
- [x] `lib/features/onboarding/onboarding_notifier.dart` — StateNotifier + submit()
- [x] `lib/features/onboarding/onboarding_screen.dart` — PageView 7 pages
- [x] `lib/core/models/daily_briefing.dart` — `DailyBriefing` @immutable 19 champs + helpers French
- [x] `lib/features/briefing/briefing_notifier.dart` — AsyncNotifier cache 4h + dégradation stale
- [x] `lib/features/briefing/morning_briefing_screen.dart` — ReadinessGauge 140px + 5 cartes + alertes + insights + CTAs
- [x] `lib/features/quick_journal/quick_journal_screen.dart` — Grille 5 actions + 5 BottomSheets (<10s)
- [x] `lib/core/analytics/analytics_service.dart` — `AnalyticsEvents` (9) + fire-and-forget
- [x] `lib/core/api/api_constants.dart` — +4 endpoints LOT 18
- [x] `lib/core/cache/cache_config.dart` — + `CacheTTL.dailyBriefing`
- [x] `lib/main.dart` — +3 routes GoRouter (/onboarding, /briefing, /quick-journal)
- [x] `lib/features/dashboard/dashboard_screen.dart` — +_BriefingCTA + _QuickJournalCTA
- [x] `lib/core/notifications/notification_scheduler.dart` — payload briefing → /briefing

---

## LOT 19 ✅ COMPLÉTÉ — Product Validation, Retention & Internal Analytics (2026-03-08)
**Objectif**: Transformer SOMA en produit piloté par la donnée — analytics dashboard interne, cohortes de rétention, funnels d'onboarding, monitoring API.

### Backend — Monitoring Infrastructure ✅
- [x] `app/models/api_metrics.py` — `ApiMetricDB` (endpoint, method, response_time_ms, status_code, created_at + 4 index)
- [x] `app/db/migrations/versions/V010_api_metrics.py` — Migration V010, down_revision=V009
- [x] `app/middleware/metrics_middleware.py` — `MetricsMiddleware` buffer deque 10 000 entrées (non bloquant), `MetricRecord`, `get_buffered_metrics()`, `flush_metrics_buffer()`

### Backend — Analytics Dashboard ✅
- [x] `app/services/analytics_dashboard_service.py` — 7 fonctions async, 8 dataclasses, `_has_event_in_window()` (D1=[1,2), D7=[6,8), D30=[28,32)), `_EPOCH = 2024-01-01`
- [x] `app/schemas/analytics_dashboard.py` — 8 schémas Pydantic v2 (AnalyticsSummaryResponse, EventCountResponse, FunnelStepResponse, OnboardingFunnelResponse, CohortRetentionResponse, FeatureUsageResponse, CoachAnalyticsResponse, ApiPerformanceStatsResponse)
- [x] `app/api/v1/endpoints/analytics_dashboard.py` — 7 endpoints GET `/analytics/*` : summary, events, funnel/onboarding, retention/cohorts, features, coach, performance
- [x] `app/api/v1/router.py` — + `analytics_dashboard_router`
- [x] `app/main.py` — + `MetricsMiddleware`

### Tests Backend LOT 19 ✅ (~58 nouveaux tests purs)
- [x] `tests/test_analytics_summary.py` — 15 tests (dataclass, ratio DAU/MAU, onboarding rate div/0, schéma Pydantic)
- [x] `tests/test_analytics_retention.py` — 18 tests (`_has_event_in_window` 3 fenêtres + edge cases, CohortRetention, schéma)
- [x] `tests/test_analytics_funnels.py` — 13 tests (_FUNNEL_STEPS 5 étapes, conversion/drop-off, div/0, overall, schemas)
- [x] `tests/test_feature_usage.py` — 12 tests (FeatureUsage, CoachAnalytics, `get_performance_stats()` mock buffer, ApiMetricDB, schemas)

### Flutter LOT 19 ✅
- [x] `lib/core/analytics/analytics_service.dart` — +6 events : briefingOpened, briefingCardView, briefingCtaClick, journalOpen, journalActionSubmitted, journalActionCancelled
- [x] `lib/features/briefing/morning_briefing_screen.dart` — tracking briefing_opened + briefing_cta_click ; _BottomCTAs → ConsumerWidget
- [x] `lib/features/quick_journal/quick_journal_screen.dart` — tracking journal_open dans 5 _showXXXSheet
- [x] `lib/features/admin/analytics_dashboard_screen.dart` — 6 FutureProvider.autoDispose, 6 sections (Summary, Features, Funnel, Retention, Coach, Performance), RefreshIndicator, color-coding métriques
- [x] `lib/core/api/api_constants.dart` — +7 endpoints analytics dashboard
- [x] `lib/main.dart` — +1 route `/admin/analytics`

---

## Ordre chronologique des lots

| Lot | Thème | État |
|-----|-------|------|
| 0 | Fondations | ✅ COMPLÉTÉ |
| 1 | Backend Core + Auth | ✅ COMPLÉTÉ |
| 2 | Health Sync + Nutrition + Scores | ✅ COMPLÉTÉ |
| 3 | Health Intelligence Engine (7 modules) | ✅ COMPLÉTÉ |
| 4 | Scheduler + Flutter MVP 3 écrans | ✅ COMPLÉTÉ |
| 5 | Stabilisation + Mobile Extended | ✅ COMPLÉTÉ |
| 6 | Mobile Features Complètes (saisie données) | ✅ COMPLÉTÉ |
| 7 | Computer Vision V1 (on-device ML Kit) | ✅ COMPLÉTÉ |
| 8 | Vision Integration + History + Hardening | ✅ COMPLÉTÉ |
| 9 | Coach IA + Jumeau Métabolique | ✅ COMPLÉTÉ |
| 10 | Predictive Health Engine (3 moteurs) | ✅ COMPLÉTÉ |
| 11 | Advanced Intelligence + Scale-Ready Architecture | ✅ COMPLÉTÉ |
| 12 | Mobile Reliability & Daily Usage Excellence | ✅ COMPLÉTÉ |
| 13 | Personalized Learning Engine | ✅ COMPLÉTÉ |
| 14 | Coach Pro / Multi-Athletes Platform | ✅ COMPLÉTÉ |
| 15 | Injury Prevention Engine | ✅ COMPLÉTÉ |
| 16 | Longevity Lab Biomarkers | ✅ COMPLÉTÉ |
| 17 | Product Consolidation & End-to-End Reliability | ✅ COMPLÉTÉ |
| 18 | Productization & Daily Experience Engine | ✅ COMPLÉTÉ |
| 19 | Product Validation, Retention & Internal Analytics | ✅ COMPLÉTÉ |
