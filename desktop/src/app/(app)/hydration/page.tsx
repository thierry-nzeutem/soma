'use client';

import { useState } from 'react';
import {
  Droplets,
  Plus,
  Loader2,
  GlassWater,
  Coffee,
  Leaf,
  Trash2,
} from 'lucide-react';
import { useHydrationToday, useLogHydration, useDeleteHydration } from '@/hooks/use-hydration';
import { useTranslations } from '@/lib/i18n/config';
import { cn, safeDateFormat } from '@/lib/utils';

// ─── Constants ───────────────────────────────────────────────────────────────

const QUICK_AMOUNTS = [200, 300, 500] as const;

const BEVERAGE_TYPES = [
  { key: 'water', icon: 'droplets' },
  { key: 'tea', icon: 'leaf' },
  { key: 'coffee', icon: 'coffee' },
  { key: 'sparkling', icon: 'glass' },
] as const;

const BEVERAGE_COLORS: Record<string, string> = {
  water:     'bg-blue-500/15 text-blue-400 border-blue-500/30',
  tea:       'bg-green-500/15 text-green-400 border-green-500/30',
  coffee:    'bg-amber-500/15 text-amber-400 border-amber-500/30',
  sparkling: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function BeverageIcon({ type, size = 15 }: { type: string; size?: number }) {
  switch (type) {
    case 'tea':
      return <Leaf size={size} />;
    case 'coffee':
      return <Coffee size={size} />;
    case 'sparkling':
      return <GlassWater size={size} />;
    default:
      return <Droplets size={size} />;
  }
}

function ProgressRing({
  value,
  max,
  size = 180,
  strokeWidth = 12,
}: {
  value: number;
  max: number;
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  const offset = circumference * (1 - pct);
  const pctDisplay = Math.round(pct * 100);

  // Color based on percentage
  const strokeColor =
    pct >= 0.8 ? '#34C759' : pct >= 0.5 ? '#FF9500' : '#FF3B30';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-soma-border/40"
        />
        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-soma-text">{pctDisplay}%</span>
        <span className="text-xs text-soma-muted mt-0.5">
          {value.toLocaleString()} / {max.toLocaleString()} ml
        </span>
      </div>
    </div>
  );
}

function BeverageTypeBadge({ type }: { type?: string | null }) {
  const label = type || 'water';
  const cls =
    BEVERAGE_COLORS[label] ?? 'bg-soma-surface text-soma-muted border-soma-border';
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium border ${cls}`}
    >
      <BeverageIcon type={label} size={11} />
      {label}
    </span>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function HydrationPage() {
  const t = useTranslations();

  const [selectedBeverage, setSelectedBeverage] = useState<string>('water');
  const [customAmount, setCustomAmount] = useState<string>('');

  const { data, isLoading } = useHydrationToday();
  const logMutation = useLogHydration();
  const deleteMutation = useDeleteHydration();

  // ── Derived data ───────────────────────────────────────────────────────────

  const totalMl = data?.total_ml ?? 0;
  const targetMl = data?.target_ml ?? 2500;
  const remainingMl = Math.max(0, targetMl - totalMl);
  const entries = data?.entries ?? [];
  const pct = targetMl > 0 ? Math.min(totalMl / targetMl, 1) : 0;

  const statusColor =
    pct >= 0.8
      ? 'text-green-400'
      : pct >= 0.5
        ? 'text-orange-400'
        : 'text-red-400';

  // ── Handlers ───────────────────────────────────────────────────────────────

  function handleQuickAdd(ml: number) {
    logMutation.mutate({ volume_ml: ml, beverage_type: selectedBeverage });
  }

  function handleCustomAdd() {
    const ml = parseInt(customAmount, 10);
    if (!ml || ml <= 0) return;
    logMutation.mutate({ volume_ml: ml, beverage_type: selectedBeverage });
    setCustomAmount('');
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div>
          <h1 className="text-lg font-semibold text-soma-text">
            {t('hydration.title')}
          </h1>
          <p className="text-sm text-soma-muted">{t('hydration.subtitle')}</p>
        </div>

        {/* Loading state */}
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : (
          <>
            {/* Progress + stats row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Large progress ring */}
              <div className="sm:col-span-1 card-surface rounded-xl p-5 flex flex-col items-center justify-center">
                <ProgressRing value={totalMl} max={targetMl} />
              </div>

              {/* Stats cards */}
              <div className="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Today progress */}
                <div className="card-surface rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <Droplets size={15} className="text-blue-400" />
                    <span className="text-xs font-medium text-soma-muted uppercase tracking-wide">
                      {t('hydration.todayProgress')}
                    </span>
                  </div>
                  <p className={cn('text-2xl font-bold', statusColor)}>
                    {totalMl.toLocaleString()}
                    <span className="text-xs font-normal text-soma-muted ml-1">ml</span>
                  </p>
                  {/* Mini progress bar */}
                  <div className="h-2 w-full rounded-full bg-soma-bg overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all duration-500',
                        pct >= 0.8 ? 'bg-green-500' : pct >= 0.5 ? 'bg-orange-500' : 'bg-red-500'
                      )}
                      style={{ width: `${Math.round(pct * 100)}%` }}
                    />
                  </div>
                </div>

                {/* Target */}
                <div className="card-surface rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <GlassWater size={15} className="text-cyan-400" />
                    <span className="text-xs font-medium text-soma-muted uppercase tracking-wide">
                      {t('hydration.target')}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-soma-text">
                    {targetMl.toLocaleString()}
                    <span className="text-xs font-normal text-soma-muted ml-1">ml</span>
                  </p>
                </div>

                {/* Remaining */}
                <div className="card-surface rounded-xl p-4 space-y-2 sm:col-span-2">
                  <div className="flex items-center gap-2">
                    <Droplets size={15} className="text-soma-muted" />
                    <span className="text-xs font-medium text-soma-muted uppercase tracking-wide">
                      {t('hydration.remaining')}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-soma-text">
                    {remainingMl.toLocaleString()}
                    <span className="text-xs font-normal text-soma-muted ml-1">ml</span>
                  </p>
                  <p className="text-[11px] text-soma-muted">
                    {remainingMl > 0
                      ? `~ ${Math.ceil(remainingMl / 250)} ${t('hydration.glassesLeft')}`
                      : t('hydration.goalReached')}
                  </p>
                </div>
              </div>
            </div>

            {/* Beverage type selector */}
            <div className="card-surface rounded-xl p-4 space-y-3">
              <h2 className="text-sm font-medium text-soma-muted">
                {t('hydration.beverageType')}
              </h2>
              <div className="flex flex-wrap gap-2">
                {BEVERAGE_TYPES.map(({ key }) => {
                  const isActive = selectedBeverage === key;
                  const colors = BEVERAGE_COLORS[key] ?? '';
                  return (
                    <button
                      key={key}
                      onClick={() => setSelectedBeverage(key)}
                      className={cn(
                        'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all',
                        isActive
                          ? `${colors} ring-1 ring-offset-1 ring-offset-soma-surface ring-current`
                          : 'border-soma-border bg-soma-surface text-soma-muted hover:text-soma-text hover:border-soma-accent/40'
                      )}
                    >
                      <BeverageIcon type={key} size={14} />
                      {t(`hydration.${key}`)}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Quick-add buttons + custom */}
            <div className="card-surface rounded-xl p-4 space-y-3">
              <h2 className="text-sm font-medium text-soma-muted">
                {t('hydration.quickAdd')}
              </h2>

              {/* Quick amounts */}
              <div className="flex flex-wrap gap-2">
                {QUICK_AMOUNTS.map((ml) => (
                  <button
                    key={ml}
                    onClick={() => handleQuickAdd(ml)}
                    disabled={logMutation.isPending}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all',
                      'bg-blue-500/10 text-blue-400 border border-blue-500/30',
                      'hover:bg-blue-500/20 hover:border-blue-500/50',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {logMutation.isPending ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Plus size={13} />
                    )}
                    {ml} ml
                  </button>
                ))}
              </div>

              {/* Custom amount input */}
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type="number"
                    min={1}
                    max={2000}
                    value={customAmount}
                    onChange={(e) => setCustomAmount(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCustomAdd()}
                    placeholder={t('hydration.customAmount')}
                    className="w-full px-3 py-2 pr-10 rounded-lg text-sm bg-soma-bg border border-soma-border text-soma-text placeholder:text-soma-muted/50 focus:outline-none focus:border-soma-accent/50 transition-colors"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-soma-muted">
                    ml
                  </span>
                </div>
                <button
                  onClick={handleCustomAdd}
                  disabled={logMutation.isPending || !customAmount}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-colors',
                    'bg-soma-accent text-white hover:bg-soma-accent/90',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {logMutation.isPending ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Plus size={12} />
                  )}
                  {t('hydration.addCustom')}
                </button>
              </div>
            </div>

            {/* Today's log */}
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-soma-muted">
                {t('hydration.todayLog')}
              </h2>

              {entries.length === 0 ? (
                <div className="card-surface rounded-xl py-12 flex flex-col items-center gap-3 text-soma-muted">
                  <Droplets size={32} className="opacity-40" />
                  <p className="text-sm">{t('hydration.noEntries')}</p>
                </div>
              ) : (
                entries
                  .slice()
                  .sort((a, b) => new Date(b.logged_at).getTime() - new Date(a.logged_at).getTime())
                  .map((entry) => (
                    <div
                      key={entry.id}
                      className="card-surface rounded-xl px-4 py-3 flex items-center gap-3 group"
                    >
                      <BeverageTypeBadge type={entry.beverage_type} />

                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-soma-text">
                          {entry.volume_ml} ml
                        </p>
                        <p className="text-[11px] text-soma-muted">
                          {safeDateFormat(entry.logged_at, 'HH:mm')}
                        </p>
                      </div>

                      <div className="flex items-center gap-1 text-xs text-soma-muted">
                        <Droplets size={12} className="text-blue-400" />
                        {entry.volume_ml} ml
                      </div>

                      <button
                        onClick={() => deleteMutation.mutate(entry.id)}
                        disabled={deleteMutation.isPending}
                        className="p-1.5 rounded-md text-soma-muted hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-50"
                        title={t('common.delete')}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
