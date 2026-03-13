'use client';

import {
  Activity,
  Heart,
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Brain,
  Dumbbell,
  Moon,
  Utensils,
  Scale,
  Target,
} from 'lucide-react';
import { useReadinessToday, useLongevityScore } from '@/hooks/use-scores';
import { useHealthPredictions } from '@/hooks/use-predictions';
import { useTranslations } from '@/lib/i18n/config';
import { cn } from '@/lib/utils';

// ─── Score Gauge ─────────────────────────────────────────────────────────────
// Reusable SVG circular gauge that animates via stroke-dasharray.
// Color is determined by value thresholds: green >= 80, orange >= 60, red < 60.

interface ScoreGaugeProps {
  value: number | null | undefined;
  size?: number;
  strokeWidth?: number;
  label?: string;
  className?: string;
}

function ScoreGauge({
  value,
  size = 140,
  strokeWidth = 10,
  label,
  className,
}: ScoreGaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const safeValue = typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 0;
  const dashOffset = circumference - (safeValue / 100) * circumference;

  // Color thresholds
  const strokeColor =
    safeValue >= 80
      ? '#34C759' // green
      : safeValue >= 60
        ? '#FF9500' // orange
        : '#FF3B30'; // red

  const trackColor = 'rgba(136,136,136,0.15)';

  return (
    <div className={cn('flex flex-col items-center gap-2', className)}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
      >
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        {/* Animated score arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-all duration-700 ease-out"
        />
      </svg>

      {/* Score number centered inside the gauge */}
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: size, height: size }}
      >
        <span
          className="font-bold text-soma-text"
          style={{ fontSize: size * 0.26 }}
        >
          {value != null ? Math.round(value) : '—'}
        </span>
        <span className="text-[10px] text-soma-muted font-medium">/100</span>
      </div>

      {label && (
        <span className="text-xs font-medium text-soma-muted text-center">{label}</span>
      )}
    </div>
  );
}

// ─── Small progress bar for component breakdowns ─────────────────────────────

interface ComponentBarProps {
  label: string;
  value: number | null | undefined;
  icon: React.ReactNode;
}

