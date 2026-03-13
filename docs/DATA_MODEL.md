# SOMA — Modèle de Données Complet

## Conventions
- `id`: UUID v4 (primary key)
- `created_at`, `updated_at`: timestamps automatiques
- Toutes les tables ont un `is_deleted` soft-delete
- Unités : SI (kg, cm, kcal, ml, bpm, minutes)
- `data_quality`: enum ('exact', 'estimated', 'inferred')

---

## MODULE A — PROFIL UTILISATEUR

### Table: `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `user_profiles`
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    age INTEGER,
    birth_date DATE,
    sex VARCHAR(10),               -- 'male', 'female', 'other'
    height_cm FLOAT,
    -- Objectifs
    goal_weight_kg FLOAT,
    primary_goal VARCHAR(50),      -- 'weight_loss', 'muscle_gain', 'maintenance', 'performance', 'longevity'
    -- Niveau
    activity_level VARCHAR(20),    -- 'sedentary', 'light', 'moderate', 'active', 'very_active'
    fitness_level VARCHAR(20),     -- 'beginner', 'intermediate', 'advanced', 'athlete'
    -- Contraintes
    physical_constraints TEXT[],   -- ['lower_back_pain', 'knee_issues', ...]
    -- Alimentation
    dietary_regime VARCHAR(50),    -- 'omnivore', 'vegetarian', 'vegan', 'keto', 'paleo', ...
    food_allergies TEXT[],
    food_intolerances TEXT[],
    intermittent_fasting BOOLEAN DEFAULT FALSE,
    fasting_protocol VARCHAR(50),  -- '16:8', '23:1', '5:2', 'omad'
    meals_per_day INTEGER DEFAULT 3,
    -- Préférences timing
    preferred_training_time VARCHAR(20),  -- 'morning', 'afternoon', 'evening'
    usual_wake_time TIME,
    usual_sleep_time TIME,
    -- Ressenti
    avg_energy_level INTEGER,      -- 1-10
    perceived_sleep_quality INTEGER, -- 1-10
    -- Équipement disponible
    home_equipment TEXT[],         -- ['dumbbells', 'resistance_bands', 'pull_up_bar', ...]
    gym_access BOOLEAN DEFAULT FALSE,
    gym_equipment TEXT[],
    -- Champs calculés (dénormalisés pour perf)
    bmi FLOAT,
    bmr_kcal FLOAT,                -- Métabolisme basal (Mifflin-St Jeor)
    tdee_kcal FLOAT,               -- Dépense énergétique totale estimée
    target_calories_kcal FLOAT,
    target_protein_g FLOAT,
    target_hydration_ml FLOAT,
    profile_completeness_score FLOAT, -- 0-100
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

### Table: `body_metrics`
```sql
CREATE TABLE body_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    measured_at TIMESTAMPTZ NOT NULL,
    weight_kg FLOAT,
    body_fat_pct FLOAT,
    muscle_mass_kg FLOAT,
    waist_cm FLOAT,
    hip_cm FLOAT,
    neck_cm FLOAT,
    source VARCHAR(50),            -- 'manual', 'apple_health', 'garmin', 'withings'
    data_quality VARCHAR(20) DEFAULT 'exact',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_body_metrics_user_date ON body_metrics(user_id, measured_at DESC);
```

---

## MODULE B — INTÉGRATIONS SANTÉ

### Table: `health_data_sources`
```sql
CREATE TABLE health_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50),       -- 'apple_health', 'google_health', 'garmin', 'polar', 'withings'
    source_name VARCHAR(100),
    is_connected BOOLEAN DEFAULT FALSE,
    last_sync_at TIMESTAMPTZ,
    permissions_granted TEXT[],    -- liste des permissions accordées
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `health_import_jobs`
```sql
CREATE TABLE health_import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source_id UUID REFERENCES health_data_sources(id),
    job_type VARCHAR(50),          -- 'full_sync', 'incremental'
    status VARCHAR(20),            -- 'pending', 'running', 'success', 'failed'
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    records_imported INTEGER,
    records_skipped INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `health_samples`
