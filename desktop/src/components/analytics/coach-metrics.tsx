'use client';

import { MessageSquare, Zap, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { CoachAnalyticsResponse } from '@/lib/types/api';

interface CoachMetricsProps {
  data: CoachAnalyticsResponse | undefined;
  isLoading: boolean;
}

function MetricRow({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | null | undefined;
  color?: string;
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-soma-border last:border-0">
      <div className="flex items-center gap-2">
        <Icon size={13} className="text-soma-muted shrink-0" />
        <span className="text-xs text-soma-muted">{label}</span>
      </div>
      <span
        className="text-sm font-bold tabular-nums"
        style={{ color: color || 'var(--soma-text)' }}
      >
        {value ?? '—'}
      </span>
    </div>
  );
}

export function CoachMetrics({ data, isLoading }: CoachMetricsProps) {
  const t = useTranslations();
  return (
    <div className="card-surface rounded-xl p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-2">
        {t('analytics.coachTitle')}
      </p>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-8 bg-soma-border rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <div>
          <MetricRow
            icon={MessageSquare}
            label={t('analytics.totalQuestions')}
            value={data?.total_questions?.toLocaleString('fr-FR')}
            color="#00E5A0"
          />
          <MetricRow
            icon={Zap}
            label={t('analytics.quickAdvice')}
            value={(data?.quick_advice_count ?? data?.total_quick_advice)?.toLocaleString('fr-FR')}
          />
          <MetricRow
            icon={TrendingUp}
            label={t('analytics.followUpRate')}
            value={
              data?.follow_up_rate != null
                ? `${(data.follow_up_rate * 100).toFixed(1)}%`
                : null
            }
            color={
              data?.follow_up_rate != null
                ? data.follow_up_rate >= 0.5
                  ? '#34C759'
                  : data.follow_up_rate >= 0.3
                  ? '#FF9500'
                  : '#FF3B30'
                : undefined
            }
          />
          <MetricRow
            icon={Users}
            label={t('analytics.questionsPerUser')}
            value={
              (data?.avg_questions_per_user ?? data?.questions_per_active_user) != null
                ? Number(data?.avg_questions_per_user ?? data?.questions_per_active_user).toFixed(2)
                : null
            }
          />
        </div>
      )}
    </div>
  );
}
