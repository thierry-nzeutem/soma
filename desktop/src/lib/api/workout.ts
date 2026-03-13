import apiClient from './client';
import type {
  WorkoutSession, WorkoutSessionCreate, WorkoutSessionUpdate, WorkoutSessionListResponse,
} from '@/lib/types/api';

export async function getWorkoutSessions(page = 1, perPage = 20): Promise<WorkoutSessionListResponse> {
  const { data } = await apiClient.get<any>('/api/v1/sessions', { params: { page, per_page: perPage } });
  return {
    sessions: Array.isArray(data) ? data : (data.sessions ?? []),
    total: data.total ?? (Array.isArray(data) ? data.length : 0),
    page: data.page ?? page,
    per_page: data.per_page ?? perPage,
  };
}

export async function getWorkoutSession(id: string): Promise<WorkoutSession> {
  const { data } = await apiClient.get<any>(`/api/v1/sessions/${id}`);
  return data;
}

export async function createWorkoutSession(body: WorkoutSessionCreate): Promise<WorkoutSession> {
  const { data } = await apiClient.post<WorkoutSession>('/api/v1/sessions', body);
  return data;
}

export async function updateWorkoutSession(id: string, body: WorkoutSessionUpdate): Promise<WorkoutSession> {
  const { data } = await apiClient.patch<WorkoutSession>(`/api/v1/sessions/${id}`, body);
  return data;
}

export async function deleteWorkoutSession(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/sessions/${id}`);
}
