import apiClient from './client';
import type { UserProfile } from '@/lib/types/api';

export async function getProfile(): Promise<UserProfile> {
  const { data } = await apiClient.get<UserProfile>('/api/v1/profile');
  return data;
}

export async function updateProfile(
  updates: Partial<Pick<UserProfile, 'first_name' | 'age' | 'sex' | 'height_cm' | 'weight_kg' | 'goal_weight_kg' | 'primary_goal' | 'activity_level' | 'calorie_target' | 'protein_target_g' | 'hydration_target_ml' | 'steps_goal'>>
): Promise<UserProfile> {
  const { data } = await apiClient.put<UserProfile>('/api/v1/profile', updates);
  return data;
}
