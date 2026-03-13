'use client';

import { useState, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  Scale, Plus, Loader2, TrendingUp, TrendingDown, Minus, Ruler, Percent,
} from 'lucide-react';
import { useBodyMetrics, useCreateBodyMetric } from '@/hooks/use-body-metrics';
import type { BodyMetricCreate } from '@/lib/types/api';
import { useTranslations } from '@/lib/i18n/config';
import { cn, safeDateFormat } from '@/lib/utils';

// ─── Constants ───────────────────────────────────────────────────────────────

const PERIODS = [30, 60, 90] as const;

const INITIAL_FORM: BodyMetricCreate = {
  weight_kg: undefined,
  body_fat_pct: undefined,
  muscle_mass_kg: undefined,
  waist_cm: undefined,
};

// ─── Custom Tooltip ──────────────────────────────────────────────────────────

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value?: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const val = payload[0]?.value;
  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="text-soma-muted mb-1">{label}</p>
      <p className="font-semibold text-soma-accent">
        {val != null ? `${Number(val).toFixed(1)} kg` : '\u2014'}
      </p>
    </div>
  );
}

// ─── Trend Arrow ─────────────────────────────────────────────────────────────

function TrendArrow({ delta }: { delta: number | null }) {
  if (delta == null || delta === 0) {
    return <Minus size={14} className="text-soma-muted" />;
  }
  if (delta > 0) {
    return <TrendingUp size={14} className="text-green-400" />;
  }
  return <TrendingDown size={14} className="text-red-400" />;
}

function formatDelta(delta: number | null, decimals = 1): string {
  if (delta == null) return '\u2014';
  const sign = delta > 0 ? '+' : '';
  return `${sign}${delta.toFixed(decimals)}`;
}

