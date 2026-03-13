# SOMA — Architecture Technique Complète

## 1. Vue d'ensemble

SOMA est une application mobile personnelle full-stack organisée en **monorepo** avec les composants suivants :

```
┌──────────────────────────────────────────────────────────┐
│                    SOMA Architecture                      │
├──────────────────────────────────────────────────────────┤
│  📱 Flutter Mobile App (iOS / Android)                   │
│     - UI/UX mobile-first                                 │
│     - HealthKit / Health Connect SDK                     │
│     - Camera / MediaPipe integration                     │
│     - Offline-first avec sync                            │
├──────────────────────────────────────────────────────────┤
│  🔌 FastAPI Backend (Python 3.11+)                       │
│     - REST API v1                                        │
│     - Auth JWT local                                     │
│     - Business logic                                     │
│     - Orchestration des services                         │
├──────────────────────────────────────────────────────────┤
│  🧠 Services IA/ML (Python)                              │
│     - Moteur nutritionnel                                │
│     - Moteur de scoring                                  │
│     - Apprentissage personnalisé                         │
│     - Prédictions physiologiques                         │
├──────────────────────────────────────────────────────────┤
│  👁️ Computer Vision Service (Python)                    │
│     - MediaPipe Pose                                     │
│     - Détection exercices                                │
│     - Comptage répétitions                               │
│     - Analyse biomécanique                               │
├──────────────────────────────────────────────────────────┤
│  🗄️ Data Layer                                          │
│     - PostgreSQL (données primaires)                     │
│     - Redis (cache, sessions, tâches)                    │
│     - SQLAlchemy + Alembic (ORM + migrations)            │
│     - Stockage fichiers (local dev / S3-compatible)      │
└──────────────────────────────────────────────────────────┘
```

## 2. Stack technique

### Mobile (Flutter)
- **Framework**: Flutter 3.x (Dart)
- **State management**: Riverpod 2.x
- **Navigation**: GoRouter
- **HTTP Client**: Dio
- **Base de données locale**: Drift (SQLite) pour offline
- **Health SDK**: health package (HealthKit + Health Connect)
- **Camera**: camera + image_picker
- **ML on-device**: tflite_flutter (MediaPipe)
- **Notifications**: flutter_local_notifications
- **Charts**: fl_chart

### Backend (FastAPI)
- **Framework**: FastAPI 0.110+
- **Python**: 3.11+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: python-jose (JWT) + passlib (bcrypt)
- **HTTP async**: httpx
- **Tâches async**: Celery + Redis
- **Logs**: structlog
- **Tests**: pytest + pytest-asyncio + httpx

### Base de données
- **PostgreSQL 15+**: données primaires
- **Redis 7+**: cache, pub/sub, Celery broker
- **pgvector** (extension): embeddings ML si nécessaire

### IA / ML
- **scikit-learn**: modèles ML interprétables
- **PyTorch**: modèles plus complexes si nécessaire
- **NumPy + pandas**: calculs et data manipulation
- **OpenAI API / Claude API**: analyse de photos de repas, conseils IA quotidiens

### Computer Vision
- **MediaPipe**: pose estimation, skeleton tracking
- **OpenCV**: traitement image/vidéo
- **TFLite**: inférence on-device mobile

## 3. Architecture fonctionnelle

```
┌─────────────────────────────────────────────────────────┐
│                    MODULES FONCTIONNELS                   │
├───────────────┬─────────────────┬───────────────────────┤
│   DONNÉES     │   ANALYSES      │   RECOMMANDATIONS     │
├───────────────┼─────────────────┼───────────────────────┤
│ Module A      │ Module J        │ Module R              │
│ Profil        │ Moteur Nutrit.  │ IA Conseillère        │
├───────────────┼─────────────────┼───────────────────────┤
│ Module B      │ Module K        │ Module L              │
│ Health Sync   │ Micronutrition  │ Complémentation       │
├───────────────┼─────────────────┼───────────────────────┤
│ Module G      │ Module N        │ Module S              │
│ Journal Sport │ Sommeil/Récup   │ Détection Stagnation  │
├───────────────┼─────────────────┼───────────────────────┤
│ Module I      │ Module O        │ Module T              │
│ Journal Alim. │ Jumeau Métab.   │ Prédictions           │
├───────────────┼─────────────────┼───────────────────────┤
│ Module M      │ Module P        │ Module U              │
│ Hydratation   │ Biomécanique    │ Apprentissage         │
└───────────────┴─────────────────┴───────────────────────┘
         │               │                  │
         └───────────────┴──────────────────┘
                         │
              ┌──────────┴──────────┐
              │  PRÉSENTATION        │
              ├─────────────────────┤
              │ Module C: Dashboard  │
              │ Module Q: Longévité  │
              │ Module V: Notifs     │
              │ Module W: Rapports   │
              └─────────────────────┘
```

