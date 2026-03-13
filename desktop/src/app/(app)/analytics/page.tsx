'use client';

import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { KpiGrid } from '@/components/analytics/kpi-grid';
import { FunnelChart } from '@/components/analytics/funnel-chart';
import { CohortTable } from '@/components/analytics/cohort-table';
import { FeatureBars } from '@/components/analytics/feature-bars';
import { CoachMetrics } from '@/components/analytics/coach-metrics';
import { PerfTable } from '@/components/analytics/perf-table';
import { PeriodSelector } from '@/components/journal/period-selector';
import {
  useAnalyticsSummary,
  useOnboardingFunnel,
  useCohortRetention,
  useFeatureUsage,
  useCoachAnalytics,
  usePerformanceStats,
} from '@/hooks/use-analytics';
import { cn } from '@/lib/utils';

export default function AnalyticsPage() {
  const queryClient = useQueryClient();
  const [days, setDays] = useState(30);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const summary = useAnalyticsSummary(days);
  const funnel = useOnboardingFunnel(days);
  const cohort = useCohortRetention();
  const features = useFeatureUsage(days);
  const coachAnalytics = useCoachAnalytics(days);
  const perf = usePerformanceStats();

  async function handleRefresh() {
    setIsRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: ['analytics'] });
    setIsRefreshing(false);
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">Analytics Admin</h1>
            <p className="text-sm text-soma-muted">
              Tableau de bord produit & monitoring
            </p>
          </div>
          <div className="flex items-center gap-3">
            <PeriodSelector value={days} onChange={setDays} />
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium',
                'border border-soma-border bg-soma-surface text-soma-muted',
                'hover:text-soma-text hover:border-soma-accent/50 transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
              Actualiser
            </button>
          </div>
        </div>

        {/* KPIs row */}
        <KpiGrid data={summary.data} isLoading={summary.isLoading} />

        {/* Row 2: Funnel + Feature bars */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <FunnelChart data={funnel.data} isLoading={funnel.isLoading} />
          <FeatureBars data={features.data} isLoading={features.isLoading} />
        </div>

        {/* Row 3: Cohort retention + Coach analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <CohortTable data={cohort.data} isLoading={cohort.isLoading} />
          <CoachMetrics data={coachAnalytics.data} isLoading={coachAnalytics.isLoading} />
        </div>

        {/* Row 4: Performance table (full width) */}
        <PerfTable data={perf.data} isLoading={perf.isLoading} />
      </div>
    </div>
  );
}
