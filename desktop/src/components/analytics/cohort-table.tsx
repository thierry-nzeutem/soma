'use client';

import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { CohortRetentionResponse } from '@/lib/types/api';

interface CohortTableProps {
  data: CohortRetentionResponse[] | undefined;
  isLoading: boolean;
}

function RetentionCell({ value }: { value: number | null | undefined }) {
  if (value == null) return <td className="px-3 py-2 text-soma-muted text-center text-xs">—</td>;

  const color =
    value >= 60
      ? '#34C759'
      : value >= 35
      ? '#FF9500'
      : '#FF3B30';

  const bgOpacity = Math.max(0.05, value / 100) * 0.3;

  return (
    <td
      className="px-3 py-2 text-center text-xs font-semibold tabular-nums"
      style={{
        color,
        backgroundColor: `${color}${Math.round(bgOpacity * 255).toString(16).padStart(2, '0')}`,
      }}
    >
      {value.toFixed(1)}%
    </td>
  );
}

export function CohortTable({ data, isLoading }: CohortTableProps) {
  const t = useTranslations();
  return (
    <div className="card-surface rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-soma-border">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          Rétention Cohortes
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-soma-border">
              <th className="px-3 py-2 text-left text-soma-muted font-medium whitespace-nowrap">
                Cohorte
              </th>
              <th className="px-3 py-2 text-center text-soma-muted font-medium whitespace-nowrap">
                Utilisateurs
              </th>
              <th className="px-3 py-2 text-center text-soma-muted font-medium">J+1</th>
              <th className="px-3 py-2 text-center text-soma-muted font-medium">J+7</th>
              <th className="px-3 py-2 text-center text-soma-muted font-medium">J+30</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-soma-border/50">
                  {[...Array(5)].map((_, j) => (
                    <td key={j} className="px-3 py-2">
                      <div className="h-3 bg-soma-border rounded animate-pulse mx-auto" style={{ width: j === 0 ? '64px' : '40px' }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : !data?.length ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-soma-muted">
                  {t('common.noData')}
                </td>
              </tr>
            ) : (
              data.map((row, i) => (
                <tr
                  key={i}
                  className={cn(
                    'border-b border-soma-border/50 hover:bg-soma-accent/5 transition-colors',
                    i % 2 === 0 ? '' : 'bg-soma-bg/20'
                  )}
                >
                  <td className="px-3 py-2 text-soma-text font-medium whitespace-nowrap">
                    {row.cohort_week}
                  </td>
                  <td className="px-3 py-2 text-soma-muted text-center tabular-nums">
                    {row.users_count?.toLocaleString('fr-FR')}
                  </td>
                  <RetentionCell value={row.retention_day1} />
                  <RetentionCell value={row.retention_day7} />
                  <RetentionCell value={row.retention_day30} />
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
