'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  askCoach,
  quickAdvice,
  getCoachHistory,
  getThread,
  createThread,
} from '@/lib/api/coach';
import type { CoachAskRequest, QuickAdviceRequest } from '@/lib/types/api';

export function useCoachHistory() {
  return useQuery({
    queryKey: ['coach-history'],
    queryFn: () => getCoachHistory(),
    staleTime: 30 * 1000,
    retry: 1,
  });
}

export function useThread(threadId: string | null) {
  return useQuery({
    queryKey: ['coach-thread', threadId],
    queryFn: () => getThread(threadId!),
    enabled: !!threadId,
    staleTime: 10 * 1000,
    retry: 1,
  });
}

export function useAskCoach() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: CoachAskRequest) => askCoach(req),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['coach-thread', variables.thread_id] });
      queryClient.invalidateQueries({ queryKey: ['coach-history'] });
    },
  });
}

export function useQuickAdvice() {
  return useMutation({
    mutationFn: (req: QuickAdviceRequest) => quickAdvice(req),
  });
}

export function useCreateThread() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title: string) => createThread({ title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coach-history'] });
    },
  });
}
