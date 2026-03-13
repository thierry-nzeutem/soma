import { useQuery } from '@tanstack/react-query';
import { getReadinessToday, getReadinessHistory, getLongevityScore } from '@/lib/api/scores';

export function useReadinessToday(date?: string) {
  return useQuery({
    queryKey: ['readiness-today', date],
    queryFn: () => getReadinessToday(date),
    staleTime: 5 * 60 * 1000,
  });
}

export function useReadinessHistory(days: number = 30) {
  return useQuery({
    queryKey: ['readiness-history', days],
    queryFn: () => getReadinessHistory(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLongevityScore(days: number = 30) {
  return useQuery({
    queryKey: ['longevity-score', days],
    queryFn: () => getLongevityScore(days),
    staleTime: 5 * 60 * 1000,
  });
}
