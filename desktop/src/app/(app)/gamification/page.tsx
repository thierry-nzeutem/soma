'use client';

import { Trophy, Flame, CheckCircle, Loader2, Star } from 'lucide-react';
import { useGamificationProfile } from '@/hooks/use-health-analytics';
import { cn } from '@/lib/utils';

function StreakCard({ label, current, best, activeToday, color }: {
  label: string; current: number; best: number; activeToday: boolean; color: string;
}) {
  return (
    <div className="bg-soma-surface border border-soma-border rounded-xl p-4 flex items-center gap-4">
      <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', `bg-${color}/10`)}>
        <Flame size={18} className={`text-${color}`} />
      </div>
      <div className="flex-1">
        <p className="text-sm font-semibold text-soma-text">{label}</p>
        {activeToday && <p className="text-xs text-green-400">Actif aujourd&apos;hui</p>}
      </div>
      <div className="text-right">
        <p className={cn('text-2xl font-bold', current > 0 ? `text-${color}` : 'text-soma-muted')}>{current}</p>
        <p className="text-xs text-soma-muted">Record: {best}j</p>
      </div>
    </div>
  );
}

export default function GamificationPage() {
  const { data, isLoading, isError } = useGamificationProfile();

  if (isLoading) return (
    <div className="flex items-center justify-center h-full">
      <Loader2 size={24} className="animate-spin text-soma-muted" />
    </div>
  );

  if (isError || !data) return (
    <div className="flex items-center justify-center h-full">
      <p className="text-soma-muted text-sm">Impossible de charger la progression.</p>
    </div>
  );

  const xpProgress = data.xp / (data.xp + data.xp_to_next_level);

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-3xl mx-auto">

        <div className="flex items-center gap-3">
          <Trophy size={20} className="text-yellow-400 shrink-0" />
          <div>
            <h1 className="text-lg font-semibold text-soma-text">Ma Progression</h1>
            <p className="text-sm text-soma-muted">Streaks, achievements et niveau</p>
          </div>
        </div>

        {/* Level Card */}
        <div className="bg-soma-surface border border-soma-accent/30 rounded-xl p-5">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-xl bg-soma-accent/20 flex items-center justify-center">
              <span className="text-2xl font-bold text-soma-accent">{data.level}</span>
            </div>
            <div className="flex-1">
              <p className="text-lg font-bold text-soma-text">{data.level_name}</p>
              <p className="text-xs text-soma-muted">{data.xp.toLocaleString()} XP  &middot;  {data.total_days_active} jours actifs</p>
            </div>
            <Star size={24} className="text-yellow-400" />
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-soma-muted">
              <span>Progression</span>
              <span>{data.xp_to_next_level} XP restants</span>
            </div>
            <div className="w-full bg-soma-border rounded-full h-2">
              <div
                className="bg-soma-accent h-2 rounded-full transition-all"
                style={{ width: `${Math.min(xpProgress * 100, 100).toFixed(1)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Overall score */}
        <div className="flex items-center gap-2">
          <Flame size={16} className="text-green-400" />
          <span className="text-sm text-soma-muted">Score de consistance :</span>
          <span className="text-sm font-bold text-green-400">{data.streaks.overall_score}/100</span>
        </div>

        {/* Streaks */}
        <div>
          <h2 className="text-sm font-semibold text-soma-text mb-3">Streaks</h2>
          <div className="space-y-3">
            <StreakCard label="Activite physique" current={data.streaks.activity.current} best={data.streaks.activity.best} activeToday={data.streaks.activity.active_today} color="orange-400" />
            <StreakCard label="Journal alimentaire" current={data.streaks.nutrition_logging.current} best={data.streaks.nutrition_logging.best} activeToday={data.streaks.nutrition_logging.active_today} color="green-400" />
            <StreakCard label="Hydratation" current={data.streaks.hydration.current} best={data.streaks.hydration.best} activeToday={data.streaks.hydration.active_today} color="blue-400" />
            <StreakCard label="Sommeil trace" current={data.streaks.sleep_logging.current} best={data.streaks.sleep_logging.best} activeToday={data.streaks.sleep_logging.active_today} color="purple-400" />
          </div>
        </div>

        {/* Achievements */}
        <div>
          <h2 className="text-sm font-semibold text-soma-text mb-3">Achievements</h2>
          <div className="space-y-3">
            {data.achievements.map(a => (
              <div key={a.id} className={cn(
                'bg-soma-surface border rounded-xl p-4 flex items-center gap-4',
                a.unlocked ? 'border-soma-accent/40' : 'border-soma-border'
              )}>
                <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center', a.unlocked ? 'bg-soma-accent/20' : 'bg-soma-border/30')}>
                  <Trophy size={20} className={a.unlocked ? 'text-soma-accent' : 'text-soma-muted'} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn('text-sm font-semibold', a.unlocked ? 'text-soma-text' : 'text-soma-muted')}>{a.title}</p>
                  <p className="text-xs text-soma-muted truncate">{a.description}</p>
                  <div className="mt-2 w-full bg-soma-border rounded-full h-1.5">
                    <div
                      className={cn('h-1.5 rounded-full', a.unlocked ? 'bg-soma-accent' : 'bg-soma-muted/50')}
                      style={{ width: `${Math.min((a.progress ?? 0) * 100, 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
                <div className="shrink-0">
                  {a.unlocked
                    ? <CheckCircle size={20} className="text-soma-accent" />
                    : <span className="text-xs text-soma-muted font-semibold">{Math.round((a.progress ?? 0) * 100)}%</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="h-6" />
      </div>
    </div>
  );
}
