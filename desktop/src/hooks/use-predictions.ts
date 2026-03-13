import { useQuery } from '@tanstack/react-query';
import { getHealthPredictions, getInjuryRisk, getOvertrainingRisk } from '@/lib/api/predictions';

export function useHealthPredictions(targetDate?: string) {
  return useQuery({
    queryKey: ['health-predictions', targetDate],
    queryFn: () => getHealthPredictions(targetDate),
    staleTime: 10 * 60 * 1000,
  });
}

export function useInjuryRisk(targetDate?: string) {
  return useQuery({
    queryKey: ['injury-risk', targetDate],
    queryFn: () => getInjuryRisk(targetDate),
    staleTime: 10 * 60 * 1000,
  });
}

export function useOvertrainingRisk(targetDate?: string) {
  return useQuery({
    queryKey: ['overtraining-risk', targetDate],
    queryFn: () => getOvertrainingRisk(targetDate),
    staleTime: 10 * 60 * 1000,
  });
}
