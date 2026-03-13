'use client';

import { Activity, Heart, Scale, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn, scoreColor, fmtPct } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { HomeSummaryResponse } from '@/lib/types/api';

interface HealthKPIsProps {
  data: HomeSummaryResponse | undefined;
  isLoading: boolean;
}

function KPICard({
  label,
  value,
  unit,
  subtitle,
  color,
  icon: Icon,
  isLoading,
  trend,
}: {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  subtitle?: string;
  color?: string;
  icon: React.ElementType;
  isLoading?: boolean;
  trend?: 'up' | 'down' | 'stable' | null;
}) {
  const TrendIcon =
    trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor =
    trend === 'up'
      ? 'text-soma-success'
      : trend === 'down'
      ? 'text-soma-danger'
      : 'text-soma-muted';

  return (
    <div className="card-surface rounded-xl p-5 flex flex-col gap-3 min-w-0">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-soma-muted uppercase tracking-wider">
          {label}
        </span>
        <div
          className={cn(
            'w-8 h-8 rounded-lg flex items-center justify-center',
            'bg-soma-bg'
          )}
        >
          <Icon size={16} className="text-soma-accent" />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <div className="h-8 w-24 bg-soma-border rounded animate-pulse" />
          <div className="h-4 w-32 bg-soma-border rounded animate-pulse" />
        </div>
      ) : (
        <>
          <div className="flex items-baseline gap-1.5">
            <span
              className="text-3xl font-bold tabular-nums"
              style={{ color: color || 'var(--soma-text)' }}
            >
              {value ?? '—'}
            </span>
            {unit && (
              <span className="text-sm text-soma-muted font-medium">{unit}</span>
            )}
            {trend && (
              <TrendIcon size={16} className={cn('ml-auto', trendColor)} />
            )}
          </div>
          {subtitle && (
            <p className="text-sm text-soma-muted leading-snug">{subtitle}</p>
          )}
        </>
      )}
    </div>
  );
}

export function HealthKPIs({ data, isLoading }: HealthKPIsProps) {
  const t = useTranslations();
  // Support both flat fields and nested structure
  const readiness =
    data?.readiness_score ?? data?.readiness?.overall_readiness ?? data?.metrics?.readiness_score;
  const longevity =
    data?.longevity_score ?? data?.longevity?.longevity_score;
  const weight =
    data?.current_weight_kg ?? data?.metrics?.weight_kg;

  // Readiness color
  const readinessColor =
    readiness == null
      ? undefined
      : readiness >= 80
      ? '#34C759'
      : readiness >= 60
      ? '#FF9500'
      : '#FF3B30';

  // Longevity color (similar thresholds)
  const longevityColor =
    longevity == null
      ? undefined
      : longevity >= 75
      ? '#34C759'
      : longevity >= 55
      ? '#FF9500'
      : '#FF3B30';

  const readinessLabel =
    readiness == null
      ? undefined
      : readiness >= 80
      ? t('dashboard.readinessExcellent')
      : readiness >= 60
      ? t('dashboard.readinessGood')
      : t('dashboard.readinessPoor');

  const longevityLabel =
    longevity == null
      ? undefined
      : longevity >= 75
      ? t('dashboard.longevityExcellent')
      : longevity >= 55
      ? t('dashboard.longevityGood')
      : t('dashboard.longevityPoor');

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <KPICard
        label={t('dashboard.readiness')}
        value={readiness != null ? Math.round(readiness) : null}
        unit="/ 100"
        subtitle={readinessLabel}
        color={readinessColor}
        icon={Activity}
        isLoading={isLoading}
      />
      <KPICard
        label={t('dashboard.longevity')}
        value={longevity != null ? Math.round(longevity) : null}
        unit="/ 100"
        subtitle={longevityLabel}
        color={longevityColor}
        icon={Heart}
        isLoading={isLoading}
      />
      <KPICard
        label={t('dashboard.currentWeight')}
        value={weight != null ? weight.toFixed(1) : null}
        unit="kg"
        subtitle={data?.bmi != null ? `IMC : ${data.bmi.toFixed(1)}` : undefined}
        color="var(--soma-text)"
        icon={Scale}
        isLoading={isLoading}
      />
    </div>
  );
}
