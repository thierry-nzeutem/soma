'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { HealthKPIs } from '@/components/dashboard/health-kpis';
import { BriefingPanel } from '@/components/dashboard/briefing-panel';
import { HealthPlanCard } from '@/components/dashboard/health-plan-card';
import { AlertsPanel } from '@/components/dashboard/alerts-panel';
import { TrendsChart } from '@/components/dashboard/trends-chart';
import { SleepCard } from '@/components/dashboard/sleep-card';
import { useHomeSummary, useDailyBriefing, useHealthPlan } from '@/hooks/use-dashboard';
import { getMetricsHistory } from '@/lib/api/journal';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const summary = useHomeSummary();
  const briefing = useDailyBriefing();
  const plan = useHealthPlan();
  const metrics = useQuery({
    queryKey: ['metrics-history', 7],
    queryFn: () => getMetricsHistory(7),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  async function handleRefresh() {
    setIsRefreshing(true);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['home-summary'] }),
      queryClient.invalidateQueries({ queryKey: ['daily-briefing'] }),
      queryClient.invalidateQueries({ queryKey: ['health-plan'] }),
      queryClient.invalidateQueries({ queryKey: ['metrics-history'] }),
      queryClient.invalidateQueries({ queryKey: ['sleep-analysis'] }),
    ]);
    setIsRefreshing(false);
  }

  const t = useTranslations();

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Page-level refresh */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">{t('dashboard.title')}</h1>
            <p className="text-sm text-soma-muted">{t('dashboard.subtitle')}</p>
          </div>
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
            <RefreshCw
              size={13}
              className={isRefreshing ? 'animate-spin' : ''}
            />
            {t('dashboard.refresh')}
          </button>
        </div>

        {/* KPI row */}
        <HealthKPIs data={summary.data} isLoading={summary.isLoading} />

        {/* Main grid: left (briefing + plan) | right (trends + alerts) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Left column */}
          <div className="space-y-5">
            <BriefingPanel data={briefing.data} isLoading={briefing.isLoading} />
            <HealthPlanCard data={plan.data} isLoading={plan.isLoading} />
            <SleepCard />
          </div>

          {/* Right column */}
          <div className="flex flex-col gap-5">
            {/* Trends chart — takes available height */}
            <div style={{ height: '280px' }}>
              <TrendsChart data={metrics.data} isLoading={metrics.isLoading} />
            </div>
            {/* Alerts + insights */}
            <AlertsPanel data={summary.data} isLoading={summary.isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}
