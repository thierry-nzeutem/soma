import { useQuery } from '@tanstack/react-query';
import {
  getBodyCompositionTrend,
  getWeightTrend,
  getCardioFitness,
  getActivityDay,
  getActivityPeriod,
  getHRAnalytics,
  getHRTimeline,
  getSleepQualityScore,
  getHRVScore,
  getGamificationProfile,
} from '@/lib/api/health-analytics';

export function useBodyCompositionTrend(period = 'month') {
  return useQuery({
    queryKey: ['body-composition-trend', period],
    queryFn: () => getBodyCompositionTrend(period),
    staleTime: 5 * 60 * 1000,
  });
}

export function useWeightTrend(period = 'month') {
  return useQuery({
    queryKey: ['weight-trend', period],
    queryFn: () => getWeightTrend(period),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCardioFitness() {
  return useQuery({
    queryKey: ['cardio-fitness'],
    queryFn: getCardioFitness,
    staleTime: 10 * 60 * 1000,
  });
}

export function useActivityDay(date?: string) {
  return useQuery({
    queryKey: ['activity-day', date ?? 'today'],
    queryFn: () => getActivityDay(date),
    staleTime: 2 * 60 * 1000,
  });
}

export function useActivityPeriod(period = 'week') {
  return useQuery({
    queryKey: ['activity-period', period],
    queryFn: () => getActivityPeriod(period),
    staleTime: 5 * 60 * 1000,
  });
}

export function useHRAnalytics(date?: string) {
  return useQuery({
    queryKey: ['hr-analytics', date ?? 'today'],
    queryFn: () => getHRAnalytics(date),
    staleTime: 2 * 60 * 1000,
  });
}

export function useHRTimeline(date?: string) {
  return useQuery({
    queryKey: ['hr-timeline', date ?? 'today'],
    queryFn: () => getHRTimeline(date),
    staleTime: 2 * 60 * 1000,
  });
}

export function useSleepQualityScore(date?: string) {
  return useQuery({
    queryKey: ['sleep-quality', date ?? 'today'],
    queryFn: () => getSleepQualityScore(date),
    staleTime: 5 * 60 * 1000,
  });
}

// ── HRV & Gamification (V2) ──────────────────────────────────────────────────
export function useHRVScore(dateStr?: string) {
  return useQuery({
    queryKey: ['hrv-score', dateStr],
    queryFn: () => getHRVScore(dateStr),
    staleTime: 1000 * 60 * 30, // 30 min
  });
}

export function useGamificationProfile() {
  return useQuery({
    queryKey: ['gamification-profile'],
    queryFn: getGamificationProfile,
    staleTime: 1000 * 60 * 15, // 15 min
  });
}
