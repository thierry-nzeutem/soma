'use client';

import { Zap, Loader2 } from 'lucide-react';
import { useCardioFitness } from '@/hooks/use-health-analytics';
import { useTranslations } from '@/lib/i18n/config';
import { cn } from '@/lib/utils';

// Category color map
function categoryColor(category: string): string {
  switch (category) {
    case 'Très faible': return 'bg-red-500/15 text-red-400';
    case 'Faible': return 'bg-orange-500/15 text-orange-400';
    case 'Moyen': return 'bg-yellow-500/15 text-yellow-400';
    case 'Bon': return 'bg-green-500/15 text-green-400';
    case 'Excellent': return 'bg-purple-500/15 text-purple-400';
    default: return 'bg-soma-border/30 text-soma-muted';
  }
}

// VO2max value to color
function vo2Color(vo2: number): string {
  if (vo2 >= 55) return 'text-purple-400';
  if (vo2 >= 45) return 'text-green-400';
  if (vo2 >= 35) return 'text-yellow-400';
  if (vo2 >= 25) return 'text-orange-400';
  return 'text-red-400';
}

export default function FitnessPage() {
  const tCommon = useTranslations('common');
  const { data, isLoading, isError } = useCardioFitness();

  const vo2 = data?.vo2max ?? null;
  const category = data?.category ?? null;
  const percentile = data?.percentile ?? null;
  const ageGroup = data?.age_group ?? null;
  const suggestion = data?.improvement_suggestion ?? null;
  const refBars: Array<{ label: string; value: number }> = data?.reference_bars ?? [];

  // Max value for reference bars scale (ml/kg/min)
  const maxRef = 70;

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-3xl mx-auto">

        <div className="flex items-center gap-3">
          <Zap size={20} className="text-purple-400 shrink-0" />
          <div>
            <h1 className="text-lg font-semibold text-soma-text">Forme physique</h1>
            <p className="text-sm text-soma-muted">Cardio-fitness &amp; VO2max</p>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : isError ? (
          <div className="bg-soma-surface border border-soma-border rounded-xl p-6 text-center">
            <Zap size={28} className="text-soma-muted/40 mx-auto mb-2" />
            <p className="text-sm text-soma-danger">{tCommon('error')}</p>
          </div>
        ) : (
          <>
            <div className="bg-soma-surface border border-soma-border rounded-xl p-6">
              <div className="flex flex-col items-center gap-4">
                {/* Big VO2max value */}
                <div className="text-center">
                  <p className={cn('text-6xl font-black tracking-tight', vo2 != null ? vo2Color(vo2) : 'text-soma-muted')}>
                    {vo2 != null ? vo2.toFixed(1) : '—'}
                  </p>
                  <p className="text-sm text-soma-muted mt-1">ml/kg/min</p>
                  <p className="text-xs text-soma-muted">VO2max</p>
                </div>

                {/* Category badge */}
                {category && (
                  <span className={cn('px-4 py-1.5 rounded-full text-sm font-semibold', categoryColor(category))}>
                    {category}
                  </span>
                )}

                {/* Percentile bar */}
                {percentile != null && (
                  <div className="w-full max-w-sm">
                    <p className="text-xs text-soma-muted text-center mb-2">
                      Meilleur que{' '}
                      <span className="font-semibold text-soma-text">{percentile}%</span>
                      {ageGroup && (
                        <span> de votre tranche d&apos;âge ({ageGroup})</span>
                      )}
                    </p>
                    <div className="h-2.5 w-full rounded-full bg-soma-border/40 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-purple-400 transition-all duration-700"
                        style={{ width: percentile + '%' }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Reference bars */}
            {refBars.length > 0 && (
              <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-soma-text mb-4">
                  Références par groupe
                </h2>
                <div className="space-y-3">
                  {refBars.map((bar) => (
                    <div key={bar.label}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-soma-text">{bar.label}</span>
                        <span className="text-xs font-medium text-soma-muted">
                          {bar.value.toFixed(1)} ml/kg/min
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-soma-border/40 overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            vo2 != null && bar.value <= vo2
                              ? 'bg-purple-400'
                              : 'bg-soma-accent/60'
                          )}
                          style={{ width: Math.min(100, (bar.value / maxRef) * 100) + '%' }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Improvement suggestion */}
            {suggestion && (
              <div className="bg-purple-500/8 border border-purple-400/20 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <Zap size={16} className="text-purple-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-purple-400 mb-1">Conseil</p>
                    <p className="text-sm text-soma-text leading-relaxed">{suggestion}</p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  );
}
