// ─── SOMA Desktop — TypeScript API Types (v2) ────────────────────────────────
// Aligned with FastAPI Pydantic schemas (backend LOT 0→19)
// Optional fields handle API variations and partial responses gracefully

// ── Auth ─────────────────────────────────────────────────────────────────────
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface RefreshRequest {
  refresh_token: string;
}

// ── Shared ────────────────────────────────────────────────────────────────────
export interface WorkoutRecommendation {
  workout_type?: string;
  type?: string;
  intensity?: string;
  duration_minutes?: number;
  focus_areas?: string[];
  rest_between_sets_sec?: number;
  rationale?: string;
}

export interface NutritionTargets {
  calories_target?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  water_ml?: number;
  hydration_target_ml?: number;
}

export interface PlanAlert {
  type?: 'info' | 'warning' | 'critical';
  severity?: 'info' | 'warning' | 'critical' | 'high' | 'medium' | 'low';
  message?: string;
  title?: string;
  description?: string;
  details?: string;
}

export interface InsightSummary {
  id?: string;
  category?: string;
  severity?: 'info' | 'warning' | 'critical';
  message?: string;
  title?: string;
  description?: string;
  details?: string;
}

// ── Home Summary (/home/summary) ──────────────────────────────────────────────
export interface DailyMetricsSummary {
  metrics_date: string;
  weight_kg: number | null;
  calories_consumed: number;
  calories_target: number;
  protein_g: number;
  protein_target_g: number;
  hydration_ml: number;
  hydration_target_ml: number;
  steps: number;
  sleep_minutes: number;
  sleep_quality_label: string | null;
  hrv_ms: number | null;
  workout_count: number;
  readiness_score: number | null;
  data_completeness_pct: number;
}

export interface ReadinessSummary {
  overall_readiness: number;
  recommended_intensity: string;
  readiness_level: string;
}

export interface LongevitySummary {
  longevity_score: number | null;
  biological_age_estimate: number | null;
}

export interface HomeSummaryResponse {
  summary_date: string;
  generated_at: string;
  metrics: DailyMetricsSummary | null;
  readiness: ReadinessSummary | null;
  unread_insights: InsightSummary[];
  unread_insights_count: number;
  plan: {
    readiness_level: string;
    recommended_intensity: string;
    protein_target_g: number;
    calorie_target: number;
    steps_goal: number;
    workout_recommendation: WorkoutRecommendation | null;
    daily_tips: string[];
    alerts: PlanAlert[];
    from_cache: boolean;
  } | null;
  longevity: LongevitySummary | null;
  has_active_plan: boolean;
  // Convenience flat fields
  readiness_score?: number | null;
  longevity_score?: number | null;
  current_weight_kg?: number | null;
  bmi?: number | null;
  alerts?: PlanAlert[];
  recent_insights?: InsightSummary[];
  twin_signals?: Record<string, unknown>;
}

// ── Daily Briefing (/daily/briefing) ─────────────────────────────────────────
export interface DailyBriefingResponse {
  briefing_date: string;
  generated_at: string;
  readiness_score: number | null;
  readiness_level?: string | null;
  readiness_color?: string;
  recommended_intensity?: string;
  sleep_duration_h?: number | null;
  sleep_duration_hours?: number | null;
  sleep_quality_label?: string | null;
  sleep_quality_score?: number | null;
  fatigue_percentage?: number | null;
  available_energy_kcal?: number | null;
  calorie_target?: number;
  protein_target_g?: number;
  carb_target_g?: number;
  fat_target_g?: number;
  hydration_target_ml?: number;
  training_type?: string | null;
  training_intensity?: string | null;
  training_duration_min?: number | null;
  active_alerts?: PlanAlert[];
  alerts?: string[];
  insights?: (string | InsightSummary)[];
  top_insight?: string | null;
  coach_tip?: string | null;
  twin_status?: string | null;
  twin_primary_concern?: string | null;
}

// ── Health Plan (/health/plan/today) ─────────────────────────────────────────
export interface DailyHealthPlanResponse {
  date: string;
  generated_at: string;
  from_cache: boolean;
  workout_recommendation: WorkoutRecommendation | null;
  nutrition_targets?: NutritionTargets | null;
  protein_target_g?: number;
  calorie_target?: number;
  hydration_target_ml?: number;
  steps_goal?: number;
  sleep_target_hours?: number;
  readiness_level?: string;
  recommended_intensity?: string;
  alerts?: PlanAlert[];
  daily_tips?: string[];
  eating_window?: { start_time: string; end_time: string } | null;
  nutrition_focus?: string | null;
  morning_briefing?: string | null;
}

