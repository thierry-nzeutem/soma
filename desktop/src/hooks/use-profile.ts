'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProfile, updateProfile } from '@/lib/api/profile';
import type { UserProfile } from '@/lib/types/api';

export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => getProfile(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (updates: Partial<UserProfile>) => updateProfile(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });
}
