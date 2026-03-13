'use client';

import { useState } from 'react';
import { useEntitlement } from '@/hooks/use-entitlements';
import { FeatureCode } from '@/lib/entitlements';
import PaywallCard from '@/components/PaywallCard';
import {
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Lightbulb,
  Loader2,
  Eye,
  EyeOff,
  RefreshCw,
  Activity,
  Moon,
  Utensils,
  Dumbbell,
  Droplets,
  Heart,
} from 'lucide-react';
import { useInsights, useMarkInsightRead, useDismissInsight } from '@/hooks/use-insights';
import { runInsights } from '@/lib/api/insights';
import { useTranslations } from '@/lib/i18n/config';
import { cn, safeDateFormat } from '@/lib/utils';
import { useQueryClient } from '@tanstack/react-query';
import type { HealthInsight } from '@/lib/types/api';

// -- Constants ----------------------------------------------------------------

type Severity = 'all' | 'critical' | 'warning' | 'info';
type Category = 'all' | 'sleep' | 'nutrition' | 'training' | 'hydration' | 'recovery';

const SEVERITIES: Severity[] = ['all', 'critical', 'warning', 'info'];
const CATEGORIES: Category[] = ['all', 'sleep', 'nutrition', 'training', 'hydration', 'recovery'];

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-red-500/15 text-red-400 border-red-500/30',
  warning:  'bg-orange-500/15 text-orange-400 border-orange-500/30',
  info:     'bg-blue-500/15 text-blue-400 border-blue-500/30',
};

function SeverityIcon({ severity }: { severity: string }) {
  if (severity === 'critical') return <XCircle size={13} />;
  if (severity === 'warning') return <AlertTriangle size={13} />;
  return <Info size={13} />;
}

function CategoryIcon({ category }: { category: string }) {
  switch (category) {
    case 'sleep':     return <Moon size={15} />;
    case 'nutrition': return <Utensils size={15} />;
    case 'training':  return <Dumbbell size={15} />;
    case 'hydration': return <Droplets size={15} />;
    case 'recovery':  return <Heart size={15} />;
    default:          return <Activity size={15} />;
  }
}

// -- Skeleton loader ----------------------------------------------------------

function SkeletonCard() {
  return (
    <div className="card-surface rounded-xl p-4 space-y-3 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="h-5 w-16 rounded-md bg-soma-bg" />
        <div className="h-5 w-5 rounded-full bg-soma-bg" />
        <div className="h-4 w-48 rounded bg-soma-bg" />
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded bg-soma-bg" />
        <div className="h-3 w-3/4 rounded bg-soma-bg" />
      </div>
      <div className="flex items-center justify-between">
        <div className="h-3 w-20 rounded bg-soma-bg" />
        <div className="flex gap-2">
          <div className="h-7 w-7 rounded-md bg-soma-bg" />
          <div className="h-7 w-7 rounded-md bg-soma-bg" />
        </div>
      </div>
    </div>
  );
}

// -- Insight Card -------------------------------------------------------------

function InsightCard({
  insight,
  onMarkRead,
  onDismiss,
  t,
}: {
  insight: HealthInsight;
  onMarkRead: (id: string) => void;
  onDismiss: (id: string) => void;
  t: (key: string) => string;
}) {
  const severityCls =
    SEVERITY_STYLES[insight.severity] ?? 'bg-soma-surface text-soma-muted border-soma-border';

  return (
    <div
      className={cn(
        'card-surface rounded-xl p-4 space-y-3 transition-colors',
        !insight.is_read && 'border-l-2 border-l-soma-accent/60'
      )}
    >
      {/* Top row: severity badge + category icon + title */}
      <div className="flex items-start gap-3">
        {/* Severity badge */}
        <span
          className={cn(
            'inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium border shrink-0',
            severityCls
          )}
        >
          <SeverityIcon severity={insight.severity} />
          {insight.severity}
        </span>

        {/* Category icon */}
        <span className="text-soma-muted shrink-0 mt-0.5">
          <CategoryIcon category={insight.category} />
        </span>

        {/* Title */}
        <h3
          className={cn(
            'text-sm font-medium leading-snug flex-1',
            insight.is_read ? 'text-soma-muted' : 'text-soma-text'
          )}
        >
          {insight.title}
        </h3>
      </div>

      {/* Message */}
      <p className="text-xs text-soma-muted leading-relaxed pl-[4.25rem]">
        {insight.message}
      </p>

      {/* Recommendation */}
      {insight.recommendation && (
        <div className="ml-[4.25rem] flex items-start gap-2 rounded-lg bg-soma-bg/60 px-3 py-2">
          <Lightbulb size={13} className="text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[11px] font-medium text-soma-muted uppercase tracking-wide">
              {t('insights.recommendation')}
            </span>
            <p className="text-xs text-soma-text leading-relaxed mt-0.5">
              {insight.recommendation}
            </p>
          </div>
        </div>
      )}

      {/* Footer: date + actions */}
      <div className="flex items-center justify-between pl-[4.25rem]">
        <span className="text-[11px] text-soma-muted">
          {safeDateFormat(insight.created_at, 'd MMM yyyy HH:mm')}
        </span>

        <div className="flex items-center gap-1">
          {!insight.is_read && (
            <button
              onClick={() => onMarkRead(insight.id)}
              title={t('insights.markRead')}
              className="p-1.5 rounded-md text-soma-muted hover:text-soma-accent hover:bg-soma-accent/10 transition-colors"
            >
              <Eye size={14} />
            </button>
          )}
          <button
            onClick={() => onDismiss(insight.id)}
            title={t('insights.dismiss')}
            className="p-1.5 rounded-md text-soma-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <XCircle size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

// -- Filter Pill --------------------------------------------------------------

function FilterPill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border',
        active
          ? 'bg-soma-accent/15 text-soma-accent border-soma-accent/40'
          : 'bg-soma-surface text-soma-muted border-soma-border hover:text-soma-text hover:border-soma-accent/30'
      )}
    >
      {label}
    </button>
  );
}