// ── Coach IA ─────────────────────────────────────────────────────────────────
export interface CoachAskRequest {
  question: string;
  thread_id?: string | null;
}

export interface CoachAnswerResponse {
  summary?: string;
  full_response?: string;
  recommendations?: string[];
  warnings?: string[];
  confidence?: number;
  context_tokens_estimate?: number;
  model_used?: string;
  thread_id?: string;
  message_id?: string;
}

export interface QuickAdviceRequest {
  topic?: string;
  question?: string;
}

export interface QuickAdviceResponse {
  advice?: string;
  answer?: string;
  recommendations?: string[];
  alert?: string | null;
  confidence?: number;
  model_used?: string;
  context_summary?: string;
}

export interface ConversationThread {
  id?: string;
  thread_id?: string;
  title?: string | null;
  summary?: string | null;
  created_at?: string;
  updated_at?: string;
  message_count?: number | null;
}

export interface ConversationMessage {
  id?: string;
  thread_id?: string;
  role: 'user' | 'coach' | 'assistant';
  content: string;
  created_at?: string;
  metadata?: Record<string, unknown> | null;
}

export interface ThreadListResponse {
  threads: ConversationThread[];
  total?: number;
}

export interface ThreadDetailResponse {
  thread?: ConversationThread;
  messages?: ConversationMessage[];
  // Flat access convenience
  thread_id?: string;
  title?: string | null;
  message_count?: number | null;
}

export interface CreateThreadRequest {
  title?: string;
}

// ── Analytics Dashboard (/analytics/*) ───────────────────────────────────────
export interface AnalyticsSummaryResponse {
  period_days: number;
  dau: number;
  wau: number;
  mau: number;
  dau_mau_ratio?: number;
  onboarding_rate?: number;
  onboarding_completion_rate?: number;
  total_users?: number;
  new_users?: number;
  active_users?: number;
  unique_users?: number;
  total_events?: number;
  journal_entries?: number;
  coach_questions?: number;
  briefing_opens?: number;
}

export interface EventCountResponse {
  event_name: string;
  count: number;
  unique_users?: number;
  date?: string;
}

export interface FunnelStepResponse {
  step_index: number;
  step_name: string;
  event_name: string;
  users_count: number;
  conversion_from_previous: number;
  drop_off_rate: number;
}

export interface OnboardingFunnelResponse {
  period_days: number;
  steps: FunnelStepResponse[];
  overall_conversion_rate: number;
}

export interface CohortRetentionResponse {
  cohort_week: string;
  users_count: number;
  retention_day1: number;
  retention_day7: number;
  retention_day30: number;
}

export interface FeatureEventCount {
  feature_name: string;
  event_count: number;
  unique_users?: number;
}

export interface FeatureUsageResponse {
  period_days?: number;
  features?: FeatureEventCount[];
  // Flat format
  briefing_views?: number;
  journal_entries?: number;
  coach_questions?: number;
  twin_views?: number;
  nutrition_logs?: number;
  biomarker_logs?: number;
  quick_advice_requests?: number;
  workout_logs?: number;
}

export interface CoachAnalyticsResponse {
  period_days?: number;
  total_questions?: number;
  total_quick_advice?: number;
  quick_advice_count?: number;
  unique_users_asking?: number;
  questions_per_active_user?: number;
  avg_questions_per_user?: number;
  follow_up_rate?: number;
}

export interface ApiEndpointStat {
  endpoint: string;
  method: string;
  request_count?: number;
  total_calls?: number;
  avg_latency_ms?: number;
  avg_response_ms?: number;
  p95_latency_ms?: number;
  p95_response_ms?: number;
  error_rate?: number;
}

export interface ApiPerformanceStatsResponse {
  endpoints: ApiEndpointStat[];
  buffer_size?: number;
  period_seconds?: number;
}

