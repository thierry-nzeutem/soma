import apiClient from './client';
import type {
  CoachAskRequest,
  CoachAnswerResponse,
  QuickAdviceRequest,
  QuickAdviceResponse,
  ThreadListResponse,
  ThreadDetailResponse,
  ConversationThread,
  CreateThreadRequest,
} from '@/lib/types/api';

export async function askCoach(request: CoachAskRequest): Promise<CoachAnswerResponse> {
  const { data } = await apiClient.post<CoachAnswerResponse>('/api/v1/coach/ask', request);
  return data;
}

export async function quickAdvice(request: QuickAdviceRequest): Promise<QuickAdviceResponse> {
  const { data } = await apiClient.post<QuickAdviceResponse>('/api/v1/coach/quick-advice', request);
  return data;
}

export async function getCoachHistory(limit = 20): Promise<ThreadListResponse> {
  const { data } = await apiClient.get<ThreadListResponse>('/api/v1/coach/history', {
    params: { limit },
  });
  return data;
}

export async function getThread(threadId: string, limit = 100): Promise<ThreadDetailResponse> {
  const { data } = await apiClient.get<ThreadDetailResponse>(`/api/v1/coach/history/${threadId}`, {
    params: { limit },
  });
  return data;
}

export async function createThread(request: CreateThreadRequest = {}): Promise<ConversationThread> {
  const { data } = await apiClient.post<ConversationThread>('/api/v1/coach/thread', request);
  return data;
}
