-- =============================================================================
-- SOMA -- Consolidated migrations V001 to V015
-- Generated from Alembic upgrade() functions
-- Target: PostgreSQL 15 / Supabase (idempotent, IF NOT EXISTS everywhere)
-- =============================================================================

-- =============================================================================
-- V001 -- Initial schema
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email)
);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    age INTEGER,
    birth_date DATE,
    sex VARCHAR(10),
    height_cm FLOAT,
    goal_weight_kg FLOAT,
    primary_goal VARCHAR(50),
    physical_constraints TEXT[],
    activity_level VARCHAR(20),
    fitness_level VARCHAR(20),
    dietary_regime VARCHAR(50),
    food_allergies TEXT[],
    food_intolerances TEXT[],
    intermittent_fasting BOOLEAN NOT NULL DEFAULT false,
    fasting_protocol VARCHAR(50),
    meals_per_day INTEGER NOT NULL DEFAULT 3,
    preferred_training_time VARCHAR(20),
    usual_wake_time TIME,
    usual_sleep_time TIME,
    avg_energy_level INTEGER,
    perceived_sleep_quality INTEGER,
    home_equipment TEXT[],
    gym_access BOOLEAN NOT NULL DEFAULT false,
    gym_equipment TEXT[],
    bmi FLOAT,
    bmr_kcal FLOAT,
    tdee_kcal FLOAT,
    target_calories_kcal FLOAT,
    target_protein_g FLOAT,
    target_hydration_ml FLOAT,
    profile_completeness_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_user_profiles_user_id ON user_profiles(user_id);

CREATE TABLE IF NOT EXISTS body_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measured_at TIMESTAMPTZ NOT NULL,
    weight_kg FLOAT,
    body_fat_pct FLOAT,
    muscle_mass_kg FLOAT,
    waist_cm FLOAT,
    hip_cm FLOAT,
    neck_cm FLOAT,
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    data_quality VARCHAR(20) NOT NULL DEFAULT 'exact',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_body_metrics_user_date ON body_metrics(user_id, measured_at);

CREATE TABLE IF NOT EXISTS health_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(100),
    is_connected BOOLEAN NOT NULL DEFAULT false,
    last_sync_at TIMESTAMPTZ,
    permissions_granted TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_health_data_sources_user_id ON health_data_sources(user_id);

CREATE TABLE IF NOT EXISTS health_import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    source_id UUID REFERENCES health_data_sources(id),
    job_type VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    records_imported INTEGER,
    records_skipped INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS health_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sample_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(50),
    data_quality VARCHAR(20) NOT NULL DEFAULT 'exact',
    external_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_health_samples_dedup UNIQUE (user_id, sample_type, recorded_at, source)
);
CREATE INDEX IF NOT EXISTS ix_health_samples_user_type_date ON health_samples(user_id, sample_type, recorded_at);

CREATE TABLE IF NOT EXISTS sleep_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,
    light_sleep_minutes INTEGER,
    awake_minutes INTEGER,
    avg_heart_rate_bpm FLOAT,
    avg_hrv_ms FLOAT,
    sleep_score INTEGER,
    source VARCHAR(50),
    data_quality VARCHAR(20) NOT NULL DEFAULT 'exact',
    perceived_quality INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sleep_sessions_user_date ON sleep_sessions(user_id, start_at);

CREATE TABLE IF NOT EXISTS hydration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_at TIMESTAMPTZ NOT NULL,
    volume_ml INTEGER NOT NULL,
    beverage_type VARCHAR(50) NOT NULL DEFAULT 'water',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_hydration_logs_user_date ON hydration_logs(user_id, logged_at);

