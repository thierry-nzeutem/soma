'use client';

import { Users, TrendingUp, Activity, Percent } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { AnalyticsSummaryResponse } from '@/lib/types/api';

interface KpiGridProps {
  data: AnalyticsSummaryResponse | undefined;
  isLoading: boolean;
}

function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  accent,
  isLoading,
}: {
  label: string;
  value: string | number | null | undefined;
  sub?: string;
  icon: React.ElementType;
  accent?: string;
  isLoading?: boolean;
}) {
  return (
    <div className="card-surface rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-soma-muted">
          {label}
        </span>
        <Icon size={14} className="text-soma-muted" />
      </div>
      {isLoading ? (
        <div className="space-y-1.5">
          <div className="h-7 w-20 bg-soma-border rounded animate-pulse" />
          <div className="h-3 w-16 bg-soma-border rounded animate-pulse" />
        </div>
      ) : (
        <>
          <p
            className="text-2xl font-bold tabular-nums"
            style={{ color: accent || 'var(--soma-text)' }}
          >
            {value ?? '—'}
          </p>
          {sub && <p className="text-xs text-soma-muted mt-1">{sub}</p>}
        </>
      )}
    </div>
  );
}

export function KpiGrid({ data, isLoading }: KpiGridProps) {
  const t = useTranslations();
  const stickiness =
    data?.dau != null && data?.mau != null && data.mau > 0
      ? ((data.dau / data.mau) * 100).toFixed(1)
      : null;

  return (
    <div className="grid grid-cols-4 gap-4">
      <KpiCard
        label="DAU"
        value={data?.dau?.toLocaleString('fr-FR')}
        sub={t('analytics.dauSub')}
        icon={Activity}
        accent="#00E5A0"
        isLoading={isLoading}
      />
      <KpiCard
        label="WAU"
        value={data?.wau?.toLocaleString('fr-FR')}
        sub={t('analytics.wauSub')}
        icon={Users}
        isLoading={isLoading}
      />
      <KpiCard
        label="MAU"
        value={data?.mau?.toLocaleString('fr-FR')}
        sub={t('analytics.mauSub')}
        icon={Users}
        isLoading={isLoading}
      />
      <KpiCard
        label="Stickiness"
        value={stickiness != null ? `${stickiness}%` : null}
        sub={(() => {
          const ob = data?.onboarding_rate ?? data?.onboarding_completion_rate;
          return `DAU/MAU ratio${ob != null ? ` · Onboarding: ${(ob * 100 > 1 ? ob : ob * 100).toFixed(1)}%` : ''}`;
        })()}
        icon={TrendingUp}
        accent={
          stickiness != null
            ? Number(stickiness) >= 10
              ? '#34C759'
              : Number(stickiness) >= 5
              ? '#FF9500'
              : '#FF3B30'
            : undefined
        }
        isLoading={isLoading}
      />
    </div>
  );
}