```sql
CREATE TABLE health_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sample_type VARCHAR(50) NOT NULL, -- 'steps', 'heart_rate', 'hrv', 'spo2', 'active_calories',
                                       -- 'resting_heart_rate', 'vo2_max', 'stand_hours',
                                       -- 'respiratory_rate', 'body_temperature'
    value FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,        -- 'count', 'bpm', 'ms', 'pct', 'kcal', 'ml/kg/min', '°C'
    recorded_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(50),
    data_quality VARCHAR(20) DEFAULT 'exact',
    external_id VARCHAR(255),         -- ID dans la source externe (pour déduplication)
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_health_samples_user_type_date ON health_samples(user_id, sample_type, recorded_at DESC);
CREATE UNIQUE INDEX idx_health_samples_dedup ON health_samples(user_id, sample_type, recorded_at, source);
```

---

## MODULE N — SOMMEIL

### Table: `sleep_sessions`
```sql
CREATE TABLE sleep_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    -- Phases (si disponibles)
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,
    light_sleep_minutes INTEGER,
    awake_minutes INTEGER,
    -- Métriques
    avg_heart_rate_bpm FLOAT,
    avg_hrv_ms FLOAT,
    sleep_score INTEGER,           -- 0-100
    -- Source
    source VARCHAR(50),
    data_quality VARCHAR(20) DEFAULT 'exact',
    -- Subjectif
    perceived_quality INTEGER,     -- 1-5
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sleep_sessions_user_date ON sleep_sessions(user_id, start_at DESC);
```

---

## MODULE M — HYDRATATION

### Table: `hydration_logs`
```sql
CREATE TABLE hydration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    logged_at TIMESTAMPTZ NOT NULL,
    volume_ml INTEGER NOT NULL,
    beverage_type VARCHAR(50) DEFAULT 'water', -- 'water', 'coffee', 'tea', 'juice', 'sport_drink'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_hydration_logs_user_date ON hydration_logs(user_id, logged_at DESC);
```

---

## MODULES H/I — NUTRITION

### Table: `food_items`
```sql
CREATE TABLE food_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),
    barcode VARCHAR(50),
    -- Macros pour 100g
    calories_per_100g FLOAT,
    protein_g_per_100g FLOAT,
    carbs_g_per_100g FLOAT,
    fat_g_per_100g FLOAT,
    fiber_g_per_100g FLOAT,
    sugar_g_per_100g FLOAT,
    -- Micronutriments pour 100g (JSONB pour flexibilité)
    micronutrients JSONB,          -- {vitamin_d_ug: 5.2, vitamin_b12_ug: 1.1, iron_mg: 3.5, ...}
    -- Classification
    food_group VARCHAR(50),        -- 'protein', 'vegetable', 'fruit', 'grain', 'dairy', 'fat', 'processed'
    is_ultra_processed BOOLEAN DEFAULT FALSE,
    nova_score INTEGER,            -- 1-4 (classification NOVA)
    -- Source
    source VARCHAR(50),            -- 'openfoodfacts', 'usda', 'manual', 'ai_estimated'
    external_id VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_food_items_name ON food_items USING gin(to_tsvector('french', name));
CREATE INDEX idx_food_items_barcode ON food_items(barcode);
```