CREATE TABLE IF NOT EXISTS exercise_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),
    slug VARCHAR(100),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    primary_muscles TEXT[],
    secondary_muscles TEXT[],
    difficulty_level VARCHAR(20),
    equipment_required TEXT[],
    execution_location VARCHAR(20),
    description TEXT,
    instructions TEXT[],
    breathing_cues TEXT,
    common_errors TEXT[],
    image_urls TEXT[],
    video_url VARCHAR(500),
    easier_variant_id UUID REFERENCES exercise_library(id),
    harder_variant_id UUID REFERENCES exercise_library(id),
    key_joint_angles JSONB,
    cv_supported BOOLEAN NOT NULL DEFAULT false,
    rep_detection_model VARCHAR(50),
    contraindications TEXT[],
    met_value FLOAT,
    format_type VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_exercise_library_slug UNIQUE (slug)
);
CREATE INDEX IF NOT EXISTS ix_exercise_library_name ON exercise_library(name);
CREATE INDEX IF NOT EXISTS ix_exercise_library_category ON exercise_library(category);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    session_type VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    location VARCHAR(50),
    total_tonnage_kg FLOAT,
    total_sets INTEGER,
    total_reps INTEGER,
    distance_km FLOAT,
    avg_heart_rate_bpm FLOAT,
    max_heart_rate_bpm FLOAT,
    calories_burned_kcal FLOAT,
    internal_load_score FLOAT,
    rpe_score FLOAT,
    energy_before INTEGER,
    energy_after INTEGER,
    perceived_difficulty INTEGER,
    technical_score FLOAT,
    notes TEXT,
    is_completed BOOLEAN NOT NULL DEFAULT false,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_workout_sessions_user_date ON workout_sessions(user_id, started_at);
CREATE INDEX IF NOT EXISTS ix_workout_sessions_status ON workout_sessions(user_id, status);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercise_library(id),
    exercise_order INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    biomechanics_score FLOAT,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_workout_exercises_session_id ON workout_exercises(session_id);

CREATE TABLE IF NOT EXISTS workout_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_exercise_id UUID NOT NULL REFERENCES workout_exercises(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL,
    reps_target INTEGER,
    reps_actual INTEGER,
    weight_kg FLOAT,
    duration_seconds INTEGER,
    rest_seconds INTEGER,
    tempo VARCHAR(20),
    time_under_tension_s FLOAT,
    range_of_motion_pct FLOAT,
    rpe_set FLOAT,
    is_warmup BOOLEAN NOT NULL DEFAULT false,
    is_pr BOOLEAN NOT NULL DEFAULT false,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    data_source VARCHAR(20) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_workout_sets_exercise_id ON workout_sets(workout_exercise_id);

CREATE TABLE IF NOT EXISTS food_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),
    barcode VARCHAR(50),
    calories_per_100g FLOAT,
    protein_g_per_100g FLOAT,
    carbs_g_per_100g FLOAT,
    fat_g_per_100g FLOAT,
    fiber_g_per_100g FLOAT,
    sugar_g_per_100g FLOAT,
    micronutrients JSONB,
    food_group VARCHAR(50),
    is_ultra_processed BOOLEAN NOT NULL DEFAULT false,
    nova_score INTEGER,
    source VARCHAR(50),
    external_id VARCHAR(100),
    verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_food_items_name ON food_items(name);
CREATE INDEX IF NOT EXISTS ix_food_items_barcode ON food_items(barcode);

CREATE TABLE IF NOT EXISTS nutrition_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    photo_path VARCHAR(500) NOT NULL,
    taken_at TIMESTAMPTZ NOT NULL,
    ai_analysis JSONB,
    identified_foods JSONB,
    estimated_calories FLOAT,
    estimated_protein_g FLOAT,
    estimated_carbs_g FLOAT,
    estimated_fat_g FLOAT,
    confidence_score FLOAT,
    user_validated BOOLEAN NOT NULL DEFAULT false,
    user_corrections JSONB,
    analysis_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_nutrition_photos_user_id ON nutrition_photos(user_id);

CREATE TABLE IF NOT EXISTS nutrition_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_at TIMESTAMPTZ NOT NULL,
    meal_type VARCHAR(30),
    food_item_id UUID REFERENCES food_items(id),
    photo_id UUID REFERENCES nutrition_photos(id),
    quantity_g FLOAT,
    calories FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    fiber_g FLOAT,
    micronutrients JSONB,
    data_quality VARCHAR(20),
    hunger_before INTEGER,
    satiety_after INTEGER,
    energy_after INTEGER,
    notes TEXT,
    fasting_window_broken BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_nutrition_entries_user_date ON nutrition_entries(user_id, logged_at);

