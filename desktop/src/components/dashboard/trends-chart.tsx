'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { DailyMetricsRecord } from '@/lib/types/api';
import { safeDateFormat } from '@/lib/utils';

interface TrendsChartProps {
  data: DailyMetricsRecord[] | undefined;
  isLoading: boolean;
}

const LINES = [
  {
    key: 'weight_kg',
    label: 'Poids (kg)',
    color: '#00E5A0',
    yAxisId: 'weight',
  },
  {
    key: 'calories_consumed',
    label: 'Calories',
    color: '#FF9500',
    yAxisId: 'calories',
  },
  {
    key: 'protein_g',
    label: 'Protéines (g)',
    color: '#AF52DE',
    yAxisId: 'protein',
  },
] as const;

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: any[];
  label?: string;
}) => {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg p-3 shadow-xl text-xs">
      <p className="text-soma-muted mb-2 font-medium">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center gap-2 mb-1">
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-soma-text">
            {entry.name}:{' '}
            <span className="font-semibold" style={{ color: entry.color }}>
              {entry.value != null ? Number(entry.value).toFixed(1) : '—'}
            </span>
          </span>
        </div>
      ))}
    </div>
  );
};

export function TrendsChart({ data, isLoading }: TrendsChartProps) {
  if (isLoading) {
    return (
      <div className="card-surface rounded-xl p-5 h-full flex flex-col gap-3">
        <div className="h-5 w-40 bg-soma-border rounded animate-pulse" />
        <div className="flex-1 bg-soma-border rounded animate-pulse" />
      </div>
    );
  }

  // Build chart data from metrics records
  const chartData = (Array.isArray(data) ? data : [])
    .slice(-7) // last 7 days
    .map((d) => ({
      date: safeDateFormat(d.date, 'd MMM', ''),
      weight_kg: d.weight_kg,
      calories_consumed: d.calories_consumed,
      protein_g: d.protein_g,
    }));

  const isEmpty = chartData.length === 0;

  return (
    <div className="card-surface rounded-xl p-5 h-full flex flex-col">
      <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-4 shrink-0">
        Tendances 7 Jours
      </p>

      {isEmpty ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-soma-muted">
            Pas assez de données pour afficher les tendances.
          </p>
        </div>
      ) : (
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 4, right: 8, left: -16, bottom: 0 }}
            >
              <defs>
                {LINES.map((line) => (
                  <linearGradient
                    key={line.key}
                    id={`gradient-${line.key}`}
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor={line.color} stopOpacity={0.2} />
                    <stop offset="95%" stopColor={line.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--soma-border)"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--soma-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                yAxisId="weight"
                orientation="left"
                tick={{ fill: 'var(--soma-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                domain={['auto', 'auto']}
              />
              <YAxis
                yAxisId="calories"
                orientation="right"
                tick={{ fill: 'var(--soma-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                hide
              />
              <YAxis yAxisId="protein" hide />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
                iconType="circle"
                iconSize={8}
              />
              {LINES.map((line) => (
                <Area
                  key={line.key}
                  type="monotone"
                  dataKey={line.key}
                  name={line.label}
                  yAxisId={line.yAxisId}
                  stroke={line.color}
                  strokeWidth={2}
                  fill={`url(#gradient-${line.key})`}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 0 }}
                  connectNulls
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
