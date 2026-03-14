/**
 * SOMA Coach Platform API — human coaching module.
 */
import { apiClient } from './client';

const BASE = '/coach-platform';

// ── Types ────────────────────────────────────────────────────────────────────

export interface CoachProfile {
  id: string;
  user_id: string;
  name: string;
  specializations: string[];
  certification?: string;
  bio?: string;
  max_athletes: number;
  is_active: boolean;
  athlete_count: number;
}

export interface AthleteSummary {
  athlete_id: string;
  athlete_name: string;
  readiness_score?: number;
  fatigue_score?: number;
  movement_health_score?: number;
  biological_age_delta?: number;
  days_since_last_session?: number;
  training_load_this_week?: number;
  sleep_quality?: number;
  nutrition_compliance?: number;
  acwr?: number;
  risk_level: 'green' | 'yellow' | 'orange' | 'red';
  alerts: string[];
}

export interface CoachDashboard {
  coach_id: string;
  total_athletes: number;
  athletes_at_risk: number;
  athletes_summary: AthleteSummary[];
}

export interface CoachInvitation {
  id: string;
  coach_profile_id: string;
  invite_code: string;
  invite_token: string;
  invite_link: string;
  invitee_email?: string;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  message?: string;
  expires_at: string;
  accepted_at?: string;
  created_at: string;
}

export interface CoachRecommendation {
  id: string;
  coach_id: string;
  athlete_id: string;
  rec_type: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed' | 'dismissed';
  title: string;
  description: string;
  target_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AthleteFullProfile {
  athlete_profile_id: string;
  user_id: string;
  display_name: string;
  sport?: string;
  goal?: string;
  date_of_birth?: string;
  first_name?: string;
  age?: number;
  sex?: string;
  height_cm?: number;
  activity_level?: string;
  fitness_level?: string;
  link_status: string;
  linked_at?: string;
  relationship_notes?: string;
  recent_notes_count: number;
  pending_recommendations_count: number;
}

// ── API functions ─────────────────────────────────────────────────────────────

export async function getCoachProfile(): Promise<CoachProfile> {
  const { data } = await apiClient.get<CoachProfile>(`${BASE}/coach/profile`);
  return data;
}

export async function registerCoach(payload: {
  name: string;
  specializations?: string[];
  certification?: string;
  bio?: string;
  max_athletes?: number;
}): Promise<CoachProfile> {
  const { data } = await apiClient.post<CoachProfile>(`${BASE}/coach/register`, payload);
  return data;
}

export async function getCoachDashboard(): Promise<CoachDashboard> {
  const { data } = await apiClient.get<CoachDashboard>(`${BASE}/dashboard`);
  return data;
}

export async function getAthleteFullProfile(athleteId: string): Promise<AthleteFullProfile> {
  const { data } = await apiClient.get<AthleteFullProfile>(`${BASE}/athlete/${athleteId}/profile`);
  return data;
}

export async function getAthleteRecommendations(athleteId: string): Promise<CoachRecommendation[]> {
  const { data } = await apiClient.get<CoachRecommendation[]>(
    `${BASE}/athlete/${athleteId}/recommendations`
  );
  return data;
}

export async function getInvitations(status?: string): Promise<CoachInvitation[]> {
  const url = status ? `${BASE}/invitations?status=${status}` : `${BASE}/invitations`;
  const { data } = await apiClient.get<CoachInvitation[]>(url);
  return data;
}

export async function createInvitation(payload: {
  invitee_email?: string;
  message?: string;
  expire_days?: number;
}): Promise<CoachInvitation> {
  const { data } = await apiClient.post<CoachInvitation>(`${BASE}/invitations`, payload);
  return data;
}

export async function cancelInvitation(inviteId: string): Promise<void> {
  await apiClient.delete(`${BASE}/invitations/${inviteId}`);
}

export async function createRecommendation(payload: {
  athlete_id: string;
  rec_type?: string;
  priority?: string;
  title: string;
  description: string;
  target_date?: string;
}): Promise<CoachRecommendation> {
  const { data } = await apiClient.post<CoachRecommendation>(`${BASE}/recommendations`, payload);
  return data;
}

export async function updateRecommendationStatus(
  recId: string,
  status: string
): Promise<CoachRecommendation> {
  const { data } = await apiClient.patch<CoachRecommendation>(
    `${BASE}/recommendations/${recId}`,
    { status }
  );
  return data;
}

export async function updateLinkStatus(
  athleteId: string,
  status: string,
  notes?: string
): Promise<void> {
  await apiClient.patch(`${BASE}/athlete/${athleteId}/status`, {
    status,
    ...(notes !== undefined && { notes }),
  });
}