// ── Journal / History ─────────────────────────────────────────────────────────
export interface DailyMetricsRecord {
  date: string;
  weight_kg?: number | null;
  calories_consumed?: number;
  calories_target?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  protein_target_g?: number;
  water_ml?: number;
  hydration_ml?: number;
  hydration_target_ml?: number;
  steps_count?: number;
  steps?: number;
  workout_count?: number;
  readiness_score?: number | null;
}

export interface SleepRecord {
  date: string;
  duration_hours?: number;
  quality_score?: number;
  quality?: number;
  quality_label?: string;
  bedtime?: string | null;
  wake_time?: string | null;
}

// ── Sleep Analysis (/sleep/analysis) ─────────────────────────────────────────
export interface SleepArchitectureResponse {
  deep_pct: number;
  rem_pct: number;
  light_pct: number;
  awake_pct: number;
  architecture_score: number;
  architecture_quality: string;
  areas_to_improve: string[];
}

export interface SleepConsistencyResponse {
  avg_bedtime_hour: number | null;
  avg_wake_hour: number | null;
  bedtime_variance_min: number;
  wake_variance_min: number;
  consistency_score: number;
  consistency_label: string;
  sessions_analyzed: number;
}

export interface SleepProblemResponse {
  problem_type: string;
  severity: string;
  description: string;
  recommendation: string;
  evidence_days: number;
}

export interface SleepAnalysisResponse {
  architecture: SleepArchitectureResponse | null;
  consistency: SleepConsistencyResponse | null;
  problems: SleepProblemResponse[];
}

// ── User Profile ──────────────────────────────────────────────────────────────
export interface UserProfile {
  id: string;
  username: string;
  first_name?: string | null;
  age?: number | null;
  sex?: string | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  goal_weight_kg?: number | null;
  primary_goal?: string | null;
  activity_level?: string | null;
  calorie_target?: number | null;
  protein_target_g?: number | null;
  hydration_target_ml?: number | null;
  steps_goal?: number | null;
  plan_code?: string;
  plan_status?: string;
}

// ── Workout Sessions ────────────────────────────────────────────────────────
export interface WorkoutSession {
  id: string;
  user_id: string;
  started_at: string;
  ended_at?: string | null;
  duration_minutes?: number | null;
  session_type?: string | null;
  status: string;
  location?: string | null;
  total_tonnage_kg?: number | null;
  total_sets?: number | null;
  total_reps?: number | null;
  distance_km?: number | null;
  avg_heart_rate_bpm?: number | null;
  max_heart_rate_bpm?: number | null;
  calories_burned_kcal?: number | null;
  rpe_score?: number | null;
  energy_before?: number | null;
  energy_after?: number | null;
  perceived_difficulty?: number | null;
  notes?: string | null;
  is_completed: boolean;
  created_at: string;
}

export interface WorkoutSessionCreate {
  session_type: string;
  started_at?: string;
  location?: string;
  status?: string;
  notes?: string;
  energy_before?: number;
}

export interface WorkoutSessionUpdate {
  ended_at?: string;
  duration_minutes?: number;
  session_type?: string;
  status?: string;
  location?: string;
  notes?: string;
  rpe_score?: number;
  energy_before?: number;
  energy_after?: number;
  calories_burned_kcal?: number;
}

export interface WorkoutSessionListResponse {
  sessions: WorkoutSession[];
  total: number;
  page: number;
  per_page: number;
}

