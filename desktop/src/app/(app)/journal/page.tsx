'use client';

import { useState } from 'react';
import { Moon } from 'lucide-react';
import { PeriodSelector } from '@/components/journal/period-selector';
import { TrendCharts } from '@/components/journal/trend-charts';
import { MetricsTable, SleepTable } from '@/components/journal/metrics-table';
import { SleepLogForm } from '@/components/journal/sleep-log-form';
import { MetricDetailModal } from '@/components/journal/metric-detail-modal';
import type { MetricInfo } from '@/components/journal/metric-detail-modal';
import { useMetricsHistory, useSleepHistory } from '@/hooks/use-journal';
import { useTranslations } from '@/lib/i18n/config';

export default function JournalPage() {
  const [days, setDays] = useState<number>(30);
  const [showSleepForm, setShowSleepForm] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<MetricInfo | null>(null);

  const metrics = useMetricsHistory(days);
  const sleep = useSleepHistory(days);
  const t = useTranslations();

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">{t('journal.title')}</h1>
            <p className="text-sm text-soma-muted">
              {t('journal.subtitle').replace('{days}', String(days))}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setShowSleepForm(true)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border border-soma-border bg-soma-surface text-soma-muted hover:text-soma-text hover:border-soma-accent/50 transition-colors"
            >
              <Moon size={13} />
              {t('journal.logSleep')}
            </button>
            <PeriodSelector value={days} onChange={setDays} />
          </div>
        </div>

        {showSleepForm && <SleepLogForm onClose={() => setShowSleepForm(false)} />}

        {/* Charts grid — clickable */}
        <TrendCharts
          metrics={metrics.data}
          sleep={sleep.data}
          isLoading={metrics.isLoading || sleep.isLoading}
          days={days}
          onChartClick={(m) => setSelectedMetric(m)}
        />

        {/* Metric detail modal */}
        <MetricDetailModal
          metric={selectedMetric}
          onClose={() => setSelectedMetric(null)}
          days={days}
          onDaysChange={setDays}
          onDataAdded={() => { metrics.refetch(); sleep.refetch(); }}
        />

        {/* Tables */}
        <div className="space-y-4">
          <MetricsTable data={metrics.data} isLoading={metrics.isLoading} />
          <SleepTable data={sleep.data} isLoading={sleep.isLoading} />
        </div>
      </div>
    </div>
  );
}
