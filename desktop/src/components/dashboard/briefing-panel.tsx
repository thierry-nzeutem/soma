'use client';

import { Activity, Moon, Zap, Brain, Lightbulb, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { DailyBriefingResponse } from '@/lib/types/api';
import { useTranslations } from '@/lib/i18n/config';

interface BriefingPanelProps {
  data: DailyBriefingResponse | undefined;
  isLoading: boolean;
}

function BriefingRow({
  icon: Icon,
  label,
  value,
  valueColor,
  subValue,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | null | undefined;
  valueColor?: string;
  subValue?: string;
}) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-soma-border last:border-0">
      <div className="w-7 h-7 rounded-lg bg-soma-bg flex items-center justify-center shrink-0 mt-0.5">
        <Icon size={14} className="text-soma-accent" />
      </div>
      <div className="flex-1 min-w-0">
        <span className="text-xs text-soma-muted block">{label}</span>
        <span
          className="text-sm font-semibold"
          style={{ color: valueColor || 'var(--soma-text)' }}
        >
          {value ?? '—'}
        </span>
        {subValue && (
          <span className="text-xs text-soma-muted block">{subValue}</span>
        )}
      </div>
    </div>
  );
}

function AlertItem({
  type,
  message,
}: {
  type: 'warning' | 'success' | 'info';
  message: string;
}) {
  const iconMap = { warning: AlertCircle, success: CheckCircle, info: Info };
  const colorMap = {
    warning: 'text-soma-warning',
    success: 'text-soma-success',
    info: 'text-soma-muted',
  };
  const Icon = iconMap[type];
  return (
    <div className="flex items-start gap-2 py-1.5">
      <Icon size={14} className={cn('shrink-0 mt-0.5', colorMap[type])} />
      <span className="text-xs text-soma-text leading-snug">{message}</span>
    </div>
  );
}

export function BriefingPanel({ data, isLoading }: BriefingPanelProps) {
  const t = useTranslations();

  if (isLoading) {
    return (
      <div className="card-surface rounded-xl p-5 flex flex-col gap-4">
        <div className="h-5 w-40 bg-soma-border rounded animate-pulse" />
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-10 bg-soma-border rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card-surface rounded-xl p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-2">
          {t('briefing.title')}
        </p>
        <p className="text-sm text-soma-muted">{t('common.noData')}</p>
      </div>
    );
  }

  const readinessColor =
    (data.readiness_score ?? 0) >= 80
      ? '#34C759'
      : (data.readiness_score ?? 0) >= 60
      ? '#FF9500'
      : '#FF3B30';

  const fatigueColor =
    (data.fatigue_percentage ?? 0) >= 70
      ? '#FF3B30'
      : (data.fatigue_percentage ?? 0) >= 40
      ? '#FF9500'
      : '#34C759';

  // Backend uses sleep_duration_h, components may receive either form
  const sleepHours = data.sleep_duration_hours ?? data.sleep_duration_h;
  const sleepLabel =
    sleepHours != null ? `${sleepHours.toFixed(1)}h` : null;

  const sleepColor =
    (sleepHours ?? 0) >= 7.5
      ? '#34C759'
      : (sleepHours ?? 0) >= 6
      ? '#FF9500'
      : '#FF3B30';

  const alerts: any[] = data.active_alerts ?? [];
  const insights: any[] = data.insights ?? [];

  return (
    <div className="card-surface rounded-xl p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-3">
        {t('briefing.title')}
      </p>

      <div className="space-y-0">
        <BriefingRow
          icon={Activity}
          label={t('briefing.readiness')}
          value={`${Math.round(data.readiness_score ?? 0)} / 100`}
          valueColor={readinessColor}
          subValue={data.readiness_level ?? undefined}
        />
        <BriefingRow
          icon={Moon}
          label={t('briefing.sleep')}
          value={sleepLabel}
          valueColor={sleepColor}
          subValue={
            data.sleep_quality_score != null
              ? `${t('sleep.quality')} : ${Math.round(data.sleep_quality_score)}/100`
              : undefined
          }
        />
        <BriefingRow
          icon={Zap}
          label={t('briefing.fatigue')}
          value={
            data.fatigue_percentage != null
              ? `${Math.round(data.fatigue_percentage)}%`
              : null
          }
          valueColor={fatigueColor}
        />
        <BriefingRow
          icon={Brain}
          label={t('briefing.energy')}
          value={
            data.available_energy_kcal != null
              ? `${Math.round(data.available_energy_kcal)} kcal`
              : null
          }
        />
      </div>

      {data.coach_tip && (
        <div className="mt-3 rounded-lg bg-soma-bg border border-soma-border p-3">
          <div className="flex items-start gap-2">
            <Lightbulb size={14} className="text-soma-accent shrink-0 mt-0.5" />
            <p className="text-xs text-soma-text leading-relaxed italic">
              "{data.coach_tip}"
            </p>
          </div>
        </div>
      )}

      {(alerts.length > 0 || insights.length > 0) && (
        <div className="mt-3 space-y-0.5">
          {alerts.map((a: any, i: number) => (
            <AlertItem
              key={i}
              type={
                a.severity === 'critical' || a.severity === 'high'
                  ? 'warning'
                  : 'info'
              }
              message={a.message || a.title || String(a)}
            />
          ))}
          {insights.slice(0, 2).map((ins: any, i: number) => (
            <AlertItem
              key={`ins-${i}`}
              type="success"
              message={
                typeof ins === 'string'
                  ? ins
                  : ins.message || ins.title || String(ins)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
