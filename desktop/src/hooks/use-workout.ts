'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWorkoutSessions, createWorkoutSession, updateWorkoutSession, deleteWorkoutSession,
} from '@/lib/api/workout';
import type { WorkoutSessionCreate, WorkoutSessionUpdate } from '@/lib/types/api';

export function useWorkoutSessions(page = 1) {
  return useQuery({
    queryKey: ['workout-sessions', page],
    queryFn: () => getWorkoutSessions(page),
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });
}

export function useCreateWorkout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WorkoutSessionCreate) => createWorkoutSession(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workout-sessions'] }),
  });
}

export function useUpdateWorkout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: WorkoutSessionUpdate }) => updateWorkoutSession(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workout-sessions'] }),
  });
}

export function useDeleteWorkout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteWorkoutSession(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workout-sessions'] }),
  });
}