CREATE TABLE IF NOT EXISTS supplement_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    supplement_name VARCHAR(100) NOT NULL,
    goal TEXT,
    reason TEXT,
    observed_data_basis TEXT,
    confidence_level FLOAT,
    evidence_type VARCHAR(30),
    suggested_dose VARCHAR(100),
    suggested_timing VARCHAR(100),
    trial_duration_weeks INTEGER,
    precautions TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_supplement_rec_user_id ON supplement_recommendations(user_id);

CREATE TABLE IF NOT EXISTS metabolic_state_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    estimated_bmr_kcal FLOAT,
    estimated_tdee_kcal FLOAT,
    estimated_glycogen_g FLOAT,
    glycogen_status VARCHAR(20),
    fatigue_score FLOAT,
    recovery_score FLOAT,
    readiness_score FLOAT,
    training_load_7d FLOAT,
    training_load_28d FLOAT,
    energy_availability_kcal FLOAT,
    estimated_glucose_mg_dl FLOAT,
    estimated_cortisol_level FLOAT,
    estimated_neural_fatigue FLOAT,
    injury_risk_score FLOAT,
    hormonal_balance_signal VARCHAR(20),
    confidence_score FLOAT,
    variables_used TEXT[],
    sleep_quality_input FLOAT,
    hrv_input FLOAT,
    resting_hr_input FLOAT,
    training_load_input FLOAT,
    nutrition_input FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_metabolic_user_date UNIQUE (user_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS ix_metabolic_snapshots_user_date ON metabolic_state_snapshots(user_id, snapshot_date);

CREATE TABLE IF NOT EXISTS readiness_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    sleep_score FLOAT,
    recovery_score FLOAT,
    training_load_score FLOAT,
    hrv_score FLOAT,
    nutrition_score FLOAT,
    hydration_score FLOAT,
    overall_readiness FLOAT,
    recommended_intensity VARCHAR(20),
    reasoning TEXT,
    variables_used JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_readiness_user_date UNIQUE (user_id, score_date)
);
CREATE INDEX IF NOT EXISTS ix_readiness_scores_user_date ON readiness_scores(user_id, score_date);

CREATE TABLE IF NOT EXISTS longevity_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score_date DATE NOT NULL,
    cardio_score FLOAT,
    strength_score FLOAT,
    sleep_score FLOAT,
    nutrition_score FLOAT,
    weight_score FLOAT,
    body_comp_score FLOAT,
    consistency_score FLOAT,
    longevity_score FLOAT,
    biological_age_estimate FLOAT,
    trend_30d FLOAT,
    trend_90d FLOAT,
    top_improvement_levers JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_longevity_user_date UNIQUE (user_id, score_date)
);
CREATE INDEX IF NOT EXISTS ix_longevity_scores_user_date ON longevity_scores(user_id, score_date);

CREATE TABLE IF NOT EXISTS daily_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation_date DATE NOT NULL,
    morning_briefing TEXT,
    daily_plan JSONB,
    workout_recommendation JSONB,
    nutrition_strategy JSONB,
    hydration_target_ml INTEGER,
    alerts JSONB,
    evening_summary TEXT,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    model_used VARCHAR(100),
    reasoning JSONB,
    CONSTRAINT uq_daily_rec_user_date UNIQUE (user_id, recommendation_date)
);
CREATE INDEX IF NOT EXISTS ix_daily_recommendations_user_date ON daily_recommendations(user_id, recommendation_date);


-- =============================================================================
-- V002 -- Nutrition and scores add-ons
-- =============================================================================

ALTER TABLE nutrition_entries ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE nutrition_entries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE nutrition_entries ADD COLUMN IF NOT EXISTS meal_name VARCHAR(200);

CREATE INDEX IF NOT EXISTS ix_nutrition_entries_user_date_active
    ON nutrition_entries(user_id, logged_at)
    WHERE is_deleted = FALSE;