function ComponentBar({ label, value, icon }: ComponentBarProps) {
  const safe = typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 0;
  const barColor =
    safe >= 80 ? 'bg-soma-success' : safe >= 60 ? 'bg-soma-warning' : 'bg-soma-danger';

  return (
    <div className="flex items-center gap-2">
      <div className="text-soma-muted shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-0.5">
          <span className="text-[11px] text-soma-text truncate">{label}</span>
          <span className="text-[11px] text-soma-muted font-medium ml-2">
            {value != null ? Math.round(value) : '—'}
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-soma-border/50">
          <div
            className={cn('h-full rounded-full transition-all duration-500', barColor)}
            style={{ width: `${safe}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Loading Skeleton ────────────────────────────────────────────────────────

function CardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'bg-soma-surface border border-soma-border rounded-xl p-5 animate-pulse',
        className
      )}
    >
      <div className="h-4 w-1/3 rounded bg-soma-border/60 mb-4" />
      <div className="flex justify-center py-6">
        <div className="w-[140px] h-[140px] rounded-full bg-soma-border/40" />
      </div>
      <div className="space-y-2 mt-4">
        <div className="h-3 w-full rounded bg-soma-border/40" />
        <div className="h-3 w-2/3 rounded bg-soma-border/40" />
      </div>
    </div>
  );
}

// ─── Risk Level Badge ────────────────────────────────────────────────────────

function RiskBadge({ level, t }: { level: string; t: (k: string) => string }) {
  const normalized = level.toLowerCase();
  const colorClass =
    normalized === 'low'
      ? 'bg-soma-success/15 text-soma-success'
      : normalized === 'moderate' || normalized === 'medium'
        ? 'bg-soma-warning/15 text-soma-warning'
        : 'bg-soma-danger/15 text-soma-danger';

  const label =
    normalized === 'low'
      ? t('low')
      : normalized === 'moderate' || normalized === 'medium'
        ? t('moderate')
        : normalized === 'optimal'
          ? t('optimal')
          : t('high');

  return (
    <span className={cn('px-2 py-0.5 rounded-full text-[11px] font-semibold', colorClass)}>
      {label}
    </span>
  );
}

// ─── Component icon mapper for readiness breakdown ───────────────────────────

function componentIcon(key: string) {
  const size = 13;
  switch (key) {
    case 'sleep':
      return <Moon size={size} />;
    case 'hrv':
      return <Activity size={size} />;
    case 'training_load':
      return <Dumbbell size={size} />;
    case 'recovery':
      return <Heart size={size} />;
    default:
      return <Target size={size} />;
  }
}

// ─── Component icon mapper for longevity breakdown ───────────────────────────

function longevityIcon(key: string) {
  const size = 13;
  switch (key) {
    case 'cardio':
      return <Heart size={size} />;
    case 'strength':
      return <Dumbbell size={size} />;
    case 'sleep':
      return <Moon size={size} />;
    case 'nutrition':
      return <Utensils size={size} />;
    case 'weight':
      return <Scale size={size} />;
    case 'body_comp':
      return <Target size={size} />;
    case 'consistency':
      return <TrendingUp size={size} />;
    default:
      return <Brain size={size} />;
  }
}

// ─── Longevity component label mapping ───────────────────────────────────────

const LONGEVITY_LABELS: Record<string, string> = {
  cardio: 'Cardio',
  strength: 'Strength',
  sleep: 'Sleep',
  nutrition: 'Nutrition',
  weight: 'Weight',
  body_comp: 'Body Comp',
  consistency: 'Consistency',
};

// ═════════════════════════════════════════════════════════════════════════════
// Main Page Component
// ═════════════════════════════════════════════════════════════════════════════

export default function ScoresPage() {
  const t = useTranslations('scores');
  const tCommon = useTranslations('common');

  // ── Data queries ──────────────────────────────────────────────────────────
  const readiness = useReadinessToday();
  const longevity = useLongevityScore();
  const predictions = useHealthPredictions();

  // ── Readiness data extraction ─────────────────────────────────────────────
  const readinessScore = readiness.data?.score ?? null;
  const readinessComponents = readiness.data?.components;
  const readinessRecommendation = readiness.data?.recommendation;

  // ── Longevity data extraction ─────────────────────────────────────────────
  const longevityScore = longevity.data?.overall_score ?? null;
  const longevityComponents = longevity.data?.components;
  const bioAge = longevity.data?.biological_age_estimate;
  const chronAge = longevity.data?.chronological_age;

  // ── Predictions data extraction ───────────────────────────────────────────
  const injuryRisk = predictions.data?.injury_risk;
  const overtraining = predictions.data?.overtraining;
  const weightPred = predictions.data?.weight_prediction;

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* ── Page Header ─────────────────────────────────────────────────── */}
        <div>
          <h1 className="text-lg font-semibold text-soma-text">{t('title')}</h1>
          <p className="text-sm text-soma-muted">{t('subtitle')}</p>
        </div>

        {/* ── Main 3-column Grid ──────────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">

          {/* ═══ A) Readiness Score Card ═══════════════════════════════════ */}
          {readiness.isLoading ? (
            <CardSkeleton />
          ) : (
            <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
              {/* Card title */}
              <div className="flex items-center gap-2 mb-4">
                <Activity size={16} className="text-soma-accent" />
                <h2 className="text-sm font-semibold text-soma-text">
                  {t('readiness')}
                </h2>
              </div>

              {/* Circular gauge */}
              <div className="flex justify-center relative">
                <ScoreGauge value={readinessScore} size={150} label={t('readiness')} />
              </div>

              {/* Recommendation text */}
              {readinessRecommendation && (
                <p className="text-xs text-soma-muted text-center mt-3 leading-relaxed">
                  {readinessRecommendation}
                </p>
              )}

              {/* Component breakdown */}
              {readinessComponents && Object.keys(readinessComponents).length > 0 && (
                <div className="mt-5 space-y-2.5">
                  <h3 className="text-[11px] font-semibold text-soma-muted uppercase tracking-wider">
                    {t('components')}
                  </h3>
                  {Object.entries(readinessComponents).map(([key, val]) => (
                    <ComponentBar
                      key={key}
                      label={key.replace(/_/g, ' ')}
                      value={val}
                      icon={componentIcon(key)}
                    />
                  ))}
                </div>
              )}

              {/* Error fallback */}
              {readiness.isError && (
                <p className="text-xs text-soma-danger text-center mt-3">
                  {tCommon('error')}
                </p>
              )}
            </div>
          )}

          {/* ═══ B) Longevity Score Card ═══════════════════════════════════ */}
          {longevity.isLoading ? (
            <CardSkeleton />
          ) : (
            <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
              {/* Card title */}
              <div className="flex items-center gap-2 mb-4">
                <Heart size={16} className="text-soma-accent" />
                <h2 className="text-sm font-semibold text-soma-text">
                  {t('longevity')}
                </h2>
              </div>

              {/* Circular gauge */}
              <div className="flex justify-center relative">
                <ScoreGauge value={longevityScore} size={150} label={t('longevity')} />
              </div>

              {/* Biological age vs Chronological age */}
              {(bioAge != null || chronAge != null) && (
                <div className="mt-4 flex items-center justify-center gap-4">
                  {bioAge != null && (
                    <div className="text-center">
                      <p className="text-lg font-bold text-soma-text">{Math.round(bioAge)}</p>
                      <p className="text-[10px] text-soma-muted">{t('biologicalAge')}</p>
                    </div>
                  )}
                  {bioAge != null && chronAge != null && (
                    <div className="text-soma-muted">
                      {bioAge < chronAge ? (
                        <TrendingDown size={18} className="text-soma-success" />
                      ) : bioAge > chronAge ? (
                        <TrendingUp size={18} className="text-soma-danger" />
                      ) : (
                        <Minus size={18} className="text-soma-muted" />
                      )}
                    </div>
                  )}
                  {chronAge != null && (
                    <div className="text-center">
                      <p className="text-lg font-bold text-soma-text">{Math.round(chronAge)}</p>
                      <p className="text-[10px] text-soma-muted">{t('chronologicalAge')}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Longevity component breakdown */}
              {longevityComponents && Object.keys(longevityComponents).length > 0 && (
                <div className="mt-5 space-y-2.5">
                  <h3 className="text-[11px] font-semibold text-soma-muted uppercase tracking-wider">
                    {t('components')}
                  </h3>
                  {Object.entries(longevityComponents)
                    .filter(([, val]) => val != null)
                    .map(([key, val]) => (
                      <ComponentBar
                        key={key}
                        label={LONGEVITY_LABELS[key] ?? key.replace(/_/g, ' ')}
                        value={val!}
                        icon={longevityIcon(key)}
                      />
                    ))}
                </div>
              )}

              {/* Error fallback */}
              {longevity.isError && (
                <p className="text-xs text-soma-danger text-center mt-3">
                  {tCommon('error')}
                </p>
              )}
            </div>
          )}

          {/* ═══ C) Health Predictions Card ════════════════════════════════ */}
          {predictions.isLoading ? (
            <CardSkeleton />
          ) : (
            <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
              {/* Card title */}
              <div className="flex items-center gap-2 mb-4">
                <Shield size={16} className="text-soma-accent" />
                <h2 className="text-sm font-semibold text-soma-text">
                  {t('predictions')}
                </h2>
              </div>

              {/* ── Injury Risk ────────────────────────────────────────── */}
              {injuryRisk && (
                <div className="mb-5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-soma-text flex items-center gap-1.5">
                      <AlertTriangle size={13} className="text-soma-warning" />
                      {t('injuryRisk')}
                    </span>
                    <RiskBadge level={injuryRisk.risk_level} t={t} />
                  </div>
                  <div className="flex justify-center relative">
                    <ScoreGauge
                      value={injuryRisk.risk_score}
                      size={100}
                      strokeWidth={8}
                    />
                  </div>
                </div>
              )}

              {/* ── Overtraining Risk ─────────────────────────────────── */}
              {overtraining && (
                <div className="mb-5">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Dumbbell size={13} className="text-soma-warning" />
                    <span className="text-xs font-medium text-soma-text">
                      {t('overtrainingRisk')}
                    </span>
                    <span className="ml-auto text-[11px] text-soma-muted font-medium">
                      {overtraining.overtraining_risk != null
                        ? Math.round(overtraining.overtraining_risk)
                        : '—'}
                      /100
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-soma-border/50">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all duration-500',
                        (overtraining.overtraining_risk ?? 0) >= 80
                          ? 'bg-soma-danger'
                          : (overtraining.overtraining_risk ?? 0) >= 60
                            ? 'bg-soma-warning'
                            : 'bg-soma-success'
                      )}
                      style={{
                        width: `${Math.min(100, Math.max(0, overtraining.overtraining_risk ?? 0))}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* ── ACWR (Acute:Chronic Workload Ratio) ───────────────── */}
              {(injuryRisk?.acwr != null || overtraining?.acwr != null) && (
                <div className="mb-5 p-3 rounded-lg bg-soma-bg/60 border border-soma-border/50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-soma-muted">
                      {t('acwr')}
                    </span>
                    <span className="text-sm font-bold text-soma-text">
                      {(injuryRisk?.acwr ?? overtraining?.acwr)?.toFixed(2) ?? '—'}
                    </span>
                  </div>
                  {overtraining?.acwr_zone && (
                    <p className="text-[10px] text-soma-muted mt-1">
                      Zone: {overtraining.acwr_zone}
                    </p>
                  )}
                </div>
              )}

              {/* ── Recommendations ───────────────────────────────────── */}
              {injuryRisk?.recommendations && injuryRisk.recommendations.length > 0 && (
                <div className="mb-5">
                  <h3 className="text-[11px] font-semibold text-soma-muted uppercase tracking-wider mb-2">
                    {t('recommendations')}
                  </h3>
                  <ul className="space-y-1.5">
                    {injuryRisk.recommendations.map((rec, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-[11px] text-soma-text leading-snug"
                      >
                        <span className="mt-0.5 shrink-0 w-1 h-1 rounded-full bg-soma-accent" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* ── Weight Prediction ─────────────────────────────────── */}
              {weightPred && weightPred.predicted_weight_kg != null && (
                <div className="p-3 rounded-lg bg-soma-bg/60 border border-soma-border/50">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Scale size={13} className="text-soma-accent" />
                    <span className="text-xs font-medium text-soma-text">
                      {t('weightPrediction')}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-lg font-bold text-soma-text">
                      {Number(weightPred.predicted_weight_kg).toFixed(1)} kg
                    </span>
                    {weightPred.confidence != null && (
                      <span className="text-[10px] text-soma-muted">
                        {t('confidence')}: {Math.round((weightPred.confidence ?? 0) * 100)}%
                      </span>
                    )}
                  </div>
                  {weightPred.target_date && (
                    <p className="text-[10px] text-soma-muted mt-0.5">
                      {weightPred.target_date}
                    </p>
                  )}
                </div>
              )}

              {/* Overtraining recommendation text */}
              {overtraining?.recommendation && (
                <p className="text-xs text-soma-muted mt-3 leading-relaxed">
                  {overtraining.recommendation}
                </p>
              )}

              {/* Error fallback */}
              {predictions.isError && (
                <p className="text-xs text-soma-danger text-center mt-3">
                  {tCommon('error')}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
