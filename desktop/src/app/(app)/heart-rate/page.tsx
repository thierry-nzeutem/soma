'use client';

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { HeartPulse, Loader2, AlertTriangle } from 'lucide-react';
import { useHRAnalytics, useHRTimeline } from '@/hooks/use-health-analytics';
import { useTranslations } from '@/lib/i18n/config';
import { cn } from '@/lib/utils';

// Color by BPM zone
function bpmFill(bpm: number): string {
  if (bpm < 60) return '#60a5fa';  // blue-400
  if (bpm <= 100) return '#34d399'; // emerald-400
  return '#f97316'; // orange-500
}

// HR stat card
interface HRCardProps {
  label: string;
  value: number | null;
  unit?: string;
  accent: string;
}

function HRCard({ label, value, unit = 'bpm', accent }: HRCardProps) {
  return (
    <div className={cn('card-surface flex flex-col gap-1 p-4', accent)}>
      <span className="text-xs text-soma-muted font-medium">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-soma-text">
          {value != null ? value.toFixed(0) : '—'}
        </span>
        <span className="text-xs text-soma-muted">{unit}</span>
      </div>
    </div>
  );
}

// Custom tooltip
function BpmTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string | number;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-soma-muted">{label}h</p>
      <p className="font-semibold text-soma-text">{payload[0].value} bpm</p>
    </div>
  );
}

export default function HeartRatePage() {
  const tCommon = useTranslations('common');

  const analytics = useHRAnalytics();
  const timeline = useHRTimeline();

  const avgAwake = analytics.data?.avg_awake_bpm ?? null;
  const avgSleep = analytics.data?.avg_sleep_bpm ?? null;
  const resting = analytics.data?.resting_hr_bpm ?? null;
  const maxBpm = analytics.data?.max_bpm ?? null;
  const highEvents: Array<unknown> = analytics.data?.high_resting_events ?? [];
  const lowEvents: Array<unknown> = analytics.data?.low_resting_events ?? [];

  const timelinePoints: Array<{ hour: number; avg_bpm: number; min_bpm: number; max_bpm: number }> =
    timeline.data?.points ?? [];

  // Ensure 24 bars
  const chartData = Array.from({ length: 24 }, (_, h) => {
    const pt = timelinePoints.find((p) => p.hour === h);
    return { hour: h, avg_bpm: pt?.avg_bpm ?? 0 };
  });

  const isLoading = analytics.isLoading || timeline.isLoading;
  const isError = analytics.isError || timeline.isError;

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">

        <div className="flex items-center gap-3">
          <HeartPulse size={20} className="text-red-400 shrink-0" />
          <div>
            <h1 className="text-lg font-semibold text-soma-text">Fréquence cardiaque</h1>
            <p className="text-sm text-soma-muted">Rythme cardiaque &amp; zones du jour</p>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : isError ? (
          <p className="text-sm text-soma-danger">{tCommon('error')}</p>
        ) : (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <HRCard label="FC moy. éveillé" value={avgAwake} accent="border-l-2 border-l-red-400/50" />
              <HRCard label="FC moy. sommeil" value={avgSleep} accent="border-l-2 border-l-blue-400/50" />
              <HRCard label="FC repos" value={resting} accent="border-l-2 border-l-emerald-400/50" />
              <HRCard label="FC max" value={maxBpm} accent="border-l-2 border-l-orange-400/50" />
            </div>

            {/* 24h Timeline chart */}
            <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-soma-text mb-4">Timeline 24h</h2>
              {timelinePoints.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 gap-2">
                  <HeartPulse size={28} className="text-soma-muted/40" />
                  <p className="text-sm text-soma-muted">{tCommon('noData')}</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="hour"
                      tick={{ fontSize: 10, fill: 'var(--soma-muted, #888)' }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(h: number) => (h % 6 === 0 ? String(h) + 'h' : '')}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: 'var(--soma-muted, #888)' }}
                      tickLine={false}
                      axisLine={false}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip content={<BpmTooltip />} cursor={false} />
                    <Bar dataKey="avg_bpm" radius={[3, 3, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={'cell-' + index}
                          fill={entry.avg_bpm > 0 ? bpmFill(entry.avg_bpm) : '#374151'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Notable events */}
            {(highEvents.length > 0 || lowEvents.length > 0) && (
              <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-soma-text mb-3">Événements notables</h2>
                <div className="space-y-2">
                  {highEvents.map((evt, i) => (
                    <div
                      key={'high-' + i}
                      className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/8 border border-red-400/20"
                    >
                      <AlertTriangle size={14} className="text-red-400 mt-0.5 shrink-0" />
                      <span className="text-xs text-soma-text">
                        FC repos élevée détectée
                        {typeof evt === 'object' && evt !== null && 'time' in evt
                          ? ' à ' + (evt as Record<string, unknown>).time
                          : ''}
                      </span>
                    </div>
                  ))}
                  {lowEvents.map((evt, i) => (
                    <div
                      key={'low-' + i}
                      className="flex items-start gap-2.5 p-3 rounded-lg bg-blue-500/8 border border-blue-400/20"
                    >
                      <AlertTriangle size={14} className="text-blue-400 mt-0.5 shrink-0" />
                      <span className="text-xs text-soma-text">
                        FC repos basse détectée
                        {typeof evt === 'object' && evt !== null && 'time' in evt
                          ? ' à ' + (evt as Record<string, unknown>).time
                          : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  );
}
