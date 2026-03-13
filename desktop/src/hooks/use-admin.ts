'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAdminStats,
  getAdminUsers,
  updateUserPlan,
  getSettings,
  updateSetting,
  getFeatureUsageStats,
} from '@/lib/api/admin';

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: getAdminStats,
    staleTime: 60 * 1000,
  });
}

export function useAdminUsers(params?: { plan_code?: string; search?: string }) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => getAdminUsers(params),
    staleTime: 30 * 1000,
  });
}

export function useUpdateUserPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, plan }: { userId: string; plan: { plan_code: string; plan_status?: string } }) =>
      updateUserPlan(userId, plan),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'users'] });
      qc.invalidateQueries({ queryKey: ['admin', 'stats'] });
    },
  });
}

export function useAdminSettings(category?: string) {
  return useQuery({
    queryKey: ['admin', 'settings', category],
    queryFn: () => getSettings(category),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateSetting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: string | null }) =>
      updateSetting(key, value),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'settings'] });
    },
  });
}

export function useFeatureUsageStats(days?: number) {
  return useQuery({
    queryKey: ['admin', 'feature-usage', days],
    queryFn: () => getFeatureUsageStats(days),
    staleTime: 5 * 60 * 1000,
  });
}
