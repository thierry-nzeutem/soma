import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getInsights, markInsightRead, dismissInsight } from '@/lib/api/insights';

export function useInsights(params?: { days?: number; category?: string; severity?: string }) {
  return useQuery({
    queryKey: ['insights', params],
    queryFn: () => getInsights(params),
    staleTime: 3 * 60 * 1000,
  });
}

export function useMarkInsightRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: markInsightRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['insights'] });
    },
  });
}

export function useDismissInsight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: dismissInsight,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['insights'] });
    },
  });
}
