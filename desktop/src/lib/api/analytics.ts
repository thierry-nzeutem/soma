import apiClient from './client';
import type {
  AnalyticsSummaryResponse,
  EventCountResponse,
  OnboardingFunnelResponse,
  CohortRetentionResponse,
  FeatureUsageResponse,
  CoachAnalyticsResponse,
  ApiPerformanceStatsResponse,
} from '@/lib/types/api';

export async function getAnalyticsSummary(days = 30): Promise<AnalyticsSummaryResponse> {
  const { data } = await apiClient.get<AnalyticsSummaryResponse>('/api/v1/analytics/summary', {
    params: { days },
  });
  return data;
}

export async function getAnalyticsEvents(days = 30, limit = 20): Promise<EventCountResponse[]> {
  const { data } = await apiClient.get<EventCountResponse[]>('/api/v1/analytics/events', {
    params: { days, limit },
  });
  return data;
}

export async function getOnboardingFunnel(days = 30): Promise<OnboardingFunnelResponse> {
  const { data } = await apiClient.get<OnboardingFunnelResponse>('/api/v1/analytics/funnel/onboarding', {
    params: { days },
  });
  return data;
}

export async function getCohortRetention(maxCohorts = 8): Promise<CohortRetentionResponse[]> {
  const { data } = await apiClient.get<CohortRetentionResponse[]>('/api/v1/analytics/retention/cohorts', {
    params: { max_cohorts: maxCohorts },
  });
  return data;
}

export async function getFeatureUsage(days = 30): Promise<FeatureUsageResponse> {
  const { data } = await apiClient.get<FeatureUsageResponse>('/api/v1/analytics/features', {
    params: { days },
  });
  return data;
}

export async function getCoachAnalytics(days = 30): Promise<CoachAnalyticsResponse> {
  const { data } = await apiClient.get<CoachAnalyticsResponse>('/api/v1/analytics/coach', {
    params: { days },
  });
  return data;
}

export async function getPerformanceStats(limit = 20): Promise<ApiPerformanceStatsResponse> {
  const { data } = await apiClient.get<ApiPerformanceStatsResponse>('/api/v1/analytics/performance', {
    params: { limit },
  });
  return data;
}
