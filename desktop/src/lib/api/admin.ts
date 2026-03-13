import { apiClient } from '@/lib/api/client';

export interface AppSetting {
  key: string;
  value: string | null;
  description: string | null;
  category: string;
  updated_at: string;
}

export interface AdminUser {
  id: string;
  username: string;
  email: string | null;
  is_active: boolean;
  is_superuser: boolean;
  plan_code: string;
  plan_status: string;
  stripe_customer_id: string | null;
  plan_started_at: string | null;
  plan_expires_at: string | null;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  active_paid_subscriptions: number;
  plan_distribution: Array<{ plan_code: string; plan_status: string; count: number }>;
  feature_usage_7d: Array<{ event_type: string; count: number }>;
}

export interface FeatureUsageStat {
  feature_code: string;
  event_type: string;
  count: number;
  unique_users: number;
}

export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await apiClient.get<AdminStats>('/api/v1/admin/stats');
  return data;
}

export async function getAdminUsers(params?: {
  plan_code?: string;
  search?: string;
  limit?: number;
}): Promise<AdminUser[]> {
  const { data } = await apiClient.get<AdminUser[]>('/api/v1/admin/users', { params });
  return data;
}

export async function updateUserPlan(
  userId: string,
  plan: { plan_code: string; plan_status?: string; plan_expires_at?: string | null }
): Promise<AdminUser> {
  const { data } = await apiClient.put<AdminUser>(`/api/v1/admin/users/${userId}/plan`, plan);
  return data;
}

export async function getSettings(category?: string): Promise<AppSetting[]> {
  const { data } = await apiClient.get<AppSetting[]>('/api/v1/admin/settings', {
    params: category ? { category } : undefined,
  });
  return data;
}

export async function updateSetting(key: string, value: string | null): Promise<AppSetting> {
  const { data } = await apiClient.put<AppSetting>(`/api/v1/admin/settings/${key}`, { value });
  return data;
}

export async function getFeatureUsageStats(days?: number): Promise<FeatureUsageStat[]> {
  const { data } = await apiClient.get<FeatureUsageStat[]>('/api/v1/admin/feature-usage', {
    params: { days: days ?? 30 },
  });
  return data;
}
