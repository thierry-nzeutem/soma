import { apiClient } from './client';
import type { ExerciseListResponse, ExerciseEntry, ExerciseEntryCreate, ExerciseSet, SetCreate } from '@/lib/types/api';

export async function getExercises(params?: { category?: string; difficulty?: string; search?: string; page?: number; per_page?: number }): Promise<ExerciseListResponse> {
  const { data } = await apiClient.get('/api/v1/exercises', { params });
  return data;
}

export async function getSessionExercises(sessionId: string): Promise<ExerciseEntry[]> {
  const { data } = await apiClient.get(`/api/v1/sessions/${sessionId}`);
  return data.exercises ?? [];
}

export async function addExerciseToSession(sessionId: string, body: ExerciseEntryCreate): Promise<ExerciseEntry> {
  const { data } = await apiClient.post(`/api/v1/sessions/${sessionId}/exercises`, body);
  return data;
}

export async function deleteExerciseFromSession(sessionId: string, entryId: string): Promise<void> {
  await apiClient.delete(`/api/v1/sessions/${sessionId}/exercises/${entryId}`);
}

export async function addSet(sessionId: string, entryId: string, body: SetCreate): Promise<ExerciseSet> {
  const { data } = await apiClient.post(`/api/v1/sessions/${sessionId}/exercises/${entryId}/sets`, body);
  return data;
}

export async function deleteSet(sessionId: string, entryId: string, setId: string): Promise<void> {
  await apiClient.delete(`/api/v1/sessions/${sessionId}/exercises/${entryId}/sets/${setId}`);
}
