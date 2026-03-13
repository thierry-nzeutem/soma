# SOMA — Contrats API v1

**Base URL**: `http://localhost:8000/api/v1`
**Auth**: Bearer JWT dans header `Authorization`
**Format**: JSON
**Versioning**: URL-based (/api/v1/)

---

## AUTH

### POST /auth/register
**Body**:
```json
{ "username": "string", "password": "string", "email": "string?" }
```
**Response 201**:
```json
{ "access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer" }
```

### POST /auth/login
**Body**: `{ "username": "string", "password": "string" }`
**Response 200**: idem register

### POST /auth/refresh
**Body**: `{ "refresh_token": "string" }`
**Response 200**: `{ "access_token": "jwt" }`

---

## PROFIL UTILISATEUR

### GET /profile
**Response 200**:
```json
{
  "id": "uuid",
  "first_name": "string",
  "age": 35,
  "sex": "male",
  "height_cm": 180,
  "goal_weight_kg": 80,
  "primary_goal": "weight_loss",
  "activity_level": "moderate",
  "fitness_level": "intermediate",
  "dietary_regime": "omnivore",
  "intermittent_fasting": true,
  "fasting_protocol": "23:1",
  "meals_per_day": 1,
  "home_equipment": ["dumbbells"],
  "gym_access": true,
  "computed": {
    "bmi": 24.7,
    "bmr_kcal": 1850,
    "tdee_kcal": 2590,
    "target_calories_kcal": 2090,
    "target_protein_g": 160,
    "target_hydration_ml": 2500
  },
  "profile_completeness_score": 85.0
}
```

### PUT /profile
**Body**: Partial profile fields
**Response 200**: Updated profile

---

## MÉTRIQUES CORPORELLES

### POST /body-metrics
**Body**:
```json
{ "weight_kg": 85.2, "body_fat_pct": 22.5, "measured_at": "2026-03-07T08:00:00Z" }
```

### GET /body-metrics?days=30
**Response 200**:
```json
{
  "entries": [{ "measured_at": "...", "weight_kg": 85.2, "body_fat_pct": 22.5 }],
  "trend": { "weight_slope_kg_per_week": -0.3, "direction": "decreasing" }
}
```

---

## HEALTH SYNC

### POST /health/sync
**Body**: `{ "source": "apple_health", "data": {...} }`
**Response 202**: `{ "job_id": "uuid", "status": "pending" }`

### GET /health/sync/{job_id}
**Response 200**: `{ "status": "success", "records_imported": 1240 }`

### GET /health/summary?date=2026-03-07
**Response 200**:
```json
{
  "date": "2026-03-07",
  "steps": 8432,
  "active_calories_kcal": 420,
  "resting_heart_rate_bpm": 58,
  "hrv_ms": 45,
  "vo2_max": 42.5,
  "stand_hours": 10,
  "distance_km": 6.2
}
```

---

## DASHBOARD

### GET /dashboard/today
**Response 200**:
```json
{
  "date": "2026-03-07",
  "scores": {
    "readiness": 78,
    "nutrition": 65,
    "activity": 55,
    "sleep": 82,
    "recovery": 74,
    "longevity": 71
  },
  "summary": {
    "calories_consumed": 1850,
    "calories_target": 2090,
    "protein_g": 145,
    "protein_target_g": 160,
    "hydration_ml": 1000,
    "hydration_target_ml": 2500,
    "steps": 8432,
    "active_minutes": 45,
    "weight_kg": 85.2
  },
  "alerts": [
    { "type": "hydration", "severity": "warning", "message": "Hydratation insuffisante : 1L / 2.5L" }
  ],
  "recommendation_preview": "Bonne récupération détectée. Séance de force recommandée aujourd'hui."
}
```

### GET /dashboard/week
### GET /dashboard/month
### GET /dashboard/trends

---

## ENTRAÎNEMENTS

