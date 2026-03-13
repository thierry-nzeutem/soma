import { apiClient } from './client';
import type { BodyMetricCreate, BodyMetricsTrend } from '@/lib/types/api';

export async function getBodyMetrics(days: number = 30): Promise<BodyMetricsTrend> {
  const { data } = await apiClient.get('/api/v1/body-metrics', { params: { days } });
  return data;
}

export async function createBodyMetric(body: BodyMetricCreate): Promise<unknown> {
  const { data } = await apiClient.post('/api/v1/body-metrics', body);
  return data;
}
