'use client';

import { Moon, AlertTriangle, Clock, BarChart3 } from 'lucide-react';
import { useSleepAnalysis } from '@/hooks/use-dashboard';
import { useTranslations } from '@/lib/i18n/config';
import type { SleepAnalysisResponse } from '@/lib/types/api';

function scoreColor(score: number): string {
  if (score >= 80) return 'text-soma-success';
  if (score >= 60) return 'text-soma-warning';
  return 'text-[#FF3B30]';
}

function scoreBg(score: number): string {
  if (score >= 80) return 'bg-soma-success/10';
  if (score >= 60) return 'bg-soma-warning/10';
  return 'bg-[#FF3B30]/10';
}

function formatHour(h: number | null): string {
  if (h == null) return '—';
  const hour = Math.floor(h) % 24;
  const min = Math.round((h - Math.floor(h)) * 60);
  return `${hour}h${min.toString().padStart(2, '0')}`;
}

export function SleepCard() {
  const { data, isLoading, error } = useSleepAnalysis(14);
  const t = useTranslations();

  if (isLoading) {
    return (
      <div className="card-surface p-5 animate-pulse">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-5 h-5 rounded bg-soma-surface" />
          <div className="h-4 w-28 rounded bg-soma-surface" />
        </div>
        <div className="space-y-3">
          <div className="h-3 w-full rounded bg-soma-surface" />
          <div className="h-3 w-2/3 rounded bg-soma-surface" />
          <div className="h-3 w-1/2 rounded bg-soma-surface" />
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="card-surface p-5">
        <div className="flex items-center gap-2 mb-3">
          <Moon size={16} className="text-soma-accent" />
          <span className="text-sm font-semibold text-soma-text">{t('dashboard.sleep')}</span>
        </div>
        <p className="text-xs text-soma-muted">
          {t('common.error')}
        </p>
      </div>
    );
  }

  const architecture = data?.architecture ?? null;
  const consistency = data?.consistency ?? null;
  const problems = data?.problems ?? [];
  const hasData = architecture || consistency;

  if (!data || !hasData) {
    return (
      <div className="card-surface p-5">
        <div className="flex items-center gap-2 mb-3">
          <Moon size={16} className="text-soma-accent" />
          <span className="text-sm font-semibold text-soma-text">{t('dashboard.sleep')}</span>
        </div>
        <p className="text-xs text-soma-muted mb-3">
          {t('common.noData')}
        </p>
        <a
          href="/journal"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-soma-accent hover:text-soma-accent/80 transition-colors"
        >
          <Moon size={12} />
          {t('sleep.logTitle')}
        </a>
      </div>
    );
  }

  return (
    <div className="card-surface p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Moon size={16} className="text-soma-accent" />
          <span className="text-sm font-semibold text-soma-text">{t('sleep.title')}</span>
        </div>
        {architecture && (
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${scoreBg(architecture.architecture_score)} ${scoreColor(architecture.architecture_score)}`}>
            {architecture.architecture_score}{t('common.score')}
          </span>
        )}
      </div>

      {/* Architecture breakdown */}
      {architecture && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs text-soma-muted">
            <BarChart3 size={12} />
            <span>{t('sleep.architecture')}</span>
          </div>
          {/* Mini bar */}
          <div className="flex h-2.5 rounded-full overflow-hidden">
            {architecture.deep_pct > 0 && (
              <div className="bg-indigo-500" style={{ width: `${architecture.deep_pct}%` }} title={`${t('sleep.deep')} ${architecture.deep_pct.toFixed(0)}%`} />
            )}
            {architecture.rem_pct > 0 && (
              <div className="bg-violet-500" style={{ width: `${architecture.rem_pct}%` }} title={`${t('sleep.rem')} ${architecture.rem_pct.toFixed(0)}%`} />
            )}
            {architecture.light_pct > 0 && (
              <div className="bg-soma-accent" style={{ width: `${architecture.light_pct}%` }} title={`${t('sleep.light')} ${architecture.light_pct.toFixed(0)}%`} />
            )}
            {architecture.awake_pct > 0 && (
              <div className="bg-soma-warning" style={{ width: `${architecture.awake_pct}%` }} title={`${t('sleep.awake')} ${architecture.awake_pct.toFixed(0)}%`} />
            )}
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px]">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-500" />{t('sleep.deep')} {architecture.deep_pct.toFixed(0)}%</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-violet-500" />{t('sleep.rem')} {architecture.rem_pct.toFixed(0)}%</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-soma-accent" />{t('sleep.light')} {architecture.light_pct.toFixed(0)}%</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-soma-warning" />{t('sleep.awake')} {architecture.awake_pct.toFixed(0)}%</span>
          </div>
        </div>
      )}

      {/* Consistency */}
      {consistency && consistency.consistency_label !== 'insufficient_data' && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs text-soma-muted">
            <Clock size={12} />
            <span>{t('sleep.consistency')}</span>
            <span className={`ml-auto text-xs font-semibold ${scoreColor(consistency.consistency_score)}`}>
              {consistency.consistency_score}{t('common.score')}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-soma-bg rounded-lg px-3 py-2 border border-soma-border">
              <div className="text-[10px] text-soma-muted">{t('sleep.avgBedtime')}</div>
              <div className="text-sm font-semibold text-soma-text">{formatHour(consistency.avg_bedtime_hour)}</div>
            </div>
            <div className="bg-soma-bg rounded-lg px-3 py-2 border border-soma-border">
              <div className="text-[10px] text-soma-muted">{t('sleep.avgWake')}</div>
              <div className="text-sm font-semibold text-soma-text">{formatHour(consistency.avg_wake_hour)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Problems */}
      {problems.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs text-soma-warning">
            <AlertTriangle size={12} />
            <span>{t('sleep.problems')}</span>
          </div>
          {problems.slice(0, 2).map((p, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className={`shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full ${
                p.severity === 'high' ? 'bg-[#FF3B30]' : p.severity === 'moderate' ? 'bg-soma-warning' : 'bg-soma-info'
              }`} />
              <span className="text-soma-text-secondary">{p.problem_type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