## 4. Architecture backend (FastAPI)

```
backend/
├── app/
│   ├── main.py                  # Entry point FastAPI
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── security.py          # JWT, hashing
│   │   ├── deps.py              # Dependency injection
│   │   └── logging.py           # structlog config
│   ├── db/
│   │   ├── base.py              # SQLAlchemy base
│   │   ├── session.py           # AsyncSession factory
│   │   └── migrations/          # Alembic
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── health.py
│   │   ├── workout.py
│   │   ├── nutrition.py
│   │   ├── sleep.py
│   │   └── ...
│   ├── schemas/                 # Pydantic schemas (request/response)
│   │   ├── user.py
│   │   ├── health.py
│   │   └── ...
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Agrège tous les routers
│   │       └── endpoints/       # Un fichier par domaine
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── health.py
│   │           ├── workouts.py
│   │           ├── nutrition.py
│   │           └── ...
│   ├── services/                # Business logic
│   │   ├── health_service.py
│   │   ├── nutrition_service.py
│   │   ├── workout_service.py
│   │   ├── scoring_service.py
│   │   └── ai_service.py
│   └── utils/
│       ├── calculations.py      # IMC, TDEE, etc.
│       └── units.py             # Normalisation unités
└── tests/
```

## 5. Architecture mobile (Flutter)

```
mobile/
├── lib/
│   ├── main.dart
│   ├── app/
│   │   ├── router.dart          # GoRouter
│   │   └── theme.dart           # Design system
│   ├── core/
│   │   ├── api/                 # Dio client + interceptors
│   │   ├── local_db/            # Drift (SQLite offline)
│   │   ├── health/              # HealthKit/Connect bridge
│   │   └── camera/              # Camera + pose detection
│   ├── features/                # Feature-first organization
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── profile/
│   │   ├── workout/
│   │   │   ├── camera_session/  # Module F
│   │   ├── nutrition/
│   │   ├── hydration/
│   │   ├── sleep/
│   │   ├── longevity/
│   │   └── settings/
│   └── shared/
│       ├── widgets/
│       └── utils/
└── test/
```

## 6. Flux de données

```
[Capteurs / HealthKit / Health Connect]
        │
        ▼
[Module B: Health Sync Service]
        │
        ▼
[PostgreSQL: health_samples]
        │
        ├──► [Module O: Jumeau métabolique] ──► metabolic_state_snapshots
        ├──► [Module N: Sommeil/Récupération] ──► readiness_scores
        ├──► [Module J: Moteur nutritionnel] ──► daily_targets
        ├──► [Module Q: Score longévité] ──► longevity_scores
        │
        ▼
[Module R: IA Conseillère] ──► daily_recommendations
        │
        ▼
[Module C: Dashboard] ──► Affichage mobile
```

## 7. Stratégie offline-first

- **Drift (SQLite)**: stockage local de toutes les données récentes (30 jours)
- **Sync queue**: actions locales mises en file pour sync dès reconnexion
- **Conflict resolution**: stratégie "last-write-wins" avec timestamp serveur
- **Cache Redis**: données calculées (scores, recommandations) avec TTL

## 8. Sécurité

- **Auth**: JWT (access token 15min + refresh token 30j) stocké en SecureStorage mobile
- **Chiffrement local**: AES-256 pour données sensibles sur device
- **HTTPS**: TLS obligatoire en production
- **Permissions**: granulaires par type de données santé
- **Audit log**: toutes les modifications importantes tracées

## 9. Scheduler & Background Jobs (LOT 4)

### Architecture choisie : APScheduler AsyncIOScheduler (in-process)

