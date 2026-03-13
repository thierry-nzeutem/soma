'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { showToast } from '@/components/ui/toaster';
import {
  getNutritionEntries, createNutritionEntry, updateNutritionEntry,
  deleteNutritionEntry, getDailyNutritionSummary,
} from '@/lib/api/nutrition';
import type { NutritionEntryCreate, NutritionEntryUpdate } from '@/lib/types/api';

export function useNutritionEntries(date?: string) {
  return useQuery({
    queryKey: ['nutrition-entries', date],
    queryFn: () => getNutritionEntries(date),
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });
}

export function useDailyNutritionSummary(date?: string) {
  return useQuery({
    queryKey: ['nutrition-summary', date],
    queryFn: () => getDailyNutritionSummary(date),
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });
}

export function useCreateNutritionEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: NutritionEntryCreate) => createNutritionEntry(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['nutrition-entries'] });
      qc.invalidateQueries({ queryKey: ['nutrition-summary'] });
      showToast('Repas ajouté', 'success');
    },
  });
}

export function useUpdateNutritionEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: NutritionEntryUpdate }) => updateNutritionEntry(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['nutrition-entries'] });
      qc.invalidateQueries({ queryKey: ['nutrition-summary'] });
    },
  });
}

export function useDeleteNutritionEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteNutritionEntry(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['nutrition-entries'] });
      qc.invalidateQueries({ queryKey: ['nutrition-summary'] });
      showToast('Repas supprimé', 'info');
    },
  });
}
