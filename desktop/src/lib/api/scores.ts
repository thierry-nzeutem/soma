import { apiClient } from './client';
import type { ReadinessScore, ReadinessScoreHistory, LongevityScore } from '@/lib/types/api';

export async function getReadinessToday(date?: string): Promise<ReadinessScore> {
  const { data } = await apiClient.get('/api/v1/scores/readiness/today', { params: date ? { date } : undefined });
  return data;
}

export async function getReadinessHistory(days: number = 30): Promise<ReadinessScoreHistory> {
  const { data } = await apiClient.get('/api/v1/scores/readiness/history', { params: { days } });
  return data;
}

export async function getLongevityScore(days: number = 30): Promise<LongevityScore> {
  const { data } = await apiClient.get('/api/v1/scores/longevity', { params: { days } });
  return data;
}
