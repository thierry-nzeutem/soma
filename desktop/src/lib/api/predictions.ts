import { apiClient } from './client';
import type { HealthPredictions, InjuryRiskResponse, OvertrainingResponse } from '@/lib/types/api';

export async function getHealthPredictions(targetDate?: string): Promise<HealthPredictions> {
  const { data } = await apiClient.get('/api/v1/health/predictions', { params: targetDate ? { target_date: targetDate } : undefined });
  return data;
}

export async function getInjuryRisk(targetDate?: string): Promise<InjuryRiskResponse> {
  const { data } = await apiClient.get('/api/v1/health/injury-risk', { params: targetDate ? { target_date: targetDate } : undefined });
  return data;
}

export async function getOvertrainingRisk(targetDate?: string): Promise<OvertrainingResponse> {
  const { data } = await apiClient.get('/api/v1/health/overtraining', { params: targetDate ? { target_date: targetDate } : undefined });
  return data;
}