### POST /workouts
**Body**:
```json
{
  "session_type": "strength",
  "location": "gym",
  "started_at": "2026-03-07T18:00:00Z",
  "rpe_score": 7,
  "notes": "Bonne séance"
}
```

### PUT /workouts/{id}/complete
**Body**: `{ "ended_at": "...", "rpe_score": 7, "energy_after": 7 }`

### POST /workouts/{id}/exercises
**Body**: `{ "exercise_id": "uuid", "exercise_order": 1 }`

### POST /workouts/{workout_id}/exercises/{ex_id}/sets
**Body**:
```json
{ "set_number": 1, "reps_target": 10, "reps_actual": 10, "weight_kg": 80, "rpe_set": 7 }
```

### GET /workouts?limit=20&offset=0
### GET /workouts/{id}
### GET /workouts/stats?period=month

---

## EXERCICES

### GET /exercises?muscle_group=quadriceps&equipment=machine&level=intermediate
### GET /exercises/{id}
### GET /exercises/search?q=squat

---

## NUTRITION (LOT 2)

### Bibliothèque d'aliments

#### GET /food-items?query=poulet&food_group=protein&page=1&per_page=20
Recherche floue dans la base d'aliments (trigram index PostgreSQL).
**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid", "name": "Chicken Breast", "name_fr": "Blanc de poulet",
      "calories_per_100g": 165, "protein_g_per_100g": 31, "carbs_g_per_100g": 0,
      "fat_g_per_100g": 3.6, "fiber_g_per_100g": 0,
      "food_group": "protein", "nova_score": 1, "is_ultra_processed": false,
      "source": "usda", "verified": true
    }
  ],
  "total": 1, "page": 1, "per_page": 20
}
```

#### GET /food-items/{id}
**Response 200**: FoodItemResponse complet
**Response 404**: Aliment introuvable

---

### Journal alimentaire

#### POST /nutrition/entries
**Body** (3 modes alternatifs) :
```json
{
  "logged_at": "2026-03-07T19:30:00Z",
  "meal_type": "dinner",
  "meal_name": "Poulet riz légumes",

  "food_item_id": "uuid",
  "quantity_g": 200,

  "calories": 620, "protein_g": 55, "carbs_g": 55, "fat_g": 12,
  "fiber_g": 4,
  "data_quality": "exact",

  "hunger_before": 7, "satiety_after": 4, "energy_after": 8,
  "notes": "Après entraînement",
  "fasting_window_broken": true
}
```
Au moins un parmi : `food_item_id`, `photo_id`, ou macro explicite requis.
**Response 201**: NutritionEntryResponse

#### GET /nutrition/entries?date=2026-03-07&page=1&per_page=50
**Response 200**:
```json
{
  "entries": [{ "id": "uuid", "calories": 620, "meal_type": "dinner", ... }],
  "total": 1,
  "date": "2026-03-07"
}
```

#### GET /nutrition/entries/{id}
**Response 200**: NutritionEntryResponse
**Response 404**: Entrée introuvable

#### PATCH /nutrition/entries/{id}
**Body**: Champs partiels (PATCH sémantique)
**Response 200**: NutritionEntryResponse mis à jour

#### DELETE /nutrition/entries/{id}
Soft-delete (is_deleted = true).
**Response 204**: Aucun contenu

---

### Résumé journalier

#### GET /nutrition/daily-summary?date=2026-03-07
**Response 200**:
```json
{
  "date": "2026-03-07",
  "meal_count": 3,
  "totals": {
    "calories": 1850, "protein_g": 145, "carbs_g": 210, "fat_g": 55, "fiber_g": 28
  },
  "goals": { "calories_target": 2090, "protein_target_g": 160 },
  "balance": {
    "calories_delta": -240, "protein_delta_g": -15,
    "pct_calories_reached": 88.5, "pct_protein_reached": 90.6
  },
  "eating_window": {
    "first_meal_at": "2026-03-07T07:00:00Z",
    "last_meal_at": "2026-03-07T19:30:00Z",
    "window_hours": 12.5,
    "fasting_compatible": false
  },
  "meals": [
    { "id": "uuid", "meal_type": "breakfast", "logged_at": "...", "calories": 350 }
  ],
  "data_completeness_pct": 100.0,
  "has_photo_entries": false
}
```

---

### Pipeline photo repas

#### POST /nutrition/photos
**Body**: `multipart/form-data` avec champ `file` (JPEG, PNG, WebP, HEIC — max 10Mo).
**Response 201**:
```json
{
  "photo_id": "uuid",
  "status": "pending",
  "message": "Photo reçue. L'analyse IA est en cours..."
}
```
L'analyse Claude Vision démarre en tâche de fond.

#### GET /nutrition/photos/{photo_id}
Sondage du résultat de l'analyse (polling).
**Response 200**:
```json
{
  "photo_id": "uuid",
  "analysis_status": "analyzed",
  "identified_foods": [
    { "name": "Chicken", "quantity_g": 200, "calories_estimated": 330, "confidence": 0.92 }
  ],
  "estimated_calories": 620,
  "estimated_protein_g": 55,
  "estimated_carbs_g": 55,
  "estimated_fat_g": 12,
  "overall_confidence": 0.85,
  "meal_type_guess": "dinner",
  "warnings": [],
  "assumptions": ["Standard cooking method assumed"],
  "created_at": "2026-03-07T19:00:00Z",
  "analyzed_at": "2026-03-07T19:00:05Z"
}
```
Statuts : `pending` → `analyzing` → `analyzed` | `failed`

#### POST /nutrition/photos/{photo_id}/confirm
Valide l'analyse et crée optionnellement une NutritionEntry.
**Body**:
```json
{
  "meal_type": "dinner",
  "meal_name": "Poulet riz légumes",
  "corrected_calories": 580,
  "corrected_protein_g": 52,
  "notes": "Portion un peu plus petite",
  "create_entry": true
}
```
**Response 200**:
```json
{
  "photo_id": "uuid",
  "user_validated": true,
  "meal_type": "dinner",
  "entry_id": "uuid",
  "final_calories": 580,
  "final_protein_g": 52,
  "final_carbs_g": 55,
  "final_fat_g": 12
}
```

---

## HYDRATATION

### POST /hydration/log
**Body**: `{ "volume_ml": 500, "logged_at": "...", "beverage_type": "water" }`

### GET /hydration/today
**Response**: `{ "total_ml": 1500, "target_ml": 2500, "pct": 60, "entries": [...] }`

---

## SOMMEIL

### POST /sleep
**Body**: `{ "start_at": "...", "end_at": "...", "perceived_quality": 4 }`

### GET /sleep?days=14

---

## RECOMMANDATIONS

### GET /recommendations/today
**Response 200**: `daily_recommendations` object complet

### GET /supplements
**Response 200**: Liste recommandations compléments actives

---

## SCORES (LOT 2)

### GET /scores/readiness/today?date=2026-03-07
Lecture du ReadinessScore persisté en DB (calculé par /dashboard/today).
**Response 200**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "score_date": "2026-03-07",
  "overall_readiness": 75.0,
  "sleep_score": 82.0,
  "hrv_score": 65.0,
  "training_load_score": 70.0,
  "recovery_score": 82.0,
  "recommended_intensity": "normal",
  "reasoning": "Bonne récupération (75/100). Séance normale recommandée.",
  "confidence_score": 0.8,
  "variables_used": {
    "sleep_available": true, "hrv_available": true,
    "sleep_minutes": 450, "hrv_ms": 48
  },
  "created_at": "2026-03-07T06:00:00Z",
  "updated_at": "2026-03-07T06:00:00Z"
}
```
**Response 404**: Score non calculé pour cette date (appeler /dashboard/today d'abord).

### GET /scores/readiness/history?days=30
**Response 200**:
```json
{
  "history": [{ ... }],
  "days_requested": 30,
  "days_available": 12,
  "date_from": "2026-02-24",
  "date_to": "2026-03-07"
}
```

### GET /scores/longevity
**Auth**: Bearer JWT
**Query**: `?days=30` (1-90)
**Response 200**:
```json
{
  "computed_at": "2026-03-07T08:00:00Z",
  "days_analyzed": 30,
  "overall_score": 72.5,
  "biological_age_years": 31,
  "chronological_age_years": 35,
  "confidence": 0.8,
  "components": {
    "cardio": {"score": 78.0, "weight": 0.20, "label": "Cardio & endurance", "data_points": 25},
    "strength": {"score": 65.0, "weight": 0.18, "label": "Force & muscle"},
    "sleep": {"score": 82.0, "weight": 0.20, "label": "Sommeil & récupération"},
    "nutrition": {"score": 70.0, "weight": 0.17, "label": "Nutrition"},
    "weight": {"score": 88.0, "weight": 0.10, "label": "Poids & IMC"},
    "body_composition": {"score": 75.0, "weight": 0.08, "label": "Composition corporelle"},
    "consistency": {"score": 60.0, "weight": 0.07, "label": "Consistance & discipline"}
  },
  "improvement_levers": ["strength", "consistency"],
  "summary": "Score calculé sur 30 jours. Âge biologique estimé : 31 ans vs 35 ans réels."
}
```

---

## LOT 3 — INTELLIGENCE SANTÉ

### GET /metrics/daily
**Auth**: Bearer JWT
**Query**: `?date=2026-03-07&force_recompute=false`
**Response 200**:
```json
{
  "id": "uuid",
  "metrics_date": "2026-03-07",
  "weight_kg": 78.5,
  "calories_consumed": 2150.0,
  "calories_target": 2400.0,
  "protein_g": 165.0,
  "protein_target_g": 180.0,
  "carbs_g": 220.0,
  "fat_g": 75.0,
  "fiber_g": 28.0,
  "hydration_ml": 2200,
  "hydration_target_ml": 2500,
  "steps": 8500,
  "active_calories_kcal": 420.0,
  "distance_km": 6.2,
  "resting_heart_rate_bpm": 58.0,
  "hrv_ms": 45.0,
  "sleep_minutes": 450,
  "sleep_score": 78.0,
  "sleep_quality_label": "good",
  "workout_count": 1,
  "total_tonnage_kg": 3200.0,
  "training_load": 65.0,
  "readiness_score": 72.0,
  "data_completeness_pct": 85.7,
  "updated_at": "2026-03-07T09:30:00Z"
}
```

### GET /metrics/history
**Auth**: Bearer JWT
**Query**: `?days=30` (1-90, défaut 30)
**Response 200**:
```json
{
  "history": [...],
  "days_requested": 30,
  "days_available": 28,
  "date_from": "2026-02-06",
  "date_to": "2026-03-07",
  "avg_readiness": 71.2,
  "avg_sleep_hours": 7.2,
  "avg_calories": 2180.0,
  "avg_steps": 8200,
  "avg_protein_g": 162.0,
  "weight_trend_kg": -1.2,
  "workout_frequency_pct": 57.1
}
```

### GET /insights
**Auth**: Bearer JWT
**Query**: `?days=30&category=sleep&severity=critical&include_dismissed=false`
**Catégories valides**: `nutrition`, `sleep`, `activity`, `recovery`, `training`, `hydration`, `weight`
**Sévérités valides**: `info`, `warning`, `critical`
**Response 200**:
```json
{
  "insights": [
    {
      "id": "uuid",
      "category": "sleep",
      "severity": "critical",
      "title": "Dette de sommeil chronique",
      "message": "Moins de 6h de sommeil sur 4 des 7 derniers jours. Récupération compromise.",
      "evidence": {"days_count": 4, "avg_hours": 5.5},
      "is_read": false,
      "is_dismissed": false,
      "created_at": "2026-03-07T07:00:00Z",
      "expires_at": "2026-03-14T07:00:00Z"
    }
  ],
  "total": 3,
  "unread_count": 2,
  "critical_count": 1,
  "by_category": {"sleep": 1, "nutrition": 1, "activity": 1},
  "by_severity": {"critical": 1, "warning": 2}
}
```

### POST /insights/run
**Auth**: Bearer JWT
**Query**: `?date=2026-03-07` (optionnel)
**Response 200**: même format que `GET /insights` (insights fraîchement générés)

### PATCH /insights/{insight_id}/read
**Auth**: Bearer JWT
**Response 200**: `InsightResponse` (is_read=true)

### PATCH /insights/{insight_id}/dismiss
**Auth**: Bearer JWT
**Response 200**: `InsightResponse` (is_dismissed=true, is_read=true)

### GET /health/plan/today
**Auth**: Bearer JWT
**Query**: `?date=2026-03-07` (optionnel)
**Response 200**:
```json
{
  "date": "2026-03-07",
  "generated_at": "2026-03-07T07:15:00Z",
  "workout_recommendation": {
    "type": "strength",
    "duration_minutes": 60,
    "intensity": "moderate",
    "location": "gym",
    "description": "Séance de force en salle — intensité modérée recommandée (récupération bonne)"
  },
  "protein_target_g": 180.0,
  "calorie_target": 2400.0,
  "hydration_target_ml": 2500.0,
  "steps_goal": 8000,
  "sleep_target_hours": 8.0,
  "readiness_level": "good",
  "recommended_intensity": "moderate",
  "alerts": [
    {"type": "hydration", "message": "Hydratation hier : 68% de l'objectif"}
  ],
  "daily_tips": [
    "Commencez la journée avec 500ml d'eau",
    "Ciblez 180g de protéines réparties sur 3-4 repas"
  ],
  "eating_window": {"start": "08:00", "end": "16:00", "protocol": "16:8"},
  "nutrition_focus": "Protéines — objectif non atteint hier (82%)"
}
```

### GET /nutrition/targets
**Auth**: Bearer JWT
**Query**: `?workout_type=strength&workout_duration_minutes=60&workout_rpe=7`
**Response 200**:
```json
{
  "calories_target": 2650.0,
  "protein_target_g": 171.0,
  "carbs_target_g": 265.5,
  "fat_target_g": 88.3,
  "fiber_target_g": 37.1,
  "hydration_target_ml": 2975.0,
  "protein_pct": 25.8,
  "carbs_pct": 40.1,
  "fat_pct": 30.0,
  "base_tdee_kcal": 2200.0,
  "workout_bonus_kcal": 250.0,
  "goal_adjustment_kcal": 200.0,
  "target_mode": "training_day",
  "eating_window_hours": 8.0,
  "fasting_start_at": "16:00",
  "reasoning": "BMR 1755 kcal × 1.550 (moderate) = TDEE 2720 kcal. Surplus de 250 kcal/jour pour prise de masse lean. Bonus entraînement strength (60 min) : +250 kcal."
}
```

### GET /nutrition/micronutrients
**Auth**: Bearer JWT
**Query**: `?date=2026-03-07&days=7`
**Response 200**:
```json
{
  "period_start": "2026-02-28",
  "period_end": "2026-03-07",
  "days": 7,
  "overall_micro_score": 62.3,
  "data_quality": "partial",
  "entries_with_micro_data_pct": 35.0,
  "analysis_note": "Estimation basée sur les groupes alimentaires (données micronutriments limitées).",
  "micronutrients": [
    {
      "key": "vitamin_d_mcg",
      "name": "Vitamin D",
      "name_fr": "Vitamine D",
      "unit": "mcg",
      "consumed": 5.2,
      "target": 20.0,
      "pct_of_target": 26.0,
      "status": "deficient",
      "food_sources": ["saumon", "maquereau", "thon", "jaune d'œuf"]
    }
  ],
  "top_deficiencies": ["Vitamine D", "Oméga-3", "Magnésium"]
}
```

### GET /nutrition/supplements/recommendations
**Auth**: Bearer JWT
**Response 200**:
```json
{
  "recommendations": [
    {
      "name": "Vitamine D3",
      "category": "vitamin",
      "confidence": "high",
      "dosage": "2000-4000 UI/jour",
      "timing": "Avec un repas contenant des graisses",
      "rationale": "Apport estimé très faible (26% de l'AJR). Déficit très fréquent en Europe.",
      "warnings": ["Consulter un médecin avant de dépasser 4000 UI/jour"],
      "evidence_level": "strong"
    }
  ],
  "analysis_basis": "Analyse basée sur 7 jours de journal alimentaire. Score micronutritionnel : 62/100.",
  "generated_at": "2026-03-07T09:00:00Z"
}
```

---

---

## LOT 5 — STABILISATION

### Champs ajoutés aux réponses existantes

#### GET /metrics/daily — champ ajouté
```json
{
  "...": "...",
  "algorithm_version": "v1.0"
}
```

#### GET /scores/longevity — champ ajouté
```json
{
  "...": "...",
  "algorithm_version": "v1.0"
}
```

#### GET /health/plan/today — champ ajouté
```json
{
  "date": "2026-03-07",
  "...": "...",
  "from_cache": false
}
```
- `from_cache: true` → plan servi depuis `DailyRecommendation` (< 6h, fast path)
- `from_cache: false` → plan fraîchement calculé et persisté

---

### GET /home/summary
**Auth**: Bearer JWT
**Query**: `?date=2026-03-07` (optionnel, défaut : aujourd'hui)
**Description**: Agrégateur de démarrage de l'app mobile. Réduit 5 appels API en 1. Déclenche un lazy compute des métriques du jour si absent.

**Response 200**:
```json
{
  "summary_date": "2026-03-07",
  "generated_at": "2026-03-07T08:00:00Z",
  "unread_insights_count": 2,
  "has_active_plan": true,

  "metrics": {
    "metrics_date": "2026-03-07",
    "weight_kg": 78.5,
    "calories_consumed": 2150.0,
    "calories_target": 2400.0,
    "protein_g": 165.0,
    "protein_target_g": 180.0,
    "hydration_ml": 2200,
    "hydration_target_ml": 2500,
    "steps": 8500,
    "sleep_minutes": 450,
    "sleep_quality_label": "good",
    "hrv_ms": 45.0,
    "workout_count": 1,
    "readiness_score": 72.0,
    "data_completeness_pct": 85.7
  },

  "readiness": {
    "overall_readiness": 72.0,
    "recommended_intensity": "moderate",
    "readiness_level": "good"
  },

  "unread_insights": [
    {
      "id": "uuid",
      "category": "sleep",
      "severity": "warning",
      "message": "Dette de sommeil détectée sur 3 des 7 derniers jours."
    }
  ],

  "plan": {
    "readiness_level": "good",
    "recommended_intensity": "moderate",
    "protein_target_g": 180.0,
    "calorie_target": 2400.0,
    "steps_goal": 8000,
    "workout_recommendation": {
      "type": "strength",
      "duration_minutes": 60,
      "intensity": "moderate",
      "location": "gym",
      "description": "Séance de force en salle"
    },
    "daily_tips": ["Commencez avec 500ml d'eau", "Ciblez 180g de protéines"],
    "alerts": [],
    "from_cache": true
  },

  "longevity": {
    "longevity_score": 72.5,
    "biological_age_estimate": 31
  }
}
```

**Notes**:
- `metrics` peut être `null` si les données du jour sont introuvables même après lazy compute
- `readiness` peut être `null` si aucun score calculé ce jour
- `plan` peut être `null` si aucun `DailyRecommendation` en cache (le plan n'est pas généré ici)
- `longevity` retourne la **dernière entrée disponible** (pas forcément aujourd'hui)
- `unread_insights` : max 5 insights, triés par `detected_at` desc

---

## RAPPORTS

### GET /reports/weekly?date=2026-03-07
### GET /reports/monthly?year=2026&month=3

---

## Codes de retour

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 201 | Créé |
| 202 | Accepté (async) |
| 400 | Données invalides |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Ressource introuvable |
| 409 | Conflit (doublon) |
| 422 | Validation Pydantic échouée |
| 500 | Erreur serveur |

## Format d'erreur standard
```json
{
  "detail": "Message d'erreur humain",
  "code": "VALIDATION_ERROR",
  "fields": { "weight_kg": "Must be positive" }
}
```

---

## LOT 18 — PRODUCTIZATION & DAILY EXPERIENCE ENGINE

### POST /profile/onboarding
**Auth**: Bearer JWT
**Body**:
```json
{
  "first_name": "Alice",
  "age": 28,
  "sex": "female",
  "height_cm": 165.0,
  "weight_kg": 62.0,
  "goal_weight_kg": 58.0,
  "primary_goal": "weight_loss",
  "activity_level": "moderate",
  "sport_frequency_per_week": 3,
  "estimated_sleep_quality": "good",
  "sleep_hours_per_night": 7.5,
  "has_biomarker_access": false,
  "fitness_level": "intermediate"
}
```
**Response 200**:
```json
{
  "profile_updated": true,
  "body_metric_logged": true,
  "initial_targets": {
    "calories_target_kcal": 1850.0,
    "protein_target_g": 105.0,
    "hydration_target_ml": 2400,
    "steps_goal": 10000,
    "sleep_hours_target": 7.5
  },
  "next_step": "view_briefing",
  "coach_welcome_message": "Bienvenue dans SOMA..."
}
```
**Notes**: Idempotent (peut être rappelé pour mise à jour profil).

---

### GET /daily/briefing
**Auth**: Bearer JWT
**Query**: `?date=2026-03-08` (optionnel, défaut = aujourd'hui)
**Response 200**:
```json
{
  "briefing_date": "2026-03-08",
  "generated_at": "2026-03-08T07:30:00Z",
  "readiness_score": 72.0,
  "readiness_level": "good",
  "readiness_color": "#34C759",
  "sleep_duration_h": 7.25,
  "sleep_quality_label": "good",
  "training_type": "strength",
  "training_intensity": "moderate",
  "training_duration_min": 60,
  "calorie_target": 2200.0,
  "protein_target_g": 165.0,
  "carb_target_g": 240.0,
  "hydration_target_ml": 2800,
  "twin_status": "good",
  "twin_primary_concern": "léger déficit énergétique",
  "alerts": ["ACWR à surveiller (1.42)", "Sommeil court hier (6.5h)"],
  "top_insight": "Votre récupération est optimale pour une séance de force aujourd'hui.",
  "coach_tip": "Après votre séance, consommez 40g de protéines dans les 30 minutes..."
}
```

---

### POST /coach/quick-advice
**Auth**: Bearer JWT
**Body**: `{ "question": "Dois-je m'entraîner aujourd'hui ?" }`
**Response 200**:
```json
{
  "answer": "Avec un score de readiness à 72%, vous êtes en bonne forme pour vous entraîner.",
  "recommendations": [
    "Optez pour une séance de force modérée (45-60 min)",
    "Consommez 165g de protéines aujourd'hui"
  ],
  "alert": null,
  "confidence": 0.78,
  "model_used": "claude-3-haiku-20240307",
  "context_summary": "readiness: 72%, fatigue: 35%, twin: good"
}
```
**Notes**: Pas de persistence DB. Réponse courte (2 phrases max + 2 recommandations).

---

### POST /analytics/event
**Auth**: Bearer JWT
**Body**: `{ "event_name": "workout_logged", "properties": { "type": "strength", "duration": 45 } }`
**Response 201**: `{ "status": "tracked" }`
**Events valides**: `app_open`, `morning_briefing_view`, `journal_entry`, `coach_question`, `workout_logged`, `nutrition_logged`, `insight_viewed`, `onboarding_complete`, `quick_advice_requested`
**Notes**: Fire-and-forget côté serveur. Jamais bloquant.