### Table: `nutrition_photos`
```sql
CREATE TABLE nutrition_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    photo_path VARCHAR(500) NOT NULL,
    taken_at TIMESTAMPTZ NOT NULL,
    -- Résultat analyse IA
    ai_analysis JSONB,             -- Résultat brut du modèle IA
    identified_foods JSONB,        -- [{name, quantity_g, confidence}, ...]
    estimated_calories FLOAT,
    estimated_protein_g FLOAT,
    estimated_carbs_g FLOAT,
    estimated_fat_g FLOAT,
    confidence_score FLOAT,        -- 0-1
    -- Validation utilisateur
    user_validated BOOLEAN DEFAULT FALSE,
    user_corrections JSONB,
    -- Statut
    analysis_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'analyzed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `nutrition_entries`
```sql
CREATE TABLE nutrition_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    logged_at TIMESTAMPTZ NOT NULL,
    meal_type VARCHAR(30),         -- 'breakfast', 'lunch', 'dinner', 'snack', 'supplement', 'drink'
    -- Source
    food_item_id UUID REFERENCES food_items(id),
    photo_id UUID REFERENCES nutrition_photos(id),
    -- Quantité et valeurs
    quantity_g FLOAT,
    calories FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    fiber_g FLOAT,
    micronutrients JSONB,
    -- Données observées
    data_quality VARCHAR(20),      -- 'exact', 'estimated', 'inferred'
    -- Contexte
    hunger_before INTEGER,         -- 1-10
    satiety_after INTEGER,         -- 1-10
    energy_after INTEGER,          -- 1-10
    notes TEXT,
    -- Fenêtre de jeûne intermittent
    fasting_window_broken BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_nutrition_entries_user_date ON nutrition_entries(user_id, logged_at DESC);
```

---

## MODULES D/G — SPORT

### Table: `exercise_library`
```sql
CREATE TABLE exercise_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),
    category VARCHAR(50),          -- 'strength', 'cardio', 'mobility', 'balance', 'hiit'
    -- Muscles
    primary_muscles TEXT[],        -- ['quadriceps', 'glutes', ...]
    secondary_muscles TEXT[],
    -- Paramètres
    difficulty_level VARCHAR(20),  -- 'beginner', 'intermediate', 'advanced'
    equipment_required TEXT[],     -- ['barbell', 'dumbbells', 'machine', 'bodyweight', ...]
    execution_location VARCHAR(20), -- 'gym', 'home', 'outdoor', 'any'
    -- Instructions
    description TEXT,
    instructions TEXT[],           -- Étapes de l'exercice
    breathing_cues TEXT,
    common_errors TEXT[],
    -- Média
    image_urls TEXT[],
    video_url VARCHAR(500),
    -- Variantes
    easier_variant_id UUID REFERENCES exercise_library(id),
    harder_variant_id UUID REFERENCES exercise_library(id),
    -- Analyse vidéo
    key_joint_angles JSONB,        -- Points de référence pour analyse posture
    cv_supported BOOLEAN DEFAULT FALSE, -- Computer vision disponible
    rep_detection_model VARCHAR(50),
    -- Contre-indications
    contraindications TEXT[],
    -- Métriques
    met_value FLOAT,               -- Metabolic Equivalent of Task
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `workout_sessions`
```sql
CREATE TABLE workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    session_type VARCHAR(50),      -- 'strength', 'cardio', 'hiit', 'mobility', 'walk', 'elliptical'
    location VARCHAR(50),          -- 'gym', 'home', 'outdoor'
    -- Volume
    total_tonnage_kg FLOAT,        -- Tonnage total (poids × reps)
    total_sets INTEGER,
    total_reps INTEGER,
    -- Cardio
    distance_km FLOAT,
    avg_heart_rate_bpm FLOAT,
    max_heart_rate_bpm FLOAT,
    calories_burned_kcal FLOAT,
    -- Charge d'entraînement
    internal_load_score FLOAT,     -- RPE × durée
    rpe_score FLOAT,               -- Rate of Perceived Exertion (1-10)
    -- Ressenti
    energy_before INTEGER,         -- 1-10
    energy_after INTEGER,
    perceived_difficulty INTEGER,  -- 1-10
    technical_score FLOAT,         -- Score de qualité technique (module F)
    -- Notes
    notes TEXT,
    -- Source (manuel vs programme généré)
    program_session_id UUID,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_workout_sessions_user_date ON workout_sessions(user_id, started_at DESC);
```

