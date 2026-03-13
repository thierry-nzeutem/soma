'use client';

import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { Activity, Footprints, Flame, MapPin, Loader2 } from 'lucide-react';
import { useActivityDay, useActivityPeriod } from '@/hooks/use-health-analytics';
import { useTranslations } from '@/lib/i18n/config';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  className?: string;
}

function StatCard({ label, value, unit, icon, className }: StatCardProps) {
  return (
    <div className={cn('card-surface flex flex-col gap-1.5 p-4', className)}>
      <div className="flex items-center gap-2 text-soma-muted">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-soma-text">{value}</span>
        {unit && <span className="text-xs text-soma-muted">{unit}</span>}
      </div>
    </div>
  );
}

function HourlyTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string | number;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-soma-muted">{label}h</p>
      <p className="font-semibold text-soma-text">{payload[0].value} pas</p>
    </div>
  );
}

type Period = 'week' | 'month';

interface PeriodToggleProps {
  value: Period;
  onChange: (p: Period) => void;
}

function PeriodToggle({ value, onChange }: PeriodToggleProps) {
  return (
    <div className="flex rounded-lg overflow-hidden border border-soma-border">
      {(['week', 'month'] as Period[]).map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={cn(
            'px-3 py-1.5 text-xs font-medium transition-colors',
            value === p
              ? 'bg-soma-accent text-white'
              : 'bg-soma-surface text-soma-muted hover:text-soma-text'
          )}
        >
          {p === 'week' ? 'Semaine' : 'Mois'}
        </button>
      ))}
    </div>
  );
}

export default function ActivityPage() {
  const tCommon = useTranslations('common');
  const [period, setPeriod] = useState<Period>('week');

  const day = useActivityDay();
  const periodData = useActivityPeriod(period);

  const totalSteps = day.data?.total_steps ?? null;
  const distanceKm = day.data?.distance_km ?? null;
  const activeCal = day.data?.active_calories_kcal ?? null;
  const totalCal = day.data?.total_calories_kcal ?? null;
  const hourlySteps: Array<{ hour: number; steps: number }> =
    day.data?.hourly_steps ?? [];

  const chartData = Array.from({ length: 24 }, (_, h) => {
    const found = hourlySteps.find((p) => p.hour === h);
    return { hour: h, steps: found?.steps ?? 0 };
  });

  const periodSteps = periodData.data?.total_steps ?? null;
  const avgDaily = periodData.data?.avg_daily_steps ?? null;
  const periodDist = periodData.data?.total_distance_km ?? null;
  const goalDays = periodData.data?.goal_days_count ?? null;

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">

        <div className="flex items-center gap-3">
          <Activity size={20} className="text-emerald-400 shrink-0" />
          <div>
            <h1 className="text-lg font-semibold text-soma-text">Activité</h1>
            <p className="text-sm text-soma-muted">Pas &amp; dépense calorique du jour</p>
          </div>
        </div>

        {day.isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : day.isError ? (
          <p className="text-sm text-soma-danger">{tCommon('error')}</p>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard
                label="Total pas"
                value={totalSteps != null ? totalSteps.toFixed(0) : '—'}
                icon={<Footprints size={14} className="text-emerald-400" />}
              />
              <StatCard
                label="Distance"
                value={distanceKm != null ? distanceKm.toFixed(1) : '—'}
                unit="km"
                icon={<MapPin size={14} className="text-blue-400" />}
              />
              <StatCard
                label="Cal. actives"
                value={activeCal != null ? activeCal.toFixed(0) : '—'}
                unit="kcal"
                icon={<Flame size={14} className="text-orange-400" />}
              />
              <StatCard
                label="Cal. totales"
                value={totalCal != null ? totalCal.toFixed(0) : '—'}
                unit="kcal"
                icon={<Flame size={14} className="text-red-400" />}
              />
            </div>

            <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-soma-text mb-4">Pas par heure</h2>
              {hourlySteps.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 gap-2">
                  <Footprints size={28} className="text-soma-muted/40" />
                  <p className="text-sm text-soma-muted">{tCommon('noData')}</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="hour"
                      tick={{ fontSize: 10, fill: 'var(--soma-muted, #888)' }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(h: number) => (h % 6 === 0 ? String(h) + 'h' : '')}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: 'var(--soma-muted, #888)' }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip content={<HourlyTooltip />} cursor={false} />
                    <Bar dataKey="steps" radius={[3, 3, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={'cell-' + index}
                          fill={
                            entry.steps > 1000
                              ? '#34d399'
                              : entry.steps > 0
                              ? '#6ee7b7'
                              : '#374151'
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </>
        )}

        <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-soma-text">Résumé de la période</h2>
            <PeriodToggle value={period} onChange={setPeriod} />
          </div>
          {periodData.isLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 size={20} className="animate-spin text-soma-muted" />
            </div>
          ) : periodData.isError ? (
            <p className="text-sm text-soma-danger">{tCommon('error')}</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-soma-muted">Total pas</span>
                <span className="text-xl font-bold text-soma-text">
                  {periodSteps != null ? Number(periodSteps).toLocaleString('fr-FR') : '—'}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-soma-muted">Moy. journalière</span>
                <span className="text-xl font-bold text-soma-text">
                  {avgDaily != null ? Number(avgDaily).toLocaleString('fr-FR') : '—'}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-soma-muted">Distance totale</span>
                <span className="text-xl font-bold text-soma-text">
                  {periodDist != null ? Number(periodDist).toFixed(1) + ' km' : '—'}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-soma-muted">Jours objectif atteint</span>
                <span className="text-xl font-bold text-soma-text">
                  {goalDays != null ? goalDays : '—'}
                </span>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
