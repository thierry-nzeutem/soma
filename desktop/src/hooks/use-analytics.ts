'use client';

import { useQuery } from '@tanstack/react-query';
import {
  getAnalyticsSummary,
  getAnalyticsEvents,
  getOnboardingFunnel,
  getCohortRetention,
  getFeatureUsage,
  getCoachAnalytics,
  getPerformanceStats,
} from '@/lib/api/analytics';

const STALE = 5 * 60 * 1000; // 5 minutes

export function useAnalyticsSummary(days = 30) {
  return useQuery({
    queryKey: ['analytics-summary', days],
    queryFn: () => getAnalyticsSummary(days),
    staleTime: STALE,
    retry: 1,
  });
}

export function useAnalyticsEvents(days = 30) {
  return useQuery({
    queryKey: ['analytics-events', days],
    queryFn: () => getAnalyticsEvents(days),
    staleTime: STALE,
    retry: 1,
  });
}

export function useOnboardingFunnel(days = 30) {
  return useQuery({
    queryKey: ['analytics-funnel', days],
    queryFn: () => getOnboardingFunnel(days),
    staleTime: STALE,
    retry: 1,
  });
}

export function useCohortRetention() {
  return useQuery({
    queryKey: ['analytics-retention'],
    queryFn: () => getCohortRetention(),
    staleTime: STALE,
    retry: 1,
  });
}

export function useFeatureUsage(days = 30) {
  return useQuery({
    queryKey: ['analytics-features', days],
    queryFn: () => getFeatureUsage(days),
    staleTime: STALE,
    retry: 1,
  });
}

export function useCoachAnalytics(days = 30) {
  return useQuery({
    queryKey: ['analytics-coach', days],
    queryFn: () => getCoachAnalytics(days),
    staleTime: STALE,
    retry: 1,
  });
}

export function usePerformanceStats() {
  return useQuery({
    queryKey: ['analytics-performance'],
    queryFn: () => getPerformanceStats(),
    staleTime: 60 * 1000, // 1 minute — more volatile
    retry: 1,
  });
}