```
FastAPI lifespan
    │
    ├── startup  → scheduler.start()
    │                    │
    │               AsyncIOScheduler (event loop FastAPI)
    │                    │
    │               CronTrigger(hour=5, minute=30, timezone="Europe/Paris")
    │                    │
    │               daily_pipeline_job()
    │                    │
    │               run_daily_pipeline_all_users(target_date)
    │                    │
    │               ┌────┴─────────────────────────────────┐
    │               │  Pour chaque User.is_active           │
    │               │                                       │
    │               │  run_daily_pipeline_for_user()        │
    │               │    Step 1 : DailyMetrics              │
    │               │    Step 2 : ReadinessScore            │
    │               │    Step 3 : Insights                  │
    │               │    Step 4 : HealthPlan (log)          │
    │               │    Step 5 : LongevityScore (log)      │
    │               └───────────────────────────────────────┘
    │
    └── shutdown → scheduler.shutdown(wait=False)
```

### Choix de design

| Décision | Choix | Raison |
|---|---|---|
| Scheduler | APScheduler in-process | Pas de service externe, simple à déployer, async-native |
| Alternative prod | Celery + Redis Beat | Pour multi-instance / haute disponibilité |
| Heure d'exécution | 5h30 Europe/Paris | Avant le réveil utilisateur, données prêtes au démarrage app |
| Grace time | 3600s (1h) | Tolère un redémarrage serveur sans manquer le job |
| Isolation steps | try/except par étape | Une DB failure n'annule pas tout le pipeline |
| Isolation users | commit après chaque user | Erreur sur user N n'affecte pas user N+1 |
| Session DB | `_get_session_factory()` standalone | Pas de contexte FastAPI disponible dans le cron |

### Fallback lazy computation