// ─── Summary Card ────────────────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  unit,
  delta,
  icon,
  color,
}: {
  label: string;
  value: number | null | undefined;
  unit: string;
  delta: number | null;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="card-surface rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className={color}>{icon}</span>
        <span className="text-xs font-medium text-soma-muted uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="text-xl font-bold text-soma-text">
        {value != null ? value.toFixed(1) : '\u2014'}
        <span className="text-xs font-normal text-soma-muted ml-1">{unit}</span>
      </p>
      <div className="flex items-center gap-1.5 text-xs text-soma-muted">
        <TrendArrow delta={delta} />
        <span>{formatDelta(delta)}</span>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function BodyMetricsPage() {
  const t = useTranslations('body');
  const tc = useTranslations('common');

  const [days, setDays] = useState<number>(30);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<BodyMetricCreate>({ ...INITIAL_FORM });

  const { data, isLoading } = useBodyMetrics(days);
  const createMetric = useCreateBodyMetric();

  const entries = data?.entries ?? [];

  // ── Derived: latest + previous for deltas ───────────────────────────────

  const latest = entries.length > 0 ? entries[entries.length - 1] : null;
  const previous = entries.length > 1 ? entries[entries.length - 2] : null;

  function delta(
    curr: number | null | undefined,
    prev: number | null | undefined,
  ): number | null {
    if (curr == null || prev == null) return null;
    return curr - prev;
  }

  // ── Chart data ──────────────────────────────────────────────────────────

  const chartData = entries.map((e) => ({
    date: safeDateFormat(e.recorded_at, 'd MMM'),
    weight_kg: e.weight_kg ?? null,
  }));

  // ── Form handlers ───────────────────────────────────────────────────────

  const resetForm = useCallback(() => {
    setForm({ ...INITIAL_FORM });
    setShowForm(false);
  }, []);

  const handleFieldChange = useCallback(
    (field: keyof BodyMetricCreate, value: string) => {
      setForm((prev) => ({
        ...prev,
        [field]: value === '' ? undefined : Number(value),
      }));
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await createMetric.mutateAsync(form);
      resetForm();
    },
    [form, createMetric, resetForm],
  );

  // ── BMI helper ──────────────────────────────────────────────────────────

  function formatBmi(bmi: number | null | undefined): string {
    if (bmi == null) return '\u2014';
    return bmi.toFixed(1);
  }

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">
              {t('title')}
            </h1>
            <p className="text-sm text-soma-muted">{t('subtitle')}</p>
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-soma-accent text-white hover:bg-soma-accent/90 transition-colors"
          >
            <Plus size={13} />
            {t('addMeasurement')}
          </button>
        </div>

        {/* Loading */}
        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <MetricCard
                label={t('weight')}
                value={latest?.weight_kg}
                unit="kg"
                delta={delta(latest?.weight_kg, previous?.weight_kg)}
                icon={<Scale size={15} />}
                color="text-emerald-400"
              />
              <MetricCard
                label={t('bodyFat')}
                value={latest?.body_fat_pct}
                unit="%"
                delta={delta(latest?.body_fat_pct, previous?.body_fat_pct)}
                icon={<Percent size={15} />}
                color="text-orange-400"
              />
              <MetricCard
                label={t('muscleMass')}
                value={latest?.muscle_mass_kg}
                unit="kg"
                delta={delta(latest?.muscle_mass_kg, previous?.muscle_mass_kg)}
                icon={<TrendingUp size={15} />}
                color="text-blue-400"
              />
              <MetricCard
                label={t('waist')}
                value={latest?.waist_cm}
                unit="cm"
                delta={delta(latest?.waist_cm, previous?.waist_cm)}
                icon={<Ruler size={15} />}
                color="text-purple-400"
              />
            </div>

            {/* Weight chart */}
            <div className="card-surface rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-soma-text">
                  {t('weight')}
                </h2>
                <div className="flex items-center gap-1">
                  {PERIODS.map((p) => (
                    <button
                      key={p}
                      onClick={() => setDays(p)}
                      className={cn(
                        'px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors',
                        days === p
                          ? 'bg-soma-accent text-white'
                          : 'text-soma-muted hover:text-soma-text hover:bg-soma-surface',
                      )}
                    >
                      {t(`period${p}`)}
                    </button>
                  ))}
                </div>
              </div>

              {chartData.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-soma-muted">
                  <Scale size={32} className="opacity-40 mb-2" />
                  <p className="text-sm">{tc('noData')}</p>
                </div>
              ) : (
                <div style={{ height: '220px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={chartData}
                      margin={{ top: 5, right: 5, left: -20, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="grad-weight" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--soma-accent)" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="var(--soma-accent)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="var(--soma-border)"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: 'var(--soma-muted)', fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis
                        tick={{ fill: 'var(--soma-muted)', fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip content={(props) => <ChartTooltip {...(props as any)} />} />
                      <Area
                        type="monotone"
                        dataKey="weight_kg"
                        stroke="var(--soma-accent)"
                        strokeWidth={2}
                        fill="url(#grad-weight)"
                        dot={false}
                        activeDot={{ r: 3, strokeWidth: 0 }}
                        connectNulls
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Add form (collapsible) */}
            {showForm && (
              <form
                onSubmit={handleSubmit}
                className="card-surface rounded-xl p-4 space-y-4 border border-soma-border"
              >
                <h3 className="text-sm font-medium text-soma-text">
                  {t('addMeasurement')}
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {([
                    ['weight_kg', t('weight'), 'kg'],
                    ['body_fat_pct', t('bodyFat'), '%'],
                    ['muscle_mass_kg', t('muscleMass'), 'kg'],
                    ['waist_cm', t('waist'), 'cm'],
                  ] as const).map(([field, label, unit]) => (
                    <div key={field} className="space-y-1">
                      <label className="text-xs font-medium text-soma-muted">
                        {label}
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          min={0}
                          step="any"
                          value={form[field] ?? ''}
                          onChange={(e) => handleFieldChange(field, e.target.value)}
                          placeholder="0"
                          className="w-full px-3 py-2 pr-8 rounded-lg text-sm bg-soma-bg border border-soma-border text-soma-text placeholder:text-soma-muted/50 focus:outline-none focus:border-soma-accent/50 transition-colors"
                        />
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-soma-muted">
                          {unit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="px-4 py-2 rounded-lg text-xs font-medium border border-soma-border bg-soma-surface text-soma-muted hover:text-soma-text transition-colors"
                  >
                    {tc('cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={createMetric.isPending}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium bg-soma-accent text-white hover:bg-soma-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {createMetric.isPending && (
                      <Loader2 size={12} className="animate-spin" />
                    )}
                    {tc('save')}
                  </button>
                </div>
              </form>
            )}

            {/* History table */}
            <div className="card-surface rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-soma-border">
                <h2 className="text-sm font-medium text-soma-text">
                  {t('history')}
                </h2>
              </div>

              {entries.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-soma-muted">
                  <Scale size={32} className="opacity-40 mb-2" />
                  <p className="text-sm">{tc('noData')}</p>
                </div>
              ) : (
                <div className="overflow-x-auto max-h-80">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-soma-border text-soma-muted">
                        <th className="text-left px-4 py-2 font-medium">Date</th>
                        <th className="text-right px-4 py-2 font-medium">{t('weight')}</th>
                        <th className="text-right px-4 py-2 font-medium">{t('bodyFat')}</th>
                        <th className="text-right px-4 py-2 font-medium">{t('muscleMass')}</th>
                        <th className="text-right px-4 py-2 font-medium">{t('waist')}</th>
                        <th className="text-right px-4 py-2 font-medium">IMC</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...entries].reverse().map((entry) => (
                        <tr
                          key={entry.id}
                          className="border-b border-soma-border/50 hover:bg-soma-surface/50 transition-colors"
                        >
                          <td className="px-4 py-2.5 text-soma-text">
                            {safeDateFormat(entry.recorded_at, 'd MMM yyyy')}
                          </td>
                          <td className="text-right px-4 py-2.5 text-soma-text font-medium">
                            {entry.weight_kg != null ? `${entry.weight_kg.toFixed(1)} kg` : '\u2014'}
                          </td>
                          <td className="text-right px-4 py-2.5 text-soma-muted">
                            {entry.body_fat_pct != null ? `${entry.body_fat_pct.toFixed(1)}%` : '\u2014'}
                          </td>
                          <td className="text-right px-4 py-2.5 text-soma-muted">
                            {entry.muscle_mass_kg != null ? `${entry.muscle_mass_kg.toFixed(1)} kg` : '\u2014'}
                          </td>
                          <td className="text-right px-4 py-2.5 text-soma-muted">
                            {entry.waist_cm != null ? `${entry.waist_cm.toFixed(1)} cm` : '\u2014'}
                          </td>
                          <td className="text-right px-4 py-2.5 text-soma-muted">
                            {formatBmi(data?.current_bmi)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
