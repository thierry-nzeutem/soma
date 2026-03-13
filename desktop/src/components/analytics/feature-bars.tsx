'use client';

import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { FeatureUsageResponse, FeatureEventCount } from '@/lib/types/api';

interface FeatureBarsProps {
  data: FeatureUsageResponse | undefined;
  isLoading: boolean;
}

const FEATURE_COLORS: Record<string, string> = {
  morning_briefing: '#00E5A0',
  daily_briefing: '#00E5A0',
  journal: '#FF9500',
  coach: '#AF52DE',
  coach_question: '#AF52DE',
  longevity: '#32ADE6',
  nutrition: '#FF6B6B',
  workout: '#FFD60A',
  hydration: '#32ADE6',
  sleep: '#6E6AE8',
  vision: '#FF9F0A',
  analytics: '#BEC2C8',
};

function getFeatureColor(name: string): string {
  const lower = name.toLowerCase().replace(/[\s-]/g, '_');
  for (const [key, color] of Object.entries(FEATURE_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return '#888888';
}

function formatFeatureName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function FeatureBars({ data, isLoading }: FeatureBarsProps) {
  const t = useTranslations();
  // Support both array format (features[]) and flat format
  const features = data?.features ?? (data
    ? Object.entries({
        briefing_views: data.briefing_views,
        journal_entries: data.journal_entries,
        coach_questions: data.coach_questions,
        twin_views: data.twin_views,
        nutrition_logs: data.nutrition_logs,
        workout_logs: data.workout_logs,
        quick_advice_requests: data.quick_advice_requests,
      })
        .filter(([, v]) => v != null && v > 0)
        .map(([k, v]): FeatureEventCount => ({ feature_name: k, event_count: v as number }))
    : []);
  const maxCount = Math.max(...features.map((f) => f.event_count ?? 0), 1);

  return (
    <div className="card-surface rounded-xl p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-3">
        Usage des Features
      </p>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="space-y-1">
              <div className="h-3 w-24 bg-soma-border rounded animate-pulse" />
              <div className="h-4 bg-soma-border rounded animate-pulse" style={{ width: `${60 - i * 8}%` }} />
            </div>
          ))}
        </div>
      ) : features.length === 0 ? (
        <p className="text-xs text-soma-muted py-4 text-center">{t('common.noData')}</p>
      ) : (
        <div className="space-y-2.5">
          {features.map((feature) => {
            const ratio = (feature.event_count ?? 0) / maxCount;
            const color = getFeatureColor(feature.feature_name);
            return (
              <div key={feature.feature_name}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-soma-text">
                    {formatFeatureName(feature.feature_name)}
                  </span>
                  <span className="text-xs font-semibold tabular-nums" style={{ color }}>
                    {feature.event_count?.toLocaleString('fr-FR')}
                  </span>
                </div>
                <div className="h-2 bg-soma-bg rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.max(ratio * 100, 2)}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>
                {feature.unique_users != null && (
                  <p className="text-[10px] text-soma-muted mt-0.5">
                    {feature.unique_users.toLocaleString('fr-FR')} utilisateurs uniques
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
