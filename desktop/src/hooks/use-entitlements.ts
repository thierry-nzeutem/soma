'use client';

import { useQuery } from '@tanstack/react-query';
import { getEntitlements } from '@/lib/api/entitlements';
import { hasFeature } from '@/lib/entitlements';

export function useEntitlements() {
  return useQuery({
    queryKey: ['entitlements'],
    queryFn: getEntitlements,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

export function useEntitlement(feature: string): boolean {
  const { data } = useEntitlements();
  return hasFeature(data, feature);
}

export function useCurrentPlan(): string {
  const { data } = useEntitlements();
  return data?.plan_code ?? 'free';
}
