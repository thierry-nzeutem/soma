'use client';

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { DailyMetricsRecord, SleepRecord } from '@/lib/types/api';
import type { MetricInfo } from './metric-detail-modal';
import { safeDateFormat } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import { Info } from 'lucide-react';

interface TrendChartsProps {
  metrics: DailyMetricsRecord[] | undefined;
  sleep: SleepRecord[] | undefined;
  isLoading: boolean;
  days: number;
  onChartClick?: (metric: MetricInfo) => void;
}

const CustomTooltip = ({ active, payload, label, unit }: { active?: boolean; payload?: any[]; label?: string; unit?: string }) => {
  if (!active || !payload?.length) return null;
  const val = payload[0]?.value;
  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="text-soma-muted mb-1">{label}</p>
      <p className="font-semibold text-soma-accent">
        {val != null ? `${Number(val).toFixed(1)}${unit ? ` ${unit}` : ''}` : '—'}
      </p>
    </div>
  );
};

function MiniChart({
  title, data, dataKey, color, unit, isLoading, onClick,
}: {
  title: string;
  data: any[];
  dataKey: string;
  color: string;
  unit?: string;
  isLoading?: boolean;
  onClick?: () => void;
}) {
  if (isLoading) {
    return (
      <div className="card-surface rounded-xl p-4 flex flex-col gap-3">
        <div className="h-4 w-24 bg-soma-border rounded animate-pulse" />
        <div className="h-24 bg-soma-border rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div
      className="card-surface rounded-xl p-4 cursor-pointer transition-all hover:ring-2 hover:ring-soma-accent/40 hover:shadow-lg group"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
    >
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          {title}
        </p>
        <Info size={12} className="text-soma-muted opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
      <div style={{ height: '100px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 2, right: 2, left: -32, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.25} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--soma-border)" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: 'var(--soma-muted)', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fill: 'var(--soma-muted)', fontSize: 10 }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
            <Tooltip content={(props) => <CustomTooltip {...(props as any)} unit={unit} />} />
            <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#grad-${dataKey})`} dot={false} activeDot={{ r: 3, strokeWidth: 0 }} connectNulls />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function TrendCharts({ metrics, sleep, isLoading, days, onChartClick }: TrendChartsProps) {
  const t = useTranslations();

  const metricTitle = (key: string) => {
    const title = t('metrics.' + key + '.title');
    // t() returns the key path as fallback if not found
    return title.startsWith('metrics.') ? key : title;
  };

  const metricsArr = Array.isArray(metrics) ? metrics : [];
  const sleepArr = Array.isArray(sleep) ? sleep : [];

  const metricsData = metricsArr.map((d) => ({
    date: safeDateFormat(d.date, 'd MMM', ''),
    weight_kg: d.weight_kg,
    calories_consumed: d.calories_consumed,
    protein_g: d.protein_g,
    water_ml: d.water_ml,
    steps: d.steps_count ?? d.steps,
  }));

  const sleepData = sleepArr.map((d) => ({
    date: safeDateFormat(d.date, 'd MMM', ''),
    duration_hours: d.duration_hours,
    quality_score: d.quality_score,
  }));

  function buildMetricInfo(key: string, rawData: { date: string; value: number | null | undefined }[]): MetricInfo {
    const prefix = 'metrics.' + key;
    const title = t(prefix + '.title');
    const unit = t(prefix + '.unit');
    const description = t(prefix + '.description');
    const goodRange = t(prefix + '.goodRange');
    const tips = t(prefix + '.tips');
    const chartConfigs: Record<string, { color: string; defaultTitle: string; defaultUnit: string }> = {
      weight_kg: { color: '#00E5A0', defaultTitle: 'Poids', defaultUnit: 'kg' },
      calories_consumed: { color: '#FF9500', defaultTitle: 'Calories', defaultUnit: 'kcal' },
      protein_g: { color: '#AF52DE', defaultTitle: 'Protéines', defaultUnit: 'g' },
      water_ml: { color: '#32ADE6', defaultTitle: 'Hydratation', defaultUnit: 'ml' },
      steps: { color: '#5AC8FA', defaultTitle: 'Pas', defaultUnit: 'pas' },
      duration_hours: { color: '#6E6AE8', defaultTitle: 'Durée sommeil', defaultUnit: 'h' },
      quality_score: { color: '#FF6B6B', defaultTitle: 'Qualité sommeil', defaultUnit: '/100' },
    };
    const cfg = chartConfigs[key] || { color: '#888', defaultTitle: key, defaultUnit: '' };
    const isFallback = (v: string, k: string) => v === k || v.startsWith('metrics.');
    return {
      key,
      title: isFallback(title, prefix + '.title') ? cfg.defaultTitle : title,
      unit: isFallback(unit, prefix + '.unit') ? cfg.defaultUnit : unit,
      description: isFallback(description, prefix + '.description') ? '' : description,
      goodRange: isFallback(goodRange, prefix + '.goodRange') ? '' : goodRange,
      tips: isFallback(tips, prefix + '.tips') ? '' : tips,
      color: cfg.color,
      data: rawData,
    };
  }

  function handleClick(key: string, source: 'metrics' | 'sleep') {
    if (!onChartClick) return;
    const arr = source === 'metrics' ? metricsArr : sleepArr;
    const rawData = arr.map((d: any) => ({ date: d.date, value: d[key] ?? null }));
    onChartClick(buildMetricInfo(key, rawData));
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-soma-muted text-center italic">{t('journal.clickForDetails')}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MiniChart title={metricTitle("weight_kg")} data={metricsData} dataKey="weight_kg" color="#00E5A0" unit="kg" isLoading={isLoading} onClick={() => handleClick('weight_kg', 'metrics')} />
        <MiniChart title={metricTitle("calories_consumed")} data={metricsData} dataKey="calories_consumed" color="#FF9500" unit="kcal" isLoading={isLoading} onClick={() => handleClick('calories_consumed', 'metrics')} />
        <MiniChart title={metricTitle("protein_g")} data={metricsData} dataKey="protein_g" color="#AF52DE" unit="g" isLoading={isLoading} onClick={() => handleClick('protein_g', 'metrics')} />
        <MiniChart title={metricTitle("water_ml")} data={metricsData} dataKey="water_ml" color="#32ADE6" unit="ml" isLoading={isLoading} onClick={() => handleClick('water_ml', 'metrics')} />
        <MiniChart title={metricTitle("steps")} data={metricsData} dataKey="steps" color="#5AC8FA" unit="pas" isLoading={isLoading} onClick={() => handleClick('steps', 'metrics')} />
        <MiniChart title={metricTitle("duration_hours")} data={sleepData} dataKey="duration_hours" color="#6E6AE8" unit="h" isLoading={isLoading} onClick={() => handleClick('duration_hours', 'sleep')} />
        <MiniChart title={metricTitle("quality_score")} data={sleepData} dataKey="quality_score" color="#FF6B6B" isLoading={isLoading} onClick={() => handleClick('quality_score', 'sleep')} />
      </div>
    </div>
  );
}