// -- Main Page ----------------------------------------------------------------

export default function InsightsPage() {
  const canUseInsights = useEntitlement(FeatureCode.ADVANCED_INSIGHTS);
  const t = useTranslations();
  const queryClient = useQueryClient();

  const [severity, setSeverity] = useState<Severity>('all');
  const [category, setCategory] = useState<Category>('all');
  const [isRunning, setIsRunning] = useState(false);

  // Fetch insights with optional filters
  const insightsQuery = useInsights({
    severity: severity === 'all' ? undefined : severity,
    category: category === 'all' ? undefined : category,
  });

  const markRead = useMarkInsightRead();
  const dismiss = useDismissInsight();

  const insights = insightsQuery.data?.insights ?? [];
  const isLoading = insightsQuery.isLoading;

  // -- Handlers ---------------------------------------------------------------

  async function handleRunInsights() {
    setIsRunning(true);
    try {
      await runInsights();
      await queryClient.invalidateQueries({ queryKey: ['insights'] });
    } finally {
      setIsRunning(false);
    }
  }

  function handleMarkRead(id: string) {
    markRead.mutate(id);
  }

  function handleDismiss(id: string) {
    dismiss.mutate(id);
  }

  // -- Label helpers ----------------------------------------------------------

  function severityLabel(s: Severity): string {
    if (s === 'all') return t('insights.all');
    return t(`insights.${s}`);
  }

  function categoryLabel(c: Category): string {
    if (c === 'all') return t('insights.all');
    return t(`insights.${c}`);
  }

  // -- Render -----------------------------------------------------------------

  if (!canUseInsights) {
    return <PaywallCard feature={FeatureCode.ADVANCED_INSIGHTS} />;
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">
              {t('insights.title')}
            </h1>
            <p className="text-sm text-soma-muted">{t('insights.subtitle')}</p>
          </div>
          <button
            onClick={handleRunInsights}
            disabled={isRunning}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium',
              'border border-soma-border bg-soma-surface text-soma-muted',
              'hover:text-soma-text hover:border-soma-accent/50 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <RefreshCw
              size={13}
              className={isRunning ? 'animate-spin' : ''}
            />
            {t('insights.refresh')}
          </button>
        </div>

        {/* Filter bar */}
        <div className="space-y-3">
          {/* Severity filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-medium text-soma-muted uppercase tracking-wide mr-1">
              {t('insights.severity')}
            </span>
            {SEVERITIES.map((s) => (
              <FilterPill
                key={s}
                label={severityLabel(s)}
                active={severity === s}
                onClick={() => setSeverity(s)}
              />
            ))}
          </div>

          {/* Category filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-medium text-soma-muted uppercase tracking-wide mr-1">
              {t('insights.category')}
            </span>
            {CATEGORIES.map((c) => (
              <FilterPill
                key={c}
                label={categoryLabel(c)}
                active={category === c}
                onClick={() => setCategory(c)}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : insights.length === 0 ? (
          <div className="card-surface rounded-xl py-16 flex flex-col items-center gap-3 text-soma-muted">
            <CheckCircle size={36} className="opacity-40" />
            <p className="text-sm">{t('insights.noInsights')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {insights.map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onMarkRead={handleMarkRead}
                onDismiss={handleDismiss}
                t={t}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