Les endpoints critiques déclenchent `lazy_ensure_today_metrics()` si les données du jour sont absentes (scheduler n'a pas encore tourné, premier lancement, etc.) :

```
GET /metrics/daily       → compute_and_persist_daily_metrics() si absent
GET /health/plan/today   → lazy_ensure_today_metrics() avant generate
GET /scores/longevity    → lazy_ensure_today_metrics() avant compute
```

`lazy_ensure_today_metrics()` passe `force_recompute=False` — le cache 2h dans `compute_and_persist_daily_metrics` empêche tout double calcul inutile.

### Fichiers

- **`app/services/scheduler_service.py`** — Pipeline + scheduler factory
- **`app/main.py`** — Intégration lifespan (start/shutdown)
- **`app/services/daily_metrics_service.py`** — `lazy_ensure_today_metrics()`

## 10. LOT 5 — Stabilisation (2026-03-07)

### Agrégateur Home Summary

`GET /home/summary` — Réduit 5 appels API en 1 au démarrage de l'app mobile :

| Donnée | Source | Comportement si absent |
|---|---|---|
| DailyMetrics | `daily_metrics` table | `lazy_ensure_today_metrics()` déclenché |
| ReadinessScore | `readiness_scores` table | `null` — non bloquant |
| Insights non lus | `insights` table | Max 5, triés par `detected_at` desc |
| Plan santé | `DailyRecommendation.daily_plan` | Cache uniquement (pas de génération ici) |
| Score longévité | `longevity_scores` table | Dernière entrée disponible (peut être ancienne) |

Le pattern "read-only aggregator" garantit une latence faible (5 SELECT séquentiels, pas de compute lourd). La génération de plan à la volée est exclue intentionnellement.

### Health Plan Persistence (DailyRecommendation)

`GET /health/plan/today` implémente une politique de cache 6h sur le modèle `DailyRecommendation` :

```
Request → Check DailyRecommendation (today)
    │
    ├── Fresh (< 6h) → return from_cache=True  (fast path, ~10ms)
    │
    └── Stale / missing → generate_daily_health_plan()
                               → upsert DailyRecommendation.daily_plan (JSONB)
                               → return from_cache=False
```

Le flag `from_cache` dans la réponse permet au client mobile de décider s'il doit afficher un indicateur "Plan mis à jour".

### Algorithm Version Tracking

Chaque enregistrement calculé porte la version de l'algorithme qui l'a produit :

| Modèle | Colonne | Valeur actuelle |
|---|---|---|
| `DailyMetrics` | `algorithm_version VARCHAR(10)` | `"v1.0"` |
| `ReadinessScore` | `algorithm_version VARCHAR(10)` | `"v1.0"` |
| `LongevityScore` | `algorithm_version VARCHAR(10)` | `"v1.0"` |

Exposé dans tous les schémas de réponse. En production, permet d'identifier les enregistrements calculés avec un algorithme obsolète et de déclencher un recalcul ciblé après mise à jour.

### Mobile Auth Architecture

```
app startup
    └── await TokenStorage.load()  (SharedPreferences → mémoire)
            │
            ├── tokens present → AuthNotifier._restoreSession() → AuthStateAuthenticated
            └── no tokens     → AuthStateUnauthenticated
                                        │
                                        └── GoRouter redirect → /login

Auth guard (GoRouter.redirect + refreshListenable):
    AuthStateUnauthenticated | AuthStateInitial  → '/login'
    AuthStateAuthenticated + isLogin route       → '/'
    _AuthListenable.notifyListeners() à chaque changement authProvider
```

TokenStorage : `accessToken` / `refreshToken` restent synchrones (lus depuis mémoire après `load()`) pour compatibilité avec le `Dio` intercepteur.

### Fichiers clés LOT 5

- **`app/schemas/home.py`** — Schémas `HomeSummaryResponse` + sous-schémas
- **`app/api/v1/endpoints/home.py`** — `GET /home/summary`
- **`app/db/migrations/versions/V004_algorithm_version.py`** — Migration V004
- **`mobile/lib/features/auth/`** — `auth_state.dart`, `auth_notifier.dart`, `login_screen.dart`
- **`mobile/lib/features/insights/`** — `insights_notifier.dart`, `insights_screen.dart`
- **`mobile/lib/core/config/app_config.dart`** — Config dev/prod
- **`mobile/lib/core/errors/api_error.dart`** — Gestion erreurs structurée
- **`mobile/lib/shared/widgets/loading_skeleton.dart`** — Placeholders animés (opacity 0.3→0.7)

## 11. LOT 7 — Computer Vision V1 (2026-03-07)

### Principe : traitement 100% on-device

Contrairement à l'architecture initiale qui envisageait un service Python MediaPipe côté serveur, LOT 7 a retenu une approche **entièrement mobile** :

```
[Caméra téléphone]
        │
        ▼ CameraImage (NV21 Android / BGRA8888 iOS)
[PoseDetectorService]
        │  google_mlkit_pose_detection (on-device, mode stream)
        ▼ DetectedPose (33 landmarks normalisés [0,1])
[ExerciseClassifier] ──► isValid + confidence + feedback
        │
        ▼ ExerciseAngles
[AngleCalculator]
        │  angles articulaires 2D (genou, coude, hanche, alignement)
        ▼
[RepCounter (FSM par exercice)]
        │  peak → ascending = comptage immédiat
        ▼ RepCounterState (count, phase, peakAngles, timestamps)
[QualityScorer]
        │  amplitude (40%) + stabilité (35%) + régularité (25%)
        ▼ MovementQuality (4 scores 0-100)
[VisionNotifier] ──► état UI (status, reps, qualité, pose)
        │
        ▼ POST /api/v1/vision/sessions
[Backend FastAPI]
        │  résumé JSON seulement — aucune vidéo transmise
        └──► vision_sessions (PostgreSQL)
```

### Automates finis RepCounter

| Exercice | Phases | Seuils | Comptage |
|---|---|---|---|
| Squat | starting → descending → peak → ascending | 155° / 115° (±10° hystérèse) | peak→ascending |
| Push-Up | starting → descending → peak → ascending | 150° / 90° (±10°) | peak→ascending |
| Plank | idle ↔ holding | ±30° alignement, 300 frames = 1 | timer-based |
| Jumping Jack | starting → ascending → peak → descending | ratio bras 0.5/0.3 + jambes | peak→descending |
| Lunge | starting → descending → peak → ascending | 155° / 110° (±10°) | peak→ascending |
| Sit-Up | starting → ascending → peak → descending | 70° / 40° (±8°) | peak→descending |

### QualityScorer — formules

```
amplitude_score  = clamp((refAngle - minPeakAngle) / refAngle * 100, 0, 100)
                   # refAngle : squat=90°, push-up=75°, plank=175°, JJ=0.8, lunge=90°, sit-up=20°

stability_score  = clamp(100 - avgDeviationFrom180 / 20 * 100, 0, 100)
                   # si < 3 frames fiables → neutre 70.0

regularity_score = clamp(100 - cv(intervalles) / 0.5 * 100, 0, 100)
                   # cv = std / mean ; si < 3 reps → neutre 60.0

overall_score    = amplitude * 0.40 + stability * 0.35 + regularity * 0.25
```

### Performance

- **Throttle** : 1 frame traitée sur 2 (_kFrameSkip = 2), mutex `_isProcessing` pour éviter pile-up
- **Résolution caméra** : `ResolutionPreset.medium` (suffisant pour 33 landmarks)
- **Mode ML Kit** : `stream` + `accurate` (vs `fast` — précision préférée sur exercices)
- **Format** : NV21 (Android via concaténation planes) / BGRA8888 (iOS, planes[0] direct)

### Schéma de données backend

```sql
vision_sessions (
  id               UUID PRIMARY KEY,
  user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
  exercise_type    VARCHAR(50) NOT NULL,  -- squat, push_up, plank, jumping_jack, lunge, sit_up
  rep_count        INTEGER NOT NULL,
  duration_seconds INTEGER NOT NULL,
  amplitude_score  FLOAT,
  stability_score  FLOAT,
  regularity_score FLOAT,
  quality_score    FLOAT,
  workout_session_id UUID REFERENCES workout_sessions(id) ON DELETE SET NULL,
  metadata         JSONB DEFAULT '{}',   -- algorithm_version, device, etc.
  algorithm_version VARCHAR(10) DEFAULT 'v1.0',
  session_date     DATE NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
)
```

### Fichiers clés LOT 7

#### Mobile (Dart)
- **`features/vision/models/`** — `exercise_frame.dart`, `pose_landmark.dart`, `vision_session.dart`
- **`features/vision/services/`** — `angle_calculator.dart`, `rep_counter.dart`, `quality_scorer.dart`, `exercise_classifier.dart`, `pose_detector_service.dart`
- **`features/vision/providers/vision_notifier.dart`** — Orchestrateur Riverpod
- **`features/vision/screens/`** — `vision_exercise_setup_screen.dart`, `vision_workout_screen.dart`, `vision_session_summary_screen.dart`
- **`features/vision/widgets/`** — `pose_overlay_painter.dart`, `rep_counter_widget.dart`, `quality_score_widget.dart`

#### Backend (Python)
- **`app/db/migrations/versions/V005_vision_sessions.py`** — Migration table vision_sessions
- **`app/models/vision_session.py`** — Modèle SQLAlchemy
- **`app/schemas/vision.py`** — Schémas Pydantic (Create + Response)
- **`app/api/v1/endpoints/vision.py`** — Endpoints POST + GET /vision/sessions

### Limitations et évolutions (LOT 8+)

| Limitation | Impact | Solution envisagée |
|---|---|---|
| Bug `toJson()` Jumping Jack | "jumping jack" rejeté par backend | Remplacer espaces par `_` dans `toJson()` |
| Pas d'historique CV dans l'app | Données sauvegardées mais non affichées | Écran historique sessions vision |
| Feedback profondeur en temps réel | Utilisateur ne sait pas à quelle profondeur aller | Flèches directionnelles sur overlay |
| Tests ML Kit mockés | Pas de test d'intégration caméra réelle | Tests sur device physique |
| Angle 2D uniquement | Moins précis que 3D pour certains exercices | ML Kit 3D ou ajout axe Z |

---

## 13. LOT 10 — Predictive Health Engine (2026-03-08)

### Principe : moteurs déterministes indépendants du LLM

Les 3 moteurs prédictifs LOT 10 suivent un pattern strict :
- **Fonctions pures** : inputs = scalaires `Optional[float]`, output = dataclass, aucun accès DB
- **Confidence proportionnelle** aux données disponibles (somme des poids des composantes présentes)
- **Pas de migration DB** : calcul à la demande, inputs lus depuis les tables existantes
- **Testabilité maximale** : ~40 tests par moteur, zéro fixture async nécessaire

```
Données DB ──► _load_all_inputs()
                    │
                    ├── MetabolicStateSnapshot (training_load_7d, training_load_28d, fatigue, tdee)
                    ├── ReadinessScore (overall_readiness, sleep_score)
                    ├── DailyMetrics × 7j (weight_kg, calories_consumed, active_calories)
                    └── VisionSession × 7j (stability_score, amplitude_score)
                         │
                         ▼
               compute_injury_risk()  ──► InjuryRiskResult
               compute_overtraining_risk() ──► OvertrainingResult
               compute_weight_predictions() ──► WeightPredictionResult
                         │
                         ▼
               GET /health/predictions (agrégé)
               GET /health/injury-risk
               GET /health/overtraining
```

### InjuryRiskEngine

**Entrées :** `training_load_7d`, `training_load_28d`, `fatigue_score`, `avg_vision_quality`, `readiness_score`

**Pondération des composantes :**

| Composante | Poids | Fonction | Justification |
|---|---|---|---|
| ACWR | 35% | `_score_acwr_risk()` | Principal prédicteur de blessure (littérature sportive) |
| Fatigue | 25% | `_score_fatigue_risk()` | Muscles/tendons moins résistants sous fatigue accumulée |
| Biomécanique | 25% | `_score_biomechanics_risk()` | Proxy asymétrie : stability + amplitude VisionSessions |
| Récupération | 15% | `_score_readiness_risk()` | Readiness faible = récupération incomplète |

**Seuils ACWR :**
```
0–0.8  : undertraining     → risque faible (déconditionnement)
0.8–1.3: zone sûre         → risque minimal (10/100)
1.3–1.5: zone modérée      → risque 10→45
1.5–2.0: zone élevée       → risque 45→80
> 2.0  : zone critique     → risque 80→100
```

**Niveaux de risque :** `low` (<25) / `moderate` (25–49) / `high` (50–74) / `critical` (≥75)

### OvertrainingEngine

**Entrées :** `training_load_7d`, `training_load_28d`, `sleep_score`, `fatigue_score`, `readiness_score`

**ACWR normalisé :**
```
ACWR = training_load_7d / (training_load_28d / 4)
```
La normalisation par 4 convertit la charge chronique (28j) en équivalent hebdomadaire avant division.

**Zones ACWR (Foster 2001, Hulin 2016) :**

| Zone | ACWR | Interprétation |
|---|---|---|
| undertraining | < 0.8 | Charge insuffisante — déconditionnement progressif |
| optimal | 0.8–1.3 | Zone de supercompensation — progression sans risque |
| moderate_risk | 1.3–1.5 | Augmentation acceptable avec vigilance |
| high_risk | 1.5–2.0 | Risque de surentraînement modéré |
| overreaching | > 2.0 | Surcharge aiguë — repos obligatoire |

**Pondération :** ACWR 40% / Bien-être (sommeil+fatigue) 35% / Readiness 25%

### WeightPredictionEngine

**Modèle énergétique linéaire :**
```
delta_kg(t) = (balance_kcal × jours × adaptation_factor) / 7700

Où :
  balance_kcal       = calories_consumed - estimated_tdee
  adaptation_factor  = 1.00 (7j) / 0.90 (14j) / 0.80 (30j)
  7700               = kcal théoriques pour ±1 kg de tissu adipeux
```

**Facteurs d'adaptation métabolique :**
- Le métabolisme s'adapte progressivement à un déficit/surplus persistant (thermogenèse adaptative)
- À 14j : efficacité métabolique accrue → réduction de 10% du delta théorique
- À 30j : adaptation marquée → réduction de 20%

**Préférence TDEE :** `estimated_tdee_kcal` (MetabolicTwin) > `active_calories_kcal` (fallback)

**Tendance :** `loss` (delta_7d < −0.3 kg) / `stable` (±0.3 kg) / `gain` (delta_7d > +0.3 kg)

### Fichiers clés LOT 10

#### Backend (Python)
- **`app/services/injury_risk_engine.py`** — InjuryRiskResult + 5 fonctions pures + `compute_injury_risk()`
- **`app/services/overtraining_engine.py`** — OvertrainingResult + `_compute_acwr()` + `compute_overtraining_risk()`
- **`app/services/weight_prediction_engine.py`** — WeightPredictionResult + modèle linéaire + `compute_weight_predictions()`
- **`app/schemas/predictions.py`** — 4 schémas Pydantic v2 (InjuryRisk, Overtraining, WeightPrediction, Combined)
- **`app/api/v1/endpoints/predictions.py`** — 3 GET endpoints + `_load_all_inputs()` helper
- **`tests/test_injury_risk_engine.py`** — 47 tests purs
- **`tests/test_overtraining_engine.py`** — 38 tests purs
- **`tests/test_weight_prediction_engine.py`** — 33 tests purs
