import apiClient from './client';
import type { DailyMetricsRecord, SleepRecord } from '@/lib/types/api';

export async function getMetricsHistory(days = 30): Promise<DailyMetricsRecord[]> {
  const { data } = await apiClient.get<any>('/api/v1/metrics/history', {
    params: { days },
  });
  const raw: any[] = Array.isArray(data) ? data : (data.history ?? []);
  return raw.map((d) => ({
    date: d.date || d.metrics_date || '',
    weight_kg: d.weight_kg ?? null,
    calories_consumed: d.calories_consumed ?? d.calories ?? undefined,
    calories_target: d.calories_target ?? undefined,
    protein_g: d.protein_g ?? undefined,
    carbs_g: d.carbs_g ?? undefined,
    fat_g: d.fat_g ?? undefined,
    water_ml: d.water_ml ?? d.hydration_ml ?? undefined,
    hydration_ml: d.hydration_ml ?? d.water_ml ?? undefined,
    hydration_target_ml: d.hydration_target_ml ?? undefined,
    steps_count: d.steps_count ?? d.steps ?? undefined,
    steps: d.steps ?? d.steps_count ?? undefined,
    workout_count: d.workout_count ?? undefined,
    readiness_score: d.readiness_score ?? null,
  }));
}

export async function getSleepHistory(days = 30): Promise<SleepRecord[]> {
  const { data } = await apiClient.get<any>('/api/v1/sleep', {
    params: { days },
  });
  const raw: any[] = Array.isArray(data) ? data : (data.sessions ?? []);
  return raw.map((d) => {
    const startAt = d.start_at ? new Date(d.start_at) : null;
    const endAt = d.end_at ? new Date(d.end_at) : null;
    const pad = (n: number) => String(n).padStart(2, '0');
    const toDateStr = (dt: Date) => dt.getFullYear() + '-' + pad(dt.getMonth() + 1) + '-' + pad(dt.getDate());
    const toTimeStr = (dt: Date) => pad(dt.getHours()) + ':' + pad(dt.getMinutes());

    return {
      date: d.date || (startAt ? toDateStr(startAt) : ''),
      duration_hours: d.duration_hours ?? (d.duration_minutes ? +(d.duration_minutes / 60).toFixed(1) : undefined),
      quality_score: d.quality_score ?? (d.perceived_quality ? d.perceived_quality * 20 : undefined),
      quality: d.quality ?? d.perceived_quality ?? undefined,
      quality_label: d.quality_label ?? d.sleep_quality_label ?? undefined,
      bedtime: d.bedtime ?? (startAt ? toTimeStr(startAt) : null),
      wake_time: d.wake_time ?? (endAt ? toTimeStr(endAt) : null),
    };
  });
}
