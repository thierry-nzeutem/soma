"""V001 initial schema — SOMA all tables

Revision ID: V001
Revises: None
Create Date: 2026-03-07

Tables créées (ordre respectant les FK) :
  users, user_profiles, body_metrics,
  health_data_sources, health_import_jobs, health_samples,
  sleep_sessions, hydration_logs,
  exercise_library, workout_sessions, workout_exercises, workout_sets,
  food_items, nutrition_photos, nutrition_entries, supplement_recommendations,
  metabolic_state_snapshots, readiness_scores, longevity_scores,
  daily_recommendations
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "V001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions PostgreSQL ──────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    # ── user_profiles ──────────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(10), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("goal_weight_kg", sa.Float(), nullable=True),
        sa.Column("primary_goal", sa.String(50), nullable=True),
        sa.Column("physical_constraints", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("activity_level", sa.String(20), nullable=True),
        sa.Column("fitness_level", sa.String(20), nullable=True),
        sa.Column("dietary_regime", sa.String(50), nullable=True),
        sa.Column("food_allergies", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("food_intolerances", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("intermittent_fasting", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("fasting_protocol", sa.String(50), nullable=True),
        sa.Column("meals_per_day", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("preferred_training_time", sa.String(20), nullable=True),
        sa.Column("usual_wake_time", sa.Time(), nullable=True),
        sa.Column("usual_sleep_time", sa.Time(), nullable=True),
        sa.Column("avg_energy_level", sa.Integer(), nullable=True),
        sa.Column("perceived_sleep_quality", sa.Integer(), nullable=True),
        sa.Column("home_equipment", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("gym_access", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("gym_equipment", postgresql.ARRAY(sa.Text()), nullable=True),
        # Champs calculés dénormalisés
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("bmr_kcal", sa.Float(), nullable=True),
        sa.Column("tdee_kcal", sa.Float(), nullable=True),
        sa.Column("target_calories_kcal", sa.Float(), nullable=True),
        sa.Column("target_protein_g", sa.Float(), nullable=True),
        sa.Column("target_hydration_ml", sa.Float(), nullable=True),
        sa.Column("profile_completeness_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])

    # ── body_metrics ───────────────────────────────────────────────────────────
    op.create_table(
        "body_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("body_fat_pct", sa.Float(), nullable=True),
        sa.Column("muscle_mass_kg", sa.Float(), nullable=True),
        sa.Column("waist_cm", sa.Float(), nullable=True),
        sa.Column("hip_cm", sa.Float(), nullable=True),
        sa.Column("neck_cm", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("data_quality", sa.String(20), nullable=False, server_default="exact"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_body_metrics_user_date", "body_metrics", ["user_id", "measured_at"])

    # ── health_data_sources ────────────────────────────────────────────────────
    op.create_table(
        "health_data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_name", sa.String(100), nullable=True),
        sa.Column("is_connected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("permissions_granted", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_health_data_sources_user_id", "health_data_sources", ["user_id"])

    # ── health_import_jobs ─────────────────────────────────────────────────────
    op.create_table(
        "health_import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("health_data_sources.id"), nullable=True),
        sa.Column("job_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_imported", sa.Integer(), nullable=True),
        sa.Column("records_skipped", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── health_samples ─────────────────────────────────────────────────────────
    op.create_table(
        "health_samples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sample_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("data_quality", sa.String(20), nullable=False, server_default="exact"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "sample_type", "recorded_at", "source", name="uq_health_samples_dedup"),
    )
    op.create_index("ix_health_samples_user_type_date", "health_samples", ["user_id", "sample_type", "recorded_at"])

    # ── sleep_sessions ─────────────────────────────────────────────────────────
    op.create_table(
        "sleep_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("deep_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("rem_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("light_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("awake_minutes", sa.Integer(), nullable=True),
        sa.Column("avg_heart_rate_bpm", sa.Float(), nullable=True),
        sa.Column("avg_hrv_ms", sa.Float(), nullable=True),
        sa.Column("sleep_score", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("data_quality", sa.String(20), nullable=False, server_default="exact"),
        sa.Column("perceived_quality", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sleep_sessions_user_date", "sleep_sessions", ["user_id", "start_at"])

    # ── hydration_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "hydration_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("volume_ml", sa.Integer(), nullable=False),
        sa.Column("beverage_type", sa.String(50), nullable=False, server_default="water"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_hydration_logs_user_date", "hydration_logs", ["user_id", "logged_at"])

    # ── exercise_library ───────────────────────────────────────────────────────
    op.create_table(
        "exercise_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_fr", sa.String(200), nullable=True),
        sa.Column("slug", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("subcategory", sa.String(50), nullable=True),
        sa.Column("primary_muscles", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("secondary_muscles", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("difficulty_level", sa.String(20), nullable=True),
        sa.Column("equipment_required", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("execution_location", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("breathing_cues", sa.Text(), nullable=True),
        sa.Column("common_errors", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("image_urls", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("easier_variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercise_library.id"), nullable=True),
        sa.Column("harder_variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercise_library.id"), nullable=True),
        sa.Column("key_joint_angles", postgresql.JSONB(), nullable=True),
        sa.Column("cv_supported", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rep_detection_model", sa.String(50), nullable=True),
        sa.Column("contraindications", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("met_value", sa.Float(), nullable=True),
        sa.Column("format_type", sa.String(20), nullable=True),  # reps | duration | distance
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_exercise_library_slug"),
    )
    op.create_index("ix_exercise_library_name", "exercise_library", ["name"])
    op.create_index("ix_exercise_library_category", "exercise_library", ["category"])

    # ── workout_sessions ───────────────────────────────────────────────────────
    op.create_table(
        "workout_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("session_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        # planned | in_progress | completed | skipped | cancelled
        sa.Column("location", sa.String(50), nullable=True),
        sa.Column("total_tonnage_kg", sa.Float(), nullable=True),
        sa.Column("total_sets", sa.Integer(), nullable=True),
        sa.Column("total_reps", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("avg_heart_rate_bpm", sa.Float(), nullable=True),
        sa.Column("max_heart_rate_bpm", sa.Float(), nullable=True),
        sa.Column("calories_burned_kcal", sa.Float(), nullable=True),
        sa.Column("internal_load_score", sa.Float(), nullable=True),
        sa.Column("rpe_score", sa.Float(), nullable=True),
        sa.Column("energy_before", sa.Integer(), nullable=True),
        sa.Column("energy_after", sa.Integer(), nullable=True),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("technical_score", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workout_sessions_user_date", "workout_sessions", ["user_id", "started_at"])
    op.create_index("ix_workout_sessions_status", "workout_sessions", ["user_id", "status"])

    # ── workout_exercises ──────────────────────────────────────────────────────
    op.create_table(
        "workout_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercise_library.id"), nullable=True),
        sa.Column("exercise_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("biomechanics_score", sa.Float(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workout_exercises_session_id", "workout_exercises", ["session_id"])

    # ── workout_sets ───────────────────────────────────────────────────────────
    op.create_table(
        "workout_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workout_exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps_target", sa.Integer(), nullable=True),
        sa.Column("reps_actual", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("tempo", sa.String(20), nullable=True),
        sa.Column("time_under_tension_s", sa.Float(), nullable=True),
        sa.Column("range_of_motion_pct", sa.Float(), nullable=True),
        sa.Column("rpe_set", sa.Float(), nullable=True),
        sa.Column("is_warmup", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_pr", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workout_sets_exercise_id", "workout_sets", ["workout_exercise_id"])

    # ── food_items ─────────────────────────────────────────────────────────────
    op.create_table(
        "food_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_fr", sa.String(200), nullable=True),
        sa.Column("barcode", sa.String(50), nullable=True),
        sa.Column("calories_per_100g", sa.Float(), nullable=True),
        sa.Column("protein_g_per_100g", sa.Float(), nullable=True),
        sa.Column("carbs_g_per_100g", sa.Float(), nullable=True),
        sa.Column("fat_g_per_100g", sa.Float(), nullable=True),
        sa.Column("fiber_g_per_100g", sa.Float(), nullable=True),
        sa.Column("sugar_g_per_100g", sa.Float(), nullable=True),
        sa.Column("micronutrients", postgresql.JSONB(), nullable=True),
        sa.Column("food_group", sa.String(50), nullable=True),
        sa.Column("is_ultra_processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("nova_score", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_food_items_name", "food_items", ["name"])
    op.create_index("ix_food_items_barcode", "food_items", ["barcode"])

    # ── nutrition_photos ───────────────────────────────────────────────────────
    op.create_table(
        "nutrition_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_path", sa.String(500), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ai_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("identified_foods", postgresql.JSONB(), nullable=True),
        sa.Column("estimated_calories", sa.Float(), nullable=True),
        sa.Column("estimated_protein_g", sa.Float(), nullable=True),
        sa.Column("estimated_carbs_g", sa.Float(), nullable=True),
        sa.Column("estimated_fat_g", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("user_validated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("user_corrections", postgresql.JSONB(), nullable=True),
        sa.Column("analysis_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_nutrition_photos_user_id", "nutrition_photos", ["user_id"])

    # ── nutrition_entries ──────────────────────────────────────────────────────
    op.create_table(
        "nutrition_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meal_type", sa.String(30), nullable=True),
        sa.Column("food_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("food_items.id"), nullable=True),
        sa.Column("photo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("nutrition_photos.id"), nullable=True),
        sa.Column("quantity_g", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("micronutrients", postgresql.JSONB(), nullable=True),
        sa.Column("data_quality", sa.String(20), nullable=True),
        sa.Column("hunger_before", sa.Integer(), nullable=True),
        sa.Column("satiety_after", sa.Integer(), nullable=True),
        sa.Column("energy_after", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("fasting_window_broken", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_nutrition_entries_user_date", "nutrition_entries", ["user_id", "logged_at"])

    # ── supplement_recommendations ─────────────────────────────────────────────
    op.create_table(
        "supplement_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("supplement_name", sa.String(100), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("observed_data_basis", sa.Text(), nullable=True),
        sa.Column("confidence_level", sa.Float(), nullable=True),
        sa.Column("evidence_type", sa.String(30), nullable=True),
        sa.Column("suggested_dose", sa.String(100), nullable=True),
        sa.Column("suggested_timing", sa.String(100), nullable=True),
        sa.Column("trial_duration_weeks", sa.Integer(), nullable=True),
        sa.Column("precautions", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_supplement_rec_user_id", "supplement_recommendations", ["user_id"])

    # ── metabolic_state_snapshots ──────────────────────────────────────────────
    op.create_table(
        "metabolic_state_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("estimated_bmr_kcal", sa.Float(), nullable=True),
        sa.Column("estimated_tdee_kcal", sa.Float(), nullable=True),
        sa.Column("estimated_glycogen_g", sa.Float(), nullable=True),
        sa.Column("glycogen_status", sa.String(20), nullable=True),
        sa.Column("fatigue_score", sa.Float(), nullable=True),
        sa.Column("recovery_score", sa.Float(), nullable=True),
        sa.Column("readiness_score", sa.Float(), nullable=True),
        sa.Column("training_load_7d", sa.Float(), nullable=True),
        sa.Column("training_load_28d", sa.Float(), nullable=True),
        sa.Column("energy_availability_kcal", sa.Float(), nullable=True),
        sa.Column("estimated_glucose_mg_dl", sa.Float(), nullable=True),
        sa.Column("estimated_cortisol_level", sa.Float(), nullable=True),
        sa.Column("estimated_neural_fatigue", sa.Float(), nullable=True),
        sa.Column("injury_risk_score", sa.Float(), nullable=True),
        sa.Column("hormonal_balance_signal", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("variables_used", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("sleep_quality_input", sa.Float(), nullable=True),
        sa.Column("hrv_input", sa.Float(), nullable=True),
        sa.Column("resting_hr_input", sa.Float(), nullable=True),
        sa.Column("training_load_input", sa.Float(), nullable=True),
        sa.Column("nutrition_input", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "snapshot_date", name="uq_metabolic_user_date"),
    )
    op.create_index("ix_metabolic_snapshots_user_date", "metabolic_state_snapshots", ["user_id", "snapshot_date"])

    # ── readiness_scores ───────────────────────────────────────────────────────
    op.create_table(
        "readiness_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score_date", sa.Date(), nullable=False),
        sa.Column("sleep_score", sa.Float(), nullable=True),
        sa.Column("recovery_score", sa.Float(), nullable=True),
        sa.Column("training_load_score", sa.Float(), nullable=True),
        sa.Column("hrv_score", sa.Float(), nullable=True),
        sa.Column("nutrition_score", sa.Float(), nullable=True),
        sa.Column("hydration_score", sa.Float(), nullable=True),
        sa.Column("overall_readiness", sa.Float(), nullable=True),
        sa.Column("recommended_intensity", sa.String(20), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("variables_used", postgresql.JSONB(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "score_date", name="uq_readiness_user_date"),
    )
    op.create_index("ix_readiness_scores_user_date", "readiness_scores", ["user_id", "score_date"])

    # ── longevity_scores ───────────────────────────────────────────────────────
    op.create_table(
        "longevity_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score_date", sa.Date(), nullable=False),
        sa.Column("cardio_score", sa.Float(), nullable=True),
        sa.Column("strength_score", sa.Float(), nullable=True),
        sa.Column("sleep_score", sa.Float(), nullable=True),
        sa.Column("nutrition_score", sa.Float(), nullable=True),
        sa.Column("weight_score", sa.Float(), nullable=True),
        sa.Column("body_comp_score", sa.Float(), nullable=True),
        sa.Column("consistency_score", sa.Float(), nullable=True),
        sa.Column("longevity_score", sa.Float(), nullable=True),
        sa.Column("biological_age_estimate", sa.Float(), nullable=True),
        sa.Column("trend_30d", sa.Float(), nullable=True),
        sa.Column("trend_90d", sa.Float(), nullable=True),
        sa.Column("top_improvement_levers", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "score_date", name="uq_longevity_user_date"),
    )
    op.create_index("ix_longevity_scores_user_date", "longevity_scores", ["user_id", "score_date"])

    # ── daily_recommendations ──────────────────────────────────────────────────
    op.create_table(
        "daily_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_date", sa.Date(), nullable=False),
        sa.Column("morning_briefing", sa.Text(), nullable=True),
        sa.Column("daily_plan", postgresql.JSONB(), nullable=True),
        sa.Column("workout_recommendation", postgresql.JSONB(), nullable=True),
        sa.Column("nutrition_strategy", postgresql.JSONB(), nullable=True),
        sa.Column("hydration_target_ml", sa.Integer(), nullable=True),
        sa.Column("alerts", postgresql.JSONB(), nullable=True),
        sa.Column("evening_summary", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("reasoning", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("user_id", "recommendation_date", name="uq_daily_rec_user_date"),
    )
    op.create_index("ix_daily_recommendations_user_date", "daily_recommendations", ["user_id", "recommendation_date"])


def downgrade() -> None:
    # Suppression dans l'ordre inverse des FK
    op.drop_table("daily_recommendations")
    op.drop_table("longevity_scores")
    op.drop_table("readiness_scores")
    op.drop_table("metabolic_state_snapshots")
    op.drop_table("supplement_recommendations")
    op.drop_table("nutrition_entries")
    op.drop_table("nutrition_photos")
    op.drop_table("food_items")
    op.drop_table("workout_sets")
    op.drop_table("workout_exercises")
    op.drop_table("workout_sessions")
    op.drop_table("exercise_library")
    op.drop_table("hydration_logs")
    op.drop_table("sleep_sessions")
    op.drop_table("health_samples")
    op.drop_table("health_import_jobs")
    op.drop_table("health_data_sources")
    op.drop_table("body_metrics")
    op.drop_table("user_profiles")
    op.drop_table("users")
