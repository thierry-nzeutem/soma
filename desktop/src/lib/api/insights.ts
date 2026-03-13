import { apiClient } from './client';
import type { InsightListResponse } from '@/lib/types/api';

export async function getInsights(params?: { days?: number; category?: string; severity?: string; include_dismissed?: boolean }): Promise<InsightListResponse> {
  const { data } = await apiClient.get('/api/v1/insights', { params });
  return data;
}

export async function runInsights(date?: string): Promise<InsightListResponse> {
  const { data } = await apiClient.post('/api/v1/insights/run', null, { params: date ? { date } : undefined });
  return data;
}

export async function markInsightRead(id: string): Promise<unknown> {
  const { data } = await apiClient.patch(`/api/v1/insights/${id}/read`);
  return data;
}

export async function dismissInsight(id: string): Promise<unknown> {
  const { data } = await apiClient.patch(`/api/v1/insights/${id}/dismiss`);
  return data;
}
