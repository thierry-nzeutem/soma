import { apiClient } from '@/lib/api/client';
import type { EntitlementsData } from '@/lib/entitlements';

export async function getEntitlements(): Promise<EntitlementsData> {
  const { data } = await apiClient.get<EntitlementsData>('/api/v1/me/entitlements');
  return data;
}
