import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { showToast } from '@/components/ui/toaster';
import { getHydrationToday, logHydration, deleteHydrationEntry } from '@/lib/api/hydration';

export function useHydrationToday() {
  return useQuery({
    queryKey: ['hydration-today'],
    queryFn: getHydrationToday,
    staleTime: 2 * 60 * 1000,
  });
}

export function useLogHydration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: logHydration,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['hydration-today'] });
      showToast('Hydratation ajoutée', 'success');
    },
  });
}

export function useDeleteHydration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteHydrationEntry(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['hydration-today'] });
      showToast('Entrée supprimée', 'info');
    },
  });
}