### Table: `workout_exercises`
```sql
CREATE TABLE workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercise_library(id),
    exercise_order INTEGER,
    notes TEXT,
    -- Analyse vidéo globale
    biomechanics_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `workout_sets`
```sql
CREATE TABLE workout_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_exercise_id UUID REFERENCES workout_exercises(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL,
    reps_target INTEGER,
    reps_actual INTEGER,
    weight_kg FLOAT,
    duration_seconds INTEGER,      -- Pour exercices isométriques, cardio
    rest_seconds INTEGER,
    -- Métriques avancées (Computer Vision)
    tempo VARCHAR(20),             -- '3-1-2' (excentrique-iso-concentrique)
    time_under_tension_s FLOAT,
    range_of_motion_pct FLOAT,     -- % de l'amplitude cible atteinte
    -- Qualité
    rpe_set FLOAT,                 -- RPE par série (1-10)
    is_warmup BOOLEAN DEFAULT FALSE,
    is_pr BOOLEAN DEFAULT FALSE,   -- Personal Record
    -- Source
    data_source VARCHAR(20) DEFAULT 'manual', -- 'manual', 'camera', 'estimated'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `exercise_analysis`
```sql
CREATE TABLE exercise_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_exercise_id UUID REFERENCES workout_exercises(id),
    -- Données Camera
    video_path VARCHAR(500),
    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
    -- Résultats pose estimation
    pose_landmarks JSONB,          -- Raw MediaPipe output
    rep_timestamps JSONB,          -- [{rep: 1, start_ms: 0, end_ms: 2300, ...}]
    reps_detected INTEGER,
    -- Scores
    symmetry_score FLOAT,          -- 0-100
    amplitude_score FLOAT,
    stability_score FLOAT,
    alignment_score FLOAT,
    overall_technique_score FLOAT,
    -- Erreurs détectées
    errors_detected TEXT[],
    -- Comparaison ref
    vs_reference_pose JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## MODULE O — JUMEAU MÉTABOLIQUE

### Table: `metabolic_state_snapshots`
```sql
CREATE TABLE metabolic_state_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    -- Métabolisme
    estimated_bmr_kcal FLOAT,
    estimated_tdee_kcal FLOAT,
    -- Glycogène (estimation)
    estimated_glycogen_g FLOAT,    -- 0-500g environ
    glycogen_status VARCHAR(20),   -- 'depleted', 'low', 'normal', 'high'
    -- État
    fatigue_score FLOAT,           -- 0-100
    recovery_score FLOAT,          -- 0-100
    readiness_score FLOAT,         -- 0-100
    training_load_7d FLOAT,        -- Charge cumulative 7 jours
    training_load_28d FLOAT,
    -- Disponibilité énergétique
    energy_availability_kcal FLOAT, -- (apports - dépense sport) / masse maigre
    -- Estimations avancées (Module T)
    estimated_glucose_mg_dl FLOAT,
    estimated_cortisol_level FLOAT, -- relatif, 0-100
    estimated_neural_fatigue FLOAT,
    injury_risk_score FLOAT,       -- 0-100
    -- Hormonal (estimation qualitative)
    hormonal_balance_signal VARCHAR(20), -- 'optimal', 'stress', 'underrecovery', 'underfed'
    -- Confiance
    confidence_score FLOAT,        -- 0-1
    variables_used TEXT[],
    -- Signaux sources
    sleep_quality_input FLOAT,
    hrv_input FLOAT,
    resting_hr_input FLOAT,
    training_load_input FLOAT,
    nutrition_input FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, snapshot_date)
);
CREATE INDEX idx_metabolic_snapshots_user_date ON metabolic_state_snapshots(user_id, snapshot_date DESC);
```

---

## MODULE Q — SCORES

### Table: `readiness_scores`
```sql
CREATE TABLE readiness_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    -- Scores composants
    sleep_score FLOAT,             -- 0-100
    recovery_score FLOAT,
    training_load_score FLOAT,
    hrv_score FLOAT,
    nutrition_score FLOAT,
    hydration_score FLOAT,
    -- Score global
    overall_readiness FLOAT,       -- 0-100
    recommended_intensity VARCHAR(20), -- 'rest', 'light', 'moderate', 'normal', 'push'
    -- Traçabilité
    reasoning TEXT,
    variables_used JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, score_date)
);
```

### Table: `longevity_scores`
```sql
CREATE TABLE longevity_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    -- Composants
    cardio_score FLOAT,            -- VO2max, zone 2
    strength_score FLOAT,          -- Volume musculation, force relative
    sleep_score FLOAT,
    nutrition_score FLOAT,
    weight_score FLOAT,
    body_comp_score FLOAT,
    consistency_score FLOAT,       -- Régularité des habitudes
    -- Score global et âge biologique
    longevity_score FLOAT,         -- 0-100
    biological_age_estimate FLOAT,
    -- Tendances
    trend_30d FLOAT,               -- +/- vs 30j avant
    trend_90d FLOAT,
    -- Top leviers
    top_improvement_levers JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, score_date)
);
```

---

## MODULE R — RECOMMANDATIONS IA

### Table: `daily_recommendations`
```sql
CREATE TABLE daily_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    recommendation_date DATE NOT NULL,
    -- Briefing matin
    morning_briefing TEXT,
    -- Plan du jour
    daily_plan JSONB,              -- {workout, nutrition, hydration, ...}
    workout_recommendation JSONB,  -- type, durée, intensité, exercices
    nutrition_strategy JSONB,      -- calories, macros, timing
    hydration_target_ml INTEGER,
    -- Alertes
    alerts JSONB,                  -- [{type, severity, message, action}, ...]
    -- Synthèse soir
    evening_summary TEXT,
    -- Méta
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    model_used VARCHAR(100),
    reasoning JSONB,
    UNIQUE(user_id, recommendation_date)
);
```

### Table: `supplement_recommendations`
```sql
CREATE TABLE supplement_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    supplement_name VARCHAR(100) NOT NULL,
    goal TEXT,
    reason TEXT,
    observed_data_basis TEXT,
    confidence_level FLOAT,        -- 0-1
    evidence_type VARCHAR(30),     -- 'data_observed', 'hypothesis', 'pattern'
    suggested_dose VARCHAR(100),
    suggested_timing VARCHAR(100),
    trial_duration_weeks INTEGER,
    precautions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## MODULE U — APPRENTISSAGE

