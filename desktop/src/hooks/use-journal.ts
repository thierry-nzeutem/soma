'use client';

import { useQuery } from '@tanstack/react-query';
import { getMetricsHistory, getSleepHistory } from '@/lib/api/journal';

export function useMetricsHistory(days: number) {
  return useQuery({
    queryKey: ['metrics-history', days],
    queryFn: () => getMetricsHistory(days),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: days > 0,
  });
}

export function useSleepHistory(days: number) {
  return useQuery({
    queryKey: ['sleep-history', days],
    queryFn: () => getSleepHistory(days),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: days > 0,
  });
}
