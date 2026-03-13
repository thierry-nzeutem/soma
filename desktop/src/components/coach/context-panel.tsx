'use client';

import { Activity, Moon, Zap, Scale, Heart, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import { useHomeSummary } from '@/hooks/use-dashboard';

interface StatRowProps {
  icon: React.ElementType;
  label: string;
  value: string | number | null | undefined;
  color?: string;
}

function StatRow({ icon: Icon, label, value, color }: StatRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-soma-border last:border-0">
      <div className="flex items-center gap-2">
        <Icon size={12} className="text-soma-muted shrink-0" />
        <span className="text-xs text-soma-muted">{label}</span>
      </div>
      <span
        className="text-xs font-semibold tabular-nums"
        style={{ color: color || 'var(--soma-text)' }}
      >
        {value ?? '—'}
      </span>
    </div>
  );
}

export function ContextPanel() {
  const t = useTranslations();
  const summary = useHomeSummary();
  const data = summary.data;

  // Support nested and flat structures
  const readiness = data?.readiness_score ?? data?.readiness?.overall_readiness ?? 0;
  const longevity = data?.longevity_score ?? data?.longevity?.longevity_score ?? 0;
  const weight = data?.current_weight_kg ?? data?.metrics?.weight_kg;
  const bmi = data?.bmi;

  const readinessColor =
    readiness >= 80 ? '#34C759' : readiness >= 60 ? '#FF9500' : '#FF3B30';

  const longevityColor =
    longevity >= 75 ? '#34C759' : longevity >= 55 ? '#FF9500' : '#FF3B30';

  const alerts: any[] = data?.alerts ?? data?.plan?.alerts ?? [];

  return (
    <div className="flex flex-col h-full bg-soma-surface border-l border-soma-border overflow-y-auto">
      <div className="px-4 py-3 border-b border-soma-border shrink-0">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          {t('coach.healthContext')}
        </p>
        <p className="text-[10px] text-soma-muted mt-0.5">{t('coach.realtimeData')}</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {/* Scores */}
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-soma-muted mb-1.5">
            {t('coach.scores')}
          </p>
          {summary.isLoading ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-7 bg-soma-border rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <div>
              <StatRow
                icon={Activity}
                label={t('dashboard.readiness')}
                value={readiness > 0 ? `${Math.round(readiness)}/100` : null}
                color={readinessColor}
              />
              <StatRow
                icon={Heart}
                label={t('dashboard.longevity')}
                value={longevity > 0 ? `${Math.round(longevity)}/100` : null}
                color={longevityColor}
              />
              <StatRow
                icon={Scale}
                label={t('dashboard.weight')}
                value={weight != null ? `${Number(weight).toFixed(1)} kg` : null}
              />
              <StatRow
                icon={Activity}
                label={t('dashboard.bmi')}
                value={bmi != null ? Number(bmi).toFixed(1) : null}
              />
            </div>
          )}
        </div>

        {/* Twin signals if available */}
        {data?.twin_signals && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-soma-muted mb-1.5">
              {t('coach.digitalTwin')}
            </p>
            <div>
              {Object.entries(data.twin_signals)
                .slice(0, 4)
                .map(([key, val]: [string, any]) => {
                  const label = key
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, (c) => c.toUpperCase());
                  const numVal = typeof val === 'number' ? val : typeof val === 'object' ? val?.value : null;
                  return (
                    <StatRow
                      key={key}
                      icon={Zap}
                      label={label}
                      value={numVal != null ? Math.round(numVal) : String(val)}
                    />
                  );
                })}
            </div>
          </div>
        )}

        {/* Active alerts */}
        {alerts.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-soma-muted mb-1.5">
              {t('coach.activeAlerts')}
            </p>
            <div className="space-y-1.5">
              {alerts.slice(0, 3).map((alert: any, i: number) => {
                const isHigh =
                  alert.severity === 'critical' || alert.severity === 'high';
                return (
                  <div
                    key={i}
                    className={cn(
                      'flex items-start gap-1.5 px-2 py-1.5 rounded-lg text-[10px]',
                      isHigh
                        ? 'bg-soma-warning/10 text-soma-warning'
                        : 'bg-soma-bg text-soma-muted'
                    )}
                  >
                    <AlertCircle size={10} className="shrink-0 mt-0.5" />
                    <span className="leading-snug">
                      {alert.title || alert.message || String(alert)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tip */}
        <div className="rounded-lg bg-soma-bg border border-soma-border p-3">
          <p className="text-[10px] font-semibold text-soma-accent mb-1 uppercase tracking-wide">
            {t('coach.tip')}
          </p>
          <p className="text-[10px] text-soma-muted leading-relaxed">
            {t('coach.tipText')}
          </p>
        </div>
      </div>
    </div>
  );
}