### Table: `adherence_logs`
```sql
CREATE TABLE adherence_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    log_date DATE NOT NULL,
    recommendation_id UUID REFERENCES daily_recommendations(id),
    -- Adhérence
    workout_done BOOLEAN,
    workout_compliance_pct FLOAT,  -- % du programme réalisé
    nutrition_compliance_pct FLOAT,
    hydration_compliance_pct FLOAT,
    sleep_goal_met BOOLEAN,
    steps_goal_met BOOLEAN,
    -- Résultats mesurés le lendemain
    next_day_energy INTEGER,       -- 1-10
    next_day_performance FLOAT,    -- vs moyenne
    weight_delta_kg FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `user_feedback`
```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    feedback_type VARCHAR(50),     -- 'recommendation_rating', 'exercise_difficulty', 'meal_accuracy'
    reference_id UUID,             -- ID de l'élément évalué
    rating INTEGER,                -- 1-5
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## MODULE W — OBJECTIFS ET RAPPORTS

### Table: `goals`
```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    goal_type VARCHAR(50),         -- 'weight', 'body_fat', 'steps', 'workout_frequency', 'nutrition', 'sleep'
    target_value FLOAT,
    target_unit VARCHAR(20),
    start_value FLOAT,
    start_date DATE,
    target_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    is_achieved BOOLEAN DEFAULT FALSE,
    achieved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `reports`
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    report_type VARCHAR(20),       -- 'weekly', 'monthly', 'quarterly'
    period_start DATE,
    period_end DATE,
    content JSONB,                 -- Rapport complet en JSON
    generated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## MODULE LOT 3 — INTELLIGENCE SANTÉ

### Table: `daily_metrics`
```sql
-- Snapshot journalier agrégé de toutes les métriques santé.
-- Alimenté par le daily_metrics_service (upsert avec cache 2h).
-- Source unique de vérité pour l'Insight Engine et le Longevity Engine.
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    metrics_date DATE NOT NULL,

    -- Anthropométrie
    weight_kg FLOAT,                    -- Dernier poids connu avant fin de journée

    -- Nutrition (depuis nutrition_entries)
    calories_consumed FLOAT,
    calories_target FLOAT,              -- Depuis UserProfile
    protein_g FLOAT,
    protein_target_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    fiber_g FLOAT,
    meal_count INTEGER,

    -- Hydratation (depuis hydration_logs)
    hydration_ml INTEGER,
    hydration_target_ml INTEGER,

    -- Activité (depuis health_samples)
    steps INTEGER,
    active_calories_kcal FLOAT,
    distance_km FLOAT,

    -- Biomarqueurs (depuis health_samples)
    resting_heart_rate_bpm FLOAT,      -- Moyenne journalière
    hrv_ms FLOAT,                       -- Moyenne journalière

    -- Sommeil (depuis sleep_sessions — nuit précédente)
    sleep_minutes INTEGER,
    sleep_score FLOAT,
    sleep_quality_label VARCHAR(20),    -- 'excellent' | 'good' | 'fair' | 'poor'

    -- Entraînement (depuis workout_sessions)
    workout_count INTEGER DEFAULT 0,
    total_tonnage_kg FLOAT,
    training_load FLOAT,

    -- Récupération (depuis readiness_scores)
    readiness_score FLOAT,

    -- Meta
    data_completeness_pct FLOAT,        -- % des 7 champs clés renseignés
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, metrics_date)
);

