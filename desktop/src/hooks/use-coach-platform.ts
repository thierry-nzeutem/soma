/**
 * React Query hooks for SOMA Coach Platform.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getCoachProfile,
  getCoachDashboard,
  getAthleteFullProfile,
  getAthleteRecommendations,
  getInvitations,
  createInvitation,
  cancelInvitation,
  createRecommendation,
  updateRecommendationStatus,
  updateLinkStatus,
  registerCoach,
} from '@/lib/api/coach-platform';

export const coachKeys = {
  all: ['coach-platform'] as const,
  profile: () => [...coachKeys.all, 'profile'] as const,
  dashboard: () => [...coachKeys.all, 'dashboard'] as const,
  invitations: (status?: string) => [...coachKeys.all, 'invitations', status ?? 'all'] as const,
  athleteProfile: (id: string) => [...coachKeys.all, 'athlete', id, 'profile'] as const,
  athleteRecs: (id: string) => [...coachKeys.all, 'athlete', id, 'recommendations'] as const,
};

export function useCoachProfile() {
  return useQuery({
    queryKey: coachKeys.profile(),
    queryFn: getCoachProfile,
    retry: false,
  });
}

export function useCoachDashboard() {
  return useQuery({
    queryKey: coachKeys.dashboard(),
    queryFn: getCoachDashboard,
    staleTime: 2 * 60 * 1000, // 2 min
    refetchInterval: 5 * 60 * 1000, // 5 min polling
  });
}

export function useInvitations(status?: string) {
  return useQuery({
    queryKey: coachKeys.invitations(status),
    queryFn: () => getInvitations(status),
  });
}

export function useAthleteFullProfile(athleteId: string) {
  return useQuery({
    queryKey: coachKeys.athleteProfile(athleteId),
    queryFn: () => getAthleteFullProfile(athleteId),
    enabled: !!athleteId,
  });
}

export function useAthleteRecommendations(athleteId: string) {
  return useQuery({
    queryKey: coachKeys.athleteRecs(athleteId),
    queryFn: () => getAthleteRecommendations(athleteId),
    enabled: !!athleteId,
  });
}

export function useRegisterCoach() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: registerCoach,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: coachKeys.profile() });
    },
  });
}

export function useCreateInvitation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createInvitation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: coachKeys.invitations() });
    },
  });
}

export function useCancelInvitation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (inviteId: string) => cancelInvitation(inviteId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: coachKeys.invitations() });
    },
  });
}

export function useCreateRecommendation(athleteId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createRecommendation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: coachKeys.athleteRecs(athleteId) });
      qc.invalidateQueries({ queryKey: coachKeys.athleteProfile(athleteId) });
    },
  });
}

export function useUpdateRecommendation(athleteId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recId, status }: { recId: string; status: string }) =>
      updateRecommendationStatus(recId, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: coachKeys.athleteRecs(athleteId) });
    },
  });
}

export function useUpdateLinkStatus(athleteId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ status, notes }: { status: string; notes?: string }) =>
      updateLinkStatus(athleteId, status, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: coachKeys.athleteProfile(athleteId) });
      qc.invalidateQueries({ queryKey: coachKeys.dashboard() });
    },
  });
}
