import { apiClient } from './client';

// Body composition trend
export async function getBodyCompositionTrend(period = 'month') {
  const { data } = await apiClient.get('/api/v1/body/composition/trend', { params: { period } });
  return data; // { period, points: [{date, body_fat_pct, muscle_mass_pct, bone_mass_kg, visceral_fat_index, water_pct, metabolic_age}], segmentation_avg }
}

// Weight trend
export async function getWeightTrend(period = 'month') {
  const { data } = await apiClient.get('/api/v1/body/weight/trend', { params: { period } });
  return data; // { period, points: [{date, weight_kg, bmi, bmr_kcal, metabolic_age}], avg_weight_kg, avg_bmi }
}

// Cardio fitness
export async function getCardioFitness() {
  const { data } = await apiClient.get('/api/v1/fitness/cardio-fitness');
  return data; // { vo2max, category, percentile, age_group, improvement_suggestion, reference_bars: [{label, value}] }
}

// Activity day
export async function getActivityDay(date?: string) {
  const { data } = await apiClient.get('/api/v1/activity/day', { params: date ? { date } : {} });
  return data; // { date, total_steps, distance_km, active_calories_kcal, total_calories_kcal, avg_heart_rate_bpm, hourly_steps: [{hour, steps}] }
}

// Activity period
export async function getActivityPeriod(period = 'week') {
  const { data } = await apiClient.get('/api/v1/activity/period', { params: { period } });
  return data; // { period, total_steps, avg_daily_steps, total_distance_km, goal_days_count }
}

// Heart rate analytics
export async function getHRAnalytics(date?: string) {
  const { data } = await apiClient.get('/api/v1/heart-rate/analytics', { params: date ? { date } : {} });
  return data; // { date, avg_awake_bpm, avg_sleep_bpm, resting_hr_bpm, max_bpm, min_bpm, high_resting_events, low_resting_events }
}

// HR timeline
export async function getHRTimeline(date?: string) {
  const { data } = await apiClient.get('/api/v1/heart-rate/timeline', { params: date ? { date } : {} });
  return data; // { date, points: [{hour, avg_bpm, min_bpm, max_bpm}], avg_awake_bpm, avg_sleep_bpm }
}

// Sleep quality score
export async function getSleepQualityScore(date?: string) {
  const { data } = await apiClient.get('/api/v1/sleep/quality-score', { params: date ? { date } : {} });
  return data; // { date, overall_score, overall_label, duration_minutes, deep_sleep_minutes, rem_sleep_minutes, sub_scores: [{name, score, label}], hypnogram: [{stage, start_minute, duration_minutes}] }
}

// ── HRV & Stress (V2) ────────────────────────────────────────────────────────
export async function getHRVScore(dateStr?: string): Promise<HRVScoreData> {
  const { data } = await apiClient.get('/api/v1/hrv/score', { params: dateStr ? { date_str: dateStr } : {} });
  return data;
}

export async function getGamificationProfile(): Promise<GamificationProfile> {
  const { data } = await apiClient.get('/api/v1/gamification/profile');
  return data;
}

// ── Type definitions ──────────────────────────────────────────────────────────
export interface HRVDayPoint {
  date: string;
  avg_hrv_ms: number | null;
  min_hrv_ms: number | null;
  max_hrv_ms: number | null;
  sample_count: number;
}

export interface HRVScoreData {
  date: string;
  hrv_score: number | null;
  avg_hrv_ms: number | null;
  resting_hrv_ms: number | null;
  trend_7d: number | null;
  stress_score: number | null;
  stress_level: string;
  recovery_indicator: string;
  baseline_7d_ms: number | null;
  history: HRVDayPoint[];
  recommendation: string | null;
}

export interface StreakInfo {
  current: number;
  best: number;
  last_active: string | null;
  active_today: boolean;
}

export interface GamificationProfile {
  streaks: {
    activity: StreakInfo;
    nutrition_logging: StreakInfo;
    hydration: StreakInfo;
    sleep_logging: StreakInfo;
    overall_score: number;
  };
  achievements: Array<{
    id: string;
    title: string;
    description: string;
    icon: string;
    unlocked: boolean;
    progress: number;
  }>;
  level: number;
  level_name: string;
  xp: number;
  xp_to_next_level: number;
  total_days_active: number;
}
