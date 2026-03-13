import apiClient from './client';
import type {
  NutritionEntry, NutritionEntryCreate, NutritionEntryUpdate,
  NutritionEntryListResponse, DailyNutritionSummary,
} from '@/lib/types/api';

export async function getNutritionEntries(date?: string): Promise<NutritionEntryListResponse> {
  const { data } = await apiClient.get<any>('/api/v1/nutrition/entries', { params: date ? { date } : undefined });
  return {
    entries: Array.isArray(data) ? data : (data.entries ?? []),
    total: data.total ?? (Array.isArray(data) ? data.length : 0),
    date: data.date ?? date,
  };
}

export async function createNutritionEntry(body: NutritionEntryCreate): Promise<NutritionEntry> {
  const { data } = await apiClient.post<NutritionEntry>('/api/v1/nutrition/entries', body);
  return data;
}

export async function updateNutritionEntry(id: string, body: NutritionEntryUpdate): Promise<NutritionEntry> {
  const { data } = await apiClient.patch<NutritionEntry>(`/api/v1/nutrition/entries/${id}`, body);
  return data;
}

export async function deleteNutritionEntry(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/nutrition/entries/${id}`);
}

export async function getDailyNutritionSummary(date?: string): Promise<DailyNutritionSummary> {
  const { data } = await apiClient.get<DailyNutritionSummary>('/api/v1/nutrition/daily-summary', { params: date ? { date } : undefined });
  return data;
}
