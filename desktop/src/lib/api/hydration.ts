import { apiClient } from './client';
import type { HydrationDaySummary } from '@/lib/types/api';

export async function getHydrationToday(): Promise<HydrationDaySummary> {
  const { data } = await apiClient.get('/api/v1/hydration/today');
  return data;
}

export async function logHydration(body: { volume_ml: number; beverage_type?: string }): Promise<{ volume_ml: number; message: string }> {
  const { data } = await apiClient.post('/api/v1/hydration/log', body);
  return data;
}

export async function deleteHydrationEntry(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/hydration/entries/${id}`);
}
