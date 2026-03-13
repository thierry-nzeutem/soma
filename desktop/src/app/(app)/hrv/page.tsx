'use client';

import { Activity, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import { useHRVScore } from '@/hooks/use-health-analytics';
import { cn } from '@/lib/utils';

function stressColor(level: string): string {
  switch (level) {
    case 'low': return 'text-green-400 bg-green-500/10 border-green-500/30';
    case 'moderate': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    case 'very_high': return 'text-red-400 bg-red-500/10 border-red-500/30';
    default: return 'text-soma-muted bg-soma-surface border-soma-border';
  }
}

function stressLabel(level: string): string {
  const map: Record<string, string> = {
    low: 'Stress faible', moderate: 'Stress modere',
    high: 'Stress eleve', very_high: 'Stress tres eleve',
  };
  return map[level] ?? 'Inconnu';
}

function recoveryLabel(ind: string): string {
  const map: Record<string, string> = {
    optimal: 'Recuperation optimale', good: 'Bonne recuperation',
    fair: 'Recuperation correcte', poor: 'Recuperation insuffisante',
  };
  return map[ind] ?? 'Inconnue';
}

function scoreColor(score: number | null): string {
  if (score === null) return 'text-soma-muted';
  if (score >= 75) return 'text-green-400';
  if (score >= 50) return 'text-yellow-400';
  return 'text-red-400';
}

function barColor(avgMs: number | null): string {
  if (!avgMs) return '#374151';
  if (avgMs >= 60) return '#10B981';
  if (avgMs >= 40) return '#F59E0B';
  return '#EF4444';
}

export default function HRVPage() {
  const { data, isLoading, isError } = useHRVScore();

  const chartData = (data?.history ?? []).map(p => ({
    date: p.date.substring(8),
    hrv: p.avg_hrv_ms ?? 0,
    fullDate: p.date,
  }));

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-3xl mx-auto">

        <div className="flex items-center gap-3">
          <Activity size={20} className="text-soma-accent shrink-0" />
          <div>
            <h1 className="text-lg font-semibold text-soma-text">HRV & Stress</h1>
            <p className="text-sm text-soma-muted">Variabilite cardiaque et recuperation</p>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : isError ? (
          <div className="bg-soma-surface border border-soma-border rounded-xl p-6 text-center">
            <p className="text-soma-muted text-sm">Impossible de charger les donnees HRV.</p>
            <p className="text-soma-muted text-xs mt-1">Connectez un wearable compatible.</p>
          </div>
        ) : !data?.avg_hrv_ms ? (
          <div className="bg-soma-surface border border-soma-border rounded-xl p-10 text-center">
            <Activity size={40} className="text-soma-muted mx-auto mb-3" />
            <p className="text-soma-text font-medium">Aucune donnee HRV</p>
            <p className="text-soma-muted text-sm mt-1">Connectez Apple Watch, Garmin ou Polar pour obtenir votre HRV.</p>
          </div>
        ) : (
          <>
            {/* HRV Score hero */}
            <div className="bg-soma-surface border border-soma-border rounded-xl p-6 flex flex-col items-center gap-4">
              <div className={cn('w-28 h-28 rounded-full border-4 flex items-center justify-center', scoreColor(data.hrv_score).replace('text-', 'border-'))}>
                <span className={cn('text-4xl font-bold', scoreColor(data.hrv_score))}>
                  {data.hrv_score ?? '--'}
                </span>
              </div>
              <p className="text-soma-muted text-sm">Score HRV</p>
              <div className="flex gap-3 flex-wrap justify-center">
                <span className={cn('text-xs font-semibold px-3 py-1 rounded-full border', stressColor(data.stress_level))}>
                  {stressLabel(data.stress_level)}
                </span>
                <span className="text-xs font-semibold px-3 py-1 rounded-full border text-blue-400 bg-blue-500/10 border-blue-500/30">
                  {recoveryLabel(data.recovery_indicator)}
                </span>
              </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'HRV moyen', value: data.avg_hrv_ms ? `${Math.round(data.avg_hrv_ms)} ms` : '--' },
                { label: 'HRV repos', value: data.resting_hrv_ms ? `${Math.round(data.resting_hrv_ms)} ms` : '--' },
                {
                  label: 'Tendance 7j',
                  value: data.trend_7d !== null ? `${data.trend_7d > 0 ? '+' : ''}${data.trend_7d.toFixed(1)}%` : '--',
                  positive: data.trend_7d !== null && data.trend_7d > 0,
                  negative: data.trend_7d !== null && data.trend_7d < 0,
                },
              ].map(kpi => (
                <div key={kpi.label} className="bg-soma-surface border border-soma-border rounded-xl p-4">
                  <p className={cn('text-xl font-bold', kpi.positive ? 'text-green-400' : kpi.negative ? 'text-red-400' : 'text-soma-text')}>
                    {kpi.value}
                  </p>
                  <p className="text-xs text-soma-muted mt-1">{kpi.label}</p>
                </div>
              ))}
            </div>

            {/* 7-day chart */}
            {chartData.length > 0 && (
              <div className="bg-soma-surface border border-soma-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-soma-text mb-4">Historique HRV (7 jours)</h2>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={chartData} barCategoryGap="20%">
                    <XAxis dataKey="date" tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} unit=" ms" width={45} />
                    <Tooltip
                      contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }}
                      formatter={(v: number) => [`${v.toFixed(0)} ms`, 'HRV moyen']}
                    />
                    <Bar dataKey="hrv" radius={[4, 4, 0, 0]}>
                      {chartData.map((d, i) => (
                        <Cell key={i} fill={barColor(d.hrv)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Baseline */}
            {data.baseline_7d_ms && (
              <div className="bg-soma-surface border border-soma-border rounded-xl p-4 flex items-center gap-3">
                <Activity size={16} className="text-soma-muted" />
                <span className="text-sm text-soma-muted">Baseline 7 jours :</span>
                <span className="text-sm font-semibold text-soma-text">{Math.round(data.baseline_7d_ms)} ms</span>
              </div>
            )}

            {/* Recommendation */}
            {data.recommendation && (
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 flex gap-3">
                <Activity size={16} className="text-blue-400 mt-0.5 shrink-0" />
                <p className="text-sm text-soma-text leading-relaxed">{data.recommendation}</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
