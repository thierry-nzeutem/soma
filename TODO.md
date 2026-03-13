# SOMA — TODO Global Priorisé

## 🔴 P0 — LOT 0/1 ✅ COMPLÉTÉ (2026-03-07)

- [x] Structure monorepo
- [x] Documentation ARCHITECTURE, DATA_MODEL, ROADMAP, RISKS, API_CONTRACTS
- [x] Docker Compose (PostgreSQL + Redis)
- [x] FastAPI app skeleton + middleware
- [x] Modèles SQLAlchemy: users, profiles, body_metrics, health, workout, nutrition, scores
- [x] Auth endpoints (register, login, refresh)
- [x] Profile endpoints (GET, PUT)
- [x] Body metrics endpoints
- [x] Health sync (structure + background job)
- [x] Sleep log endpoints
- [x] Hydration log + today summary
- [x] Service calculs physiologiques (BMR, TDEE, BMI, protéines, hydratation)
- [x] Tests unitaires calculs (31 tests)
- [x] **Alembic migrations initiales** — V001 créée (20 tables)
- [x] **Seed data exercices** — 59 exercices de base (`data/exercises_seed.json`)
- [x] **Dashboard endpoint `/api/v1/dashboard/today`** — score récupération V1, alertes, recs
- [x] **Module sport workout** — sessions, exercices, séries (14 endpoints CRUD)
- [x] **Tests unitaires dashboard** (35 tests) + **workout** (33 tests) → **99 tests ✅**

## 🟠 P1 — LOT 2 ✅ COMPLÉTÉ (2026-03-07)

- [x] **Migration V002** — `is_deleted`, `updated_at`, `meal_name`, `entry_id`, indexes trigram
- [x] **Module nutrition: journal alimentaire CRUD** — 11 endpoints (FoodItem search + NutritionEntry + daily-summary)
- [x] **Module nutrition: pipeline photo repas** — upload → Claude Vision mock/réel (BackgroundTask) → confirm → entry
- [x] **Score de récupération persistant** — `ReadinessScore` avec upsert + freshness 1h (compute_and_persist_readiness)
- [x] **Endpoints ReadinessScore** — GET /scores/readiness/today + /history
- [x] **Intégration dashboard** — build_dashboard() persiste le score (lazy import, fallback silencieux)
- [x] **Tests unitaires LOT 2** — 72 tests (nutrition, vision, readiness) → **171 tests ✅**
- [x] **Tests d'intégration** — structure créée (`tests/integration/` avec skip auto)
  - [x] test_auth_flow.py (register → login → refresh → protected)
  - [x] test_nutrition_integration.py (CRUD, daily-summary, ownership isolation)
  - [x] test_readiness_integration.py (persistance, freshness, historique)
- [x] **Documentation** — API_CONTRACTS.md + CHANGELOG.md mis à jour (LOT 2)

## 🟠 P1 — LOT 3 (Priorité haute — prochaine)

- [ ] **Tests d'intégration live** — lancer sur PostgreSQL réel (`SOMA_TEST_DATABASE_URL`)
- [ ] **Module nutrition: moteur adaptatif** — TDEE dynamique, ajustement calories selon historique
- [ ] **Jumeau métabolique** — snapshot `MetabolicStateSnapshot` quotidien
- [ ] **Module nutrition: micronutrition** — estimation déficiences depuis les entrées
- [ ] **Recommandations compléments** — basées sur pattern nutritionnel observé

## 🟡 P2 — LOT 4/5 (Priorité moyenne)

- [ ] Recommandations IA quotidiennes (Claude API)
- [ ] Score longévité multi-dimensions
- [ ] Module sommeil: analyse + score
- [ ] Rapports hebdomadaires auto-générés
- [ ] Notifications intelligentes
- [ ] Recommandations complémentation

## 🟢 P3 — LOT 6/7 (Mobile + CV)

- [ ] **Flutter app**: setup projet + Riverpod + GoRouter
- [ ] **Flutter**: écrans onboarding + profil
- [ ] **Flutter**: dashboard
- [ ] **Flutter**: journal d'entraînement
- [ ] **Flutter**: journal alimentaire + photo
- [ ] **Flutter**: Apple HealthKit integration (iOS)
- [ ] **Flutter**: Google Health Connect (Android)
- [ ] **Computer Vision**: MediaPipe Pose service
- [ ] **Computer Vision**: comptage répétitions
- [ ] **Computer Vision**: analyse biomécanique

## 🔵 P4 — LOT 8 (Avancé)

- [ ] Prédictions glycémie / cortisol (Module T)
- [ ] Score risque blessure (ACWR)
- [ ] Détection stagnation + adaptation programme
- [ ] Apprentissage personnalisé (Module U)
- [ ] Optimisation zone 2 cardio
- [ ] Rapports mensuels / trimestriels

## 📋 Décisions techniques pendantes

- [x] ~~Choisir modèle vision pour analyse photo repas~~ → Claude Vision (claude-opus-4-5), toggle mock/réel
- [ ] Valider stack MediaPipe sur Android / iOS Flutter
- [ ] Définir stratégie de cache Redis pour scores/recommandations
- [ ] Choisir entre Celery vs APScheduler pour tâches périodiques (génération scores nuit)
