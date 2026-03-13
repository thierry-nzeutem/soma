'use client';

import { AlertTriangle, CheckCircle2, Info, TrendingUp, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { HomeSummaryResponse } from '@/lib/types/api';

interface AlertsPanelProps {
  data: HomeSummaryResponse | undefined;
  isLoading: boolean;
}

type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info' | 'success';

function AlertCard({
  title,
  message,
  severity,
}: {
  title: string;
  message?: string;
  severity: AlertSeverity;
}) {
  const config: Record<
    AlertSeverity,
    { icon: React.ElementType; iconClass: string; borderClass: string; bgClass: string }
  > = {
    critical: {
      icon: AlertTriangle,
      iconClass: 'text-soma-danger',
      borderClass: 'border-soma-danger/30',
      bgClass: 'bg-soma-danger/5',
    },
    high: {
      icon: AlertTriangle,
      iconClass: 'text-soma-warning',
      borderClass: 'border-soma-warning/30',
      bgClass: 'bg-soma-warning/5',
    },
    medium: {
      icon: Info,
      iconClass: 'text-soma-warning',
      borderClass: 'border-soma-warning/20',
      bgClass: 'bg-soma-warning/5',
    },
    low: {
      icon: Info,
      iconClass: 'text-soma-muted',
      borderClass: 'border-soma-border',
      bgClass: '',
    },
    info: {
      icon: Info,
      iconClass: 'text-soma-muted',
      borderClass: 'border-soma-border',
      bgClass: '',
    },
    success: {
      icon: CheckCircle2,
      iconClass: 'text-soma-success',
      borderClass: 'border-soma-success/30',
      bgClass: 'bg-soma-success/5',
    },
  };

  const { icon: Icon, iconClass, borderClass, bgClass } = config[severity];

  return (
    <div
      className={cn(
        'rounded-lg border p-3 flex items-start gap-2.5',
        borderClass,
        bgClass
      )}
    >
      <Icon size={14} className={cn('shrink-0 mt-0.5', iconClass)} />
      <div className="min-w-0">
        <p className="text-xs font-semibold text-soma-text">{title}</p>
        {message && (
          <p className="text-xs text-soma-muted mt-0.5 leading-snug">{message}</p>
        )}
      </div>
    </div>
  );
}

function InsightCard({
  title,
  message,
  category,
}: {
  title: string;
  message?: string;
  category?: string;
}) {
  return (
    <div className="rounded-lg border border-soma-border p-3 flex items-start gap-2.5">
      <Sparkles size={14} className="text-soma-accent shrink-0 mt-0.5" />
      <div className="min-w-0">
        {category && (
          <span className="text-[10px] text-soma-accent uppercase tracking-wider font-semibold">
            {category}
          </span>
        )}
        <p className="text-xs font-semibold text-soma-text">{title}</p>
        {message && (
          <p className="text-xs text-soma-muted mt-0.5 leading-snug line-clamp-2">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

export function AlertsPanel({ data, isLoading }: AlertsPanelProps) {
  if (isLoading) {
    return (
      <div className="card-surface rounded-xl p-5 flex flex-col gap-3">
        <div className="h-5 w-36 bg-soma-border rounded animate-pulse" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-14 bg-soma-border rounded animate-pulse" />
        ))}
      </div>
    );
  }

  // Support both flat fields and nested plan.alerts
  const alerts: any[] = data?.alerts ?? data?.plan?.alerts ?? [];
  const insights: any[] = data?.recent_insights ?? data?.unread_insights ?? [];

  const hasContent = alerts.length > 0 || insights.length > 0;

  return (
    <div className="card-surface rounded-xl p-5 flex flex-col gap-3 overflow-y-auto">
      <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted shrink-0">
        Alertes & Insights
      </p>

      {!hasContent ? (
        <div className="flex flex-col items-center justify-center py-6 gap-2">
          <CheckCircle2 size={24} className="text-soma-success" />
          <p className="text-xs text-soma-muted text-center">
            Tout est optimal — aucune alerte active
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {/* Alerts first */}
          {alerts.map((alert: any, i: number) => {
            const severity: AlertSeverity =
              alert.severity === 'critical'
                ? 'critical'
                : alert.severity === 'high'
                ? 'high'
                : alert.severity === 'medium'
                ? 'medium'
                : 'low';

            return (
              <AlertCard
                key={i}
                title={alert.title || alert.message || 'Alerte'}
                message={alert.description || alert.details}
                severity={severity}
              />
            );
          })}

          {/* Insights */}
          {insights.map((insight: any, i: number) => (
            <InsightCard
              key={`ins-${i}`}
              title={
                typeof insight === 'string'
                  ? insight
                  : insight.title || insight.message || 'Insight'
              }
              message={
                typeof insight === 'object' ? insight.description || insight.details : undefined
              }
              category={
                typeof insight === 'object' ? insight.category : undefined
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