CREATE INDEX idx_daily_metrics_user_date ON daily_metrics(user_id, metrics_date DESC);
```

### Table: `insights`
```sql
-- Insights détectés par l'Insight Engine sur les patterns des 7 derniers jours.
-- Upsert par contrainte unique (user_id, category, period_start, period_end).
-- Expiration automatique à 7 jours après détection.
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Classification
    category VARCHAR(50) NOT NULL,      -- 'nutrition'|'sleep'|'activity'|'recovery'|'training'|'hydration'|'weight'
    severity VARCHAR(20) NOT NULL,      -- 'info' | 'warning' | 'critical'
    period_start DATE NOT NULL,         -- Début de la fenêtre analysée
    period_end DATE NOT NULL,           -- Fin de la fenêtre analysée

    -- Contenu
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    evidence JSONB,                     -- Données brutes ayant déclenché l'insight (avg, count, ACWR...)

    -- Statut
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,

    -- Expiration
    expires_at TIMESTAMPTZ,             -- Généralement created_at + 7 jours

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, category, period_start, period_end)
);

CREATE INDEX idx_insights_user_active ON insights(user_id, is_dismissed, expires_at);
CREATE INDEX idx_insights_user_category ON insights(user_id, category, severity);
```

---

## INDEXES GLOBAUX

```sql
-- Performances générales
CREATE INDEX idx_health_samples_type ON health_samples(sample_type, recorded_at DESC);
CREATE INDEX idx_nutrition_user_meal ON nutrition_entries(user_id, meal_type, logged_at DESC);
CREATE INDEX idx_workout_user_type ON workout_sessions(user_id, session_type, started_at DESC);

-- LOT 3 — Intelligence santé
CREATE INDEX idx_daily_metrics_user_date ON daily_metrics(user_id, metrics_date DESC);
CREATE INDEX idx_insights_user_active ON insights(user_id, is_dismissed, expires_at);
```

## EXTENSIONS PostgreSQL

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Recherche texte approximative
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- Chiffrement
```
