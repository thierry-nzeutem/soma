import apiClient from './client';
import type {
  HomeSummaryResponse,
  DailyBriefingResponse,
  DailyHealthPlanResponse,
  SleepAnalysisResponse,
} from '@/lib/types/api';

export async function getHomeSummary(date?: string): Promise<HomeSummaryResponse> {
  const params = date ? { date } : {};
  const { data } = await apiClient.get<HomeSummaryResponse>('/api/v1/home/summary', { params });
  return data;
}

export async function getDailyBriefing(date?: string): Promise<DailyBriefingResponse> {
  const params = date ? { date } : {};
  const { data } = await apiClient.get<DailyBriefingResponse>('/api/v1/daily/briefing', { params });
  return data;
}

export async function getHealthPlan(date?: string): Promise<DailyHealthPlanResponse> {
  const params = date ? { date } : {};
  const { data } = await apiClient.get<DailyHealthPlanResponse>('/api/v1/health/plan/today', { params });
  return data;
}

export async function getSleepAnalysis(days: number = 14): Promise<SleepAnalysisResponse> {
  const { data } = await apiClient.get<SleepAnalysisResponse>('/api/v1/sleep/analysis', {
    params: { days },
  });
  return data;
}
