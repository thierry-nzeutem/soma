import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { showToast } from '@/components/ui/toaster';
import { getBodyMetrics, createBodyMetric } from '@/lib/api/body-metrics';

export function useBodyMetrics(days: number = 30) {
  return useQuery({
    queryKey: ['body-metrics', days],
    queryFn: () => getBodyMetrics(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateBodyMetric() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createBodyMetric,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['body-metrics'] });
      showToast('Mesure enregistrée', 'success');
    },
  });
}
