'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { OnboardingFunnelResponse } from '@/lib/types/api';

interface FunnelChartProps {
  data: OnboardingFunnelResponse | undefined;
  isLoading: boolean;
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg p-3 shadow-xl text-xs">
      <p className="font-semibold text-soma-text mb-1">{d.step_name}</p>
      <p className="text-soma-muted">
        Utilisateurs : <span className="font-semibold text-soma-text">{d.users_count?.toLocaleString('fr-FR')}</span>
      </p>
      <p className="text-soma-muted">
        Conversion : <span className="font-semibold text-soma-accent">{d.conversion_from_previous}%</span>
      </p>
      {d.drop_off_rate > 0 && (
        <p className="text-soma-muted">
          Drop-off : <span className="font-semibold text-soma-danger">{d.drop_off_rate}%</span>
        </p>
      )}
    </div>
  );
};

export function FunnelChart({ data, isLoading }: FunnelChartProps) {
  const t = useTranslations();
  const steps = data?.steps ?? [];
  const maxCount = Math.max(...steps.map((s) => s.users_count ?? 0), 1);

  return (
    <div className="card-surface rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          Funnel Onboarding
        </p>
        {data?.overall_conversion_rate != null && (
          <span
            className={cn(
              'text-xs font-bold',
              data.overall_conversion_rate >= 30
                ? 'text-soma-success'
                : data.overall_conversion_rate >= 15
                ? 'text-soma-warning'
                : 'text-soma-danger'
            )}
          >
            {data.overall_conversion_rate}% global
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="h-40 bg-soma-border rounded animate-pulse" />
      ) : steps.length === 0 ? (
        <div className="h-40 flex items-center justify-center">
          <p className="text-xs text-soma-muted">{t('common.noData')}</p>
        </div>
      ) : (
        <div style={{ height: '180px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={steps}
              layout="vertical"
              margin={{ top: 0, right: 8, left: 8, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--soma-border)" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: 'var(--soma-muted)', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                dataKey="step_name"
                type="category"
                width={110}
                tick={{ fill: 'var(--soma-muted)', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="users_count" radius={[0, 4, 4, 0]} maxBarSize={22}>
                {steps.map((step, i) => {
                  const ratio = (step.users_count ?? 0) / maxCount;
                  const r = Math.round(0 + (255 - 0) * (1 - ratio)).toString(16).padStart(2, '0');
                  const g = Math.round(229 + (100 - 229) * (1 - ratio)).toString(16).padStart(2, '0');
                  const color = ratio > 0.5 ? '#00E5A0' : ratio > 0.25 ? '#FF9500' : '#FF3B30';
                  return <Cell key={i} fill={color} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