// ── Nutrition Entries ────────────────────────────────────────────────────────
export interface NutritionEntry {
  id: string;
  user_id: string;
  logged_at: string;
  meal_type?: string | null;
  meal_name?: string | null;
  food_item_id?: string | null;
  photo_id?: string | null;
  quantity_g?: number | null;
  calories?: number | null;
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
  fiber_g?: number | null;
  data_quality?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NutritionEntryCreate {
  meal_type?: string;
  meal_name?: string;
  logged_at?: string;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  notes?: string;
}

export interface NutritionEntryUpdate {
  meal_type?: string;
  meal_name?: string;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  notes?: string;
}

export interface NutritionEntryListResponse {
  entries: NutritionEntry[];
  total: number;
  date?: string;
}

export interface DailyNutritionSummary {
  date: string;
  meal_count: number;
  totals: { calories: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g: number };
  goals?: { calories_target?: number; protein_target_g?: number; carbs_target_g?: number; fat_target_g?: number } | null;
  balance?: { calories_delta?: number; protein_delta_g?: number; pct_calories_reached?: number; pct_protein_reached?: number } | null;
  meals: { id: string; meal_type?: string; meal_name?: string; logged_at: string; calories?: number; protein_g?: number }[];
  data_completeness_pct: number;
}


// ── Hydration ───────────────────────────────────────────────────────────────
export interface HydrationEntry {
  id: string;
  volume_ml: number;
  beverage_type?: string | null;
  logged_at: string;
}

export interface HydrationDaySummary {
  total_ml: number;
  target_ml: number;
  entries: HydrationEntry[];
  remaining_ml: number;
  status: string;
}

// ── Body Metrics ────────────────────────────────────────────────────────────
export interface BodyMetric {
  id: string;
  user_id: string;
  recorded_at: string;
  weight_kg?: number | null;
  body_fat_pct?: number | null;
  muscle_mass_kg?: number | null;
  waist_cm?: number | null;
}

export interface BodyMetricCreate {
  weight_kg?: number;
  body_fat_pct?: number;
  muscle_mass_kg?: number;
  waist_cm?: number;
}

export interface BodyMetricsTrend {
  entries: BodyMetric[];
  trend: string;
  current_bmi?: number | null;
}

// ── Health Insights ─────────────────────────────────────────────────────────
export interface HealthInsight {
  id: string;
  user_id: string;
  category: string;
  severity: string;
  title: string;
  message: string;
  metric_key?: string | null;
  metric_value?: number | null;
  recommendation?: string | null;
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
}

export interface InsightListResponse {
  insights: HealthInsight[];
  total: number;
}

// ── Scores ──────────────────────────────────────────────────────────────────
export interface ReadinessScore {
  score: number;
  date: string;
  components?: Record<string, number>;
  recommendation?: string;
}

export interface ReadinessScoreHistory {
  scores: ReadinessScore[];
  avg_score: number;
  trend: string;
}

export interface LongevityScore {
  overall_score: number;
  date: string;
  components: {
    cardio?: number;
    strength?: number;
    sleep?: number;
    nutrition?: number;
    weight?: number;
    body_comp?: number;
    consistency?: number;
  };
  biological_age_estimate?: number;
  chronological_age?: number;
}

// ── Exercises ───────────────────────────────────────────────────────────────
export interface Exercise {
  id: string;
  name: string;
  category: string;
  muscle_groups: string[];
  difficulty: string;
  description?: string;
  instructions?: string[];
  equipment?: string[];
}

export interface ExerciseListResponse {
  exercises: Exercise[];
  total: number;
  page: number;
  per_page: number;
}

export interface ExerciseEntry {
  id: string;
  session_id: string;
  exercise_id?: string | null;
  exercise_name: string;
  order_index: number;
  notes?: string | null;
  sets: ExerciseSet[];
}

export interface ExerciseEntryCreate {
  exercise_id?: string;
  exercise_name: string;
  order_index?: number;
  notes?: string;
}

export interface ExerciseSet {
  id: string;
  entry_id: string;
  set_number: number;
  reps?: number | null;
  weight_kg?: number | null;
  duration_seconds?: number | null;
  rpe?: number | null;
  is_warmup: boolean;
}

export interface SetCreate {
  set_number?: number;
  reps?: number;
  weight_kg?: number;
  duration_seconds?: number;
  rpe?: number;
  is_warmup?: boolean;
}

// ── Predictions ─────────────────────────────────────────────────────────────
export interface InjuryRiskResponse {
  risk_score: number;
  risk_level: string;
  acwr?: number;
  components?: Record<string, number>;
  recommendations: string[];
}

export interface OvertrainingResponse {
  overtraining_risk: number;
  acwr?: number;
  acwr_zone?: string;
  recommendation: string;
}

export interface HealthPredictions {
  injury_risk: InjuryRiskResponse;
  overtraining: OvertrainingResponse;
  weight_prediction?: {
    predicted_weight_kg: number;
    target_date: string;
    confidence: number;
  };
}

// ── Food Items ──────────────────────────────────────────────────────────────
export interface FoodItem {
  id: string;
  name: string;
  food_group?: string;
  calories_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  fiber_per_100g?: number;
  nova_score?: number;
}

export interface FoodItemListResponse {
  items: FoodItem[];
  total: number;
  page: number;
  per_page: number;
}