ALTER TABLE nutrition_photos ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE nutrition_photos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE nutrition_photos ADD COLUMN IF NOT EXISTS entry_id UUID;
ALTER TABLE nutrition_photos ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER;
ALTER TABLE nutrition_photos ADD COLUMN IF NOT EXISTS mime_type VARCHAR(50);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_nutrition_photos_entry_id' AND table_name = 'nutrition_photos') THEN
        ALTER TABLE nutrition_photos ADD CONSTRAINT fk_nutrition_photos_entry_id FOREIGN KEY (entry_id) REFERENCES nutrition_entries(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_nutrition_photos_entry_id
    ON nutrition_photos(entry_id)
    WHERE is_deleted = FALSE;

ALTER TABLE readiness_scores ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS ix_food_items_name_trgm
    ON food_items USING gin(name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS ix_food_items_name_fr_trgm
    ON food_items USING gin(name_fr gin_trgm_ops)
    WHERE name_fr IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_food_items_source ON food_items(source);


-- =============================================================================
-- V003 -- Daily metrics and insights
-- =============================================================================

CREATE TABLE IF NOT EXISTS daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    metrics_date DATE NOT NULL,
    weight_kg FLOAT,
    calories_consumed FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT,
    fiber_g FLOAT,
    calories_target FLOAT,
    protein_target_g FLOAT,
    meal_count INTEGER,
    hydration_ml INTEGER,
    hydration_target_ml INTEGER,
    steps INTEGER,
    active_calories_kcal FLOAT,
    distance_km FLOAT,
    resting_heart_rate_bpm FLOAT,
    hrv_ms FLOAT,
    sleep_minutes INTEGER,
    sleep_score FLOAT,
    sleep_quality_label VARCHAR(20),
    workout_count INTEGER NOT NULL DEFAULT 0,
    total_tonnage_kg FLOAT,
    training_load FLOAT,
    readiness_score FLOAT,
    longevity_score FLOAT,
    data_completeness_pct FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_daily_metrics_user_date UNIQUE (user_id, metrics_date),
    CONSTRAINT fk_daily_metrics_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_daily_metrics_user_id ON daily_metrics(user_id);
CREATE INDEX IF NOT EXISTS ix_daily_metrics_date ON daily_metrics(metrics_date);
CREATE INDEX IF NOT EXISTS ix_daily_metrics_user_date ON daily_metrics(user_id, metrics_date);

CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    insight_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    action VARCHAR(500),
    data_evidence JSONB,
    is_read BOOLEAN NOT NULL DEFAULT false,
    is_dismissed BOOLEAN NOT NULL DEFAULT false,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_insight_user_date_category_title UNIQUE (user_id, insight_date, category, title),
    CONSTRAINT fk_insights_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_insights_user_id ON insights(user_id);
CREATE INDEX IF NOT EXISTS ix_insights_date ON insights(insight_date);
CREATE INDEX IF NOT EXISTS ix_insights_category ON insights(category);
CREATE INDEX IF NOT EXISTS ix_insights_severity ON insights(severity);
CREATE INDEX IF NOT EXISTS ix_insights_active ON insights(user_id, insight_date)
    WHERE is_dismissed = FALSE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'readiness_scores' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE readiness_scores
        ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
    END IF;
END$$;


-- =============================================================================
-- V004 -- Algorithm version tracking
-- =============================================================================

ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0';
ALTER TABLE readiness_scores ADD COLUMN IF NOT EXISTS algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0';
ALTER TABLE longevity_scores ADD COLUMN IF NOT EXISTS algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0';


-- =============================================================================
-- V005 -- Vision sessions
-- =============================================================================

CREATE TABLE IF NOT EXISTS vision_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_type VARCHAR(50) NOT NULL,
    rep_count INTEGER NOT NULL DEFAULT 0,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    amplitude_score FLOAT,
    stability_score FLOAT,
    regularity_score FLOAT,
    quality_score FLOAT,
    workout_session_id UUID REFERENCES workout_sessions(id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0',
    session_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_vision_sessions_user_date ON vision_sessions(user_id, session_date);
CREATE INDEX IF NOT EXISTS ix_vision_sessions_workout_session ON vision_sessions(workout_session_id);


-- =============================================================================
-- V006 -- Coach IA models
-- =============================================================================

CREATE TABLE IF NOT EXISTS conversation_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_conversation_threads_user_id ON conversation_threads(user_id);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES conversation_threads(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_conversation_messages_thread_id ON conversation_messages(thread_id);

ALTER TABLE metabolic_state_snapshots ADD COLUMN IF NOT EXISTS protein_status VARCHAR(20);
ALTER TABLE metabolic_state_snapshots ADD COLUMN IF NOT EXISTS hydration_status VARCHAR(20);
ALTER TABLE metabolic_state_snapshots ADD COLUMN IF NOT EXISTS stress_load FLOAT;
ALTER TABLE metabolic_state_snapshots ADD COLUMN IF NOT EXISTS plateau_risk BOOLEAN;
ALTER TABLE metabolic_state_snapshots ADD COLUMN IF NOT EXISTS metabolic_age FLOAT;


-- =============================================================================
-- V007 -- Advanced health engines
-- =============================================================================

CREATE TABLE IF NOT EXISTS digital_twin_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    snapshot_date DATE NOT NULL,
    components JSONB,
    overall_status VARCHAR(20),
    primary_concern TEXT,
    global_confidence FLOAT,
    plateau_risk BOOLEAN,
    under_recovery_risk BOOLEAN,
    recommendations JSONB,
    algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_digital_twin_user_date UNIQUE (user_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS ix_digital_twin_user_id ON digital_twin_snapshots(user_id);
CREATE INDEX IF NOT EXISTS ix_digital_twin_user_date ON digital_twin_snapshots(user_id, snapshot_date);

CREATE TABLE IF NOT EXISTS biological_age_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    snapshot_date DATE NOT NULL,
    chronological_age INTEGER,
    biological_age FLOAT,
    biological_age_delta FLOAT,
    longevity_risk_score FLOAT,
    components JSONB,
    levers JSONB,
    trend_direction VARCHAR(20),
    confidence FLOAT,
    explanation TEXT,
    algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_bio_age_user_date UNIQUE (user_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS ix_bio_age_user_id ON biological_age_snapshots(user_id);
CREATE INDEX IF NOT EXISTS ix_bio_age_user_date ON biological_age_snapshots(user_id, snapshot_date);

CREATE TABLE IF NOT EXISTS motion_intelligence_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    snapshot_date DATE NOT NULL,
    movement_health_score FLOAT,
    stability_score FLOAT,
    mobility_score FLOAT,
    asymmetry_score FLOAT,
    overall_quality_trend VARCHAR(20),
    consecutive_quality_sessions INTEGER,
    sessions_analyzed INTEGER,
    days_analyzed INTEGER,
    exercise_profiles JSONB,
    recommendations JSONB,
    risk_alerts JSONB,
    confidence FLOAT,
    algorithm_version VARCHAR(10) NOT NULL DEFAULT 'v1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_motion_user_date UNIQUE (user_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS ix_motion_user_id ON motion_intelligence_snapshots(user_id);
CREATE INDEX IF NOT EXISTS ix_motion_user_date ON motion_intelligence_snapshots(user_id, snapshot_date);

CREATE INDEX IF NOT EXISTS ix_conversation_messages_thread_created
    ON conversation_messages(thread_id, created_at);

-- =============================================================================
-- V008 -- Coach platform and biomarkers
-- =============================================================================

CREATE TABLE IF NOT EXISTS coach_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(150) NOT NULL,
    specializations JSONB,
    certification VARCHAR(200),
    bio TEXT,
    max_athletes INTEGER NOT NULL DEFAULT 50,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_coach_profiles_user_id UNIQUE (user_id)
);
CREATE INDEX IF NOT EXISTS ix_coach_profiles_user_id ON coach_profiles(user_id);

CREATE TABLE IF NOT EXISTS athlete_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    sport VARCHAR(100),
    goal VARCHAR(200),
    date_of_birth DATE,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_athlete_profiles_user_id UNIQUE (user_id)
);
CREATE INDEX IF NOT EXISTS ix_athlete_profiles_user_id ON athlete_profiles(user_id);

CREATE TABLE IF NOT EXISTS coach_athlete_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL,
    athlete_id UUID NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    role VARCHAR(50) NOT NULL DEFAULT 'primary',
    linked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_coach_athlete_link UNIQUE (coach_id, athlete_id)
);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_links_coach_id ON coach_athlete_links(coach_id);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_links_athlete_id ON coach_athlete_links(athlete_id);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_links_coach_athlete ON coach_athlete_links(coach_id, athlete_id);

CREATE TABLE IF NOT EXISTS training_programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL,
    athlete_id UUID,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    duration_weeks INTEGER NOT NULL DEFAULT 4,
    sport_focus VARCHAR(100),
    difficulty VARCHAR(50),
    weeks JSONB,
    is_template BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_training_programs_coach_id ON training_programs(coach_id);
CREATE INDEX IF NOT EXISTS ix_training_programs_athlete_id ON training_programs(athlete_id);

CREATE TABLE IF NOT EXISTS athlete_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL,
    athlete_id UUID NOT NULL,
    note_date DATE NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    is_private BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_athlete_notes_coach_athlete ON athlete_notes(coach_id, athlete_id);

CREATE TABLE IF NOT EXISTS athlete_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL,
    athlete_id UUID NOT NULL,
    alert_type VARCHAR(80) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metric_value FLOAT,
    threshold_value FLOAT,
    is_acknowledged BOOLEAN NOT NULL DEFAULT false,
    acknowledged_at TIMESTAMPTZ,
    generated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_athlete_alerts_coach_athlete ON athlete_alerts(coach_id, athlete_id);
CREATE INDEX IF NOT EXISTS ix_athlete_alerts_coach_unack ON athlete_alerts(coach_id, is_acknowledged);

CREATE TABLE IF NOT EXISTS lab_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    marker_name VARCHAR(100) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    test_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_lab_results_user_id ON lab_results(user_id);
CREATE INDEX IF NOT EXISTS ix_lab_results_user_date ON lab_results(user_id, test_date);

-- =============================================================================
-- V009 -- Analytics events
-- =============================================================================

CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    properties JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS ix_analytics_events_event_name ON analytics_events(event_name);
CREATE INDEX IF NOT EXISTS ix_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX IF NOT EXISTS ix_analytics_events_user_created ON analytics_events(user_id, created_at);


-- =============================================================================
-- V010 -- API metrics
-- =============================================================================

CREATE TABLE IF NOT EXISTS api_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_api_metrics_endpoint ON api_metrics(endpoint);
CREATE INDEX IF NOT EXISTS ix_api_metrics_status_code ON api_metrics(status_code);
CREATE INDEX IF NOT EXISTS ix_api_metrics_created_at ON api_metrics(created_at);
CREATE INDEX IF NOT EXISTS ix_api_metrics_endpoint_time ON api_metrics(endpoint, created_at);


-- =============================================================================
-- V011 -- User preferences
-- =============================================================================

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS theme_preference VARCHAR(10) NOT NULL DEFAULT 'system';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS locale VARCHAR(10) NOT NULL DEFAULT 'fr';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Paris';


-- =============================================================================
-- V012 -- Body composition enriched fields
-- =============================================================================

ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS bone_mass_kg FLOAT;
ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS visceral_fat_index FLOAT;
ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS water_pct FLOAT;
ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS metabolic_age INTEGER;
ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS trunk_fat_pct FLOAT;
ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS trunk_muscle_pct FLOAT;


-- =============================================================================
-- V013 -- HRV, cycle tracking, gamification
-- =============================================================================

CREATE TABLE IF NOT EXISTS menstrual_cycle_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cycle_start_date DATE NOT NULL,
    cycle_length_days INTEGER,
    period_duration_days INTEGER,
    notes TEXT,
    symptoms TEXT,
    flow_intensity VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cycle_user_start ON menstrual_cycle_entries(user_id, cycle_start_date);

-- =============================================================================
-- V014 -- Subscription plans
-- =============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_code VARCHAR(20) NOT NULL DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_status VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_provider VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_started_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_users_plan_code ON users(plan_code);
CREATE INDEX IF NOT EXISTS ix_users_stripe_customer ON users(stripe_customer_id);

CREATE TABLE IF NOT EXISTS plans (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rank INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS plan_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_code VARCHAR(20) NOT NULL REFERENCES plans(code) ON DELETE CASCADE,
    feature_code VARCHAR(100) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_plan_features_plan ON plan_features(plan_code);

CREATE TABLE IF NOT EXISTS feature_entitlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_code VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    source VARCHAR(30) NOT NULL DEFAULT 'plan',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_entitlements_user ON feature_entitlements(user_id);

INSERT INTO plans (code, name, rank) VALUES ('free', 'SOMA Free', 1) ON CONFLICT DO NOTHING;
INSERT INTO plans (code, name, rank) VALUES ('ai', 'SOMA AI', 2) ON CONFLICT DO NOTHING;
INSERT INTO plans (code, name, rank) VALUES ('performance', 'SOMA Performance', 3) ON CONFLICT DO NOTHING;

INSERT INTO plan_features (plan_code, feature_code) VALUES ('free', 'basic_dashboard') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('free', 'basic_health_metrics') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('free', 'local_ai_tips') ON CONFLICT DO NOTHING;

INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'basic_dashboard') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'basic_health_metrics') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'local_ai_tips') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'ai_coach') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'daily_briefing') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'advanced_insights') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'pdf_reports') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'anomaly_detection') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('ai', 'biological_age') ON CONFLICT DO NOTHING;

INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'basic_dashboard') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'basic_health_metrics') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'local_ai_tips') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'ai_coach') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'daily_briefing') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'advanced_insights') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'pdf_reports') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'anomaly_detection') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'biological_age') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'readiness_score') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'injury_prediction') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'biomechanics_vision') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'advanced_vo2max') ON CONFLICT DO NOTHING;
INSERT INTO plan_features (plan_code, feature_code) VALUES ('performance', 'training_load') ON CONFLICT DO NOTHING;


-- =============================================================================
-- V015 -- Webhook idempotency, feature usage events, admin settings
-- =============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    event_id VARCHAR(255) PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feature_usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    feature_code VARCHAR(100),
    plan_code VARCHAR(20),
    metadata TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_feature_usage_user ON feature_usage_events(user_id);
CREATE INDEX IF NOT EXISTS ix_feature_usage_type ON feature_usage_events(event_type);
CREATE INDEX IF NOT EXISTS ix_feature_usage_occurred ON feature_usage_events(occurred_at);

CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    description TEXT,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(100)
);

INSERT INTO app_settings (key, value, description, category) VALUES ('free_plan_daily_ai_limit', '10', 'Max AI requests per day for free plan', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('free_plan_max_prompt_chars', '1200', 'Max prompt length in chars for free plan', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('free_plan_ai_timeout_seconds', '15', 'Timeout in seconds for free plan AI calls', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('ai_plan_daily_ai_limit', '100', 'Max AI requests per day for AI plan', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('performance_plan_daily_ai_limit', '500', 'Max AI requests per day for performance plan', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('stripe_price_ai_monthly', '', 'Stripe Price ID for AI plan monthly', 'billing') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('stripe_price_ai_yearly', '', 'Stripe Price ID for AI plan yearly', 'billing') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('stripe_price_perf_monthly', '', 'Stripe Price ID for Performance plan monthly', 'billing') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('stripe_price_perf_yearly', '', 'Stripe Price ID for Performance plan yearly', 'billing') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('trial_ai_days', '7', 'Trial duration in days for AI plan', 'billing') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('trial_performance_days', '3', 'Trial duration in days for Performance plan', 'billing') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('ollama_model', 'llama3.2:3b', 'Ollama model for free plan local AI', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('claude_standard_model', 'claude-3-5-haiku-20241022', 'Claude model for AI plan', 'ai') ON CONFLICT DO NOTHING;
INSERT INTO app_settings (key, value, description, category) VALUES ('claude_advanced_model', 'claude-3-5-sonnet-20241022', 'Claude model for Performance plan', 'ai') ON CONFLICT DO NOTHING;

