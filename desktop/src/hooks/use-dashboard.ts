'use client';

import { useQuery } from '@tanstack/react-query';
import { getHomeSummary, getDailyBriefing, getHealthPlan, getSleepAnalysis } from '@/lib/api/dashboard';

export function useHomeSummary() {
  return useQuery({
    queryKey: ['home-summary'],
    queryFn: () => getHomeSummary(),
    staleTime: 4 * 60 * 1000, // 4 minutes
    retry: 1,
  });
}

export function useDailyBriefing() {
  return useQuery({
    queryKey: ['daily-briefing'],
    queryFn: () => getDailyBriefing(),
    staleTime: 60 * 60 * 1000, // 1 hour
    retry: 1,
  });
}

export function useHealthPlan() {
  return useQuery({
    queryKey: ['health-plan'],
    queryFn: () => getHealthPlan(),
    staleTime: 6 * 60 * 60 * 1000, // 6 hours
    retry: 1,
  });
}

export function useSleepAnalysis(days: number = 14) {
  return useQuery({
    queryKey: ['sleep-analysis', days],
    queryFn: () => getSleepAnalysis(days),
    staleTime: 4 * 60 * 60 * 1000, // 4 hours
    retry: 1,
  });
}
