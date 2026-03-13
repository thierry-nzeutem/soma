'use client';

import { Dumbbell, Utensils, Droplets, Clock, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { DailyHealthPlanResponse } from '@/lib/types/api';

interface HealthPlanCardProps {
  data: DailyHealthPlanResponse | undefined;
  isLoading: boolean;
}

function PlanRow({
  icon: Icon,
  label,
  value,
  unit,
  accent,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-soma-border last:border-0">
      <div className="flex items-center gap-2.5">
        <Icon size={14} className={accent ? 'text-soma-accent' : 'text-soma-muted'} />
        <span className="text-sm text-soma-muted">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-sm font-semibold text-soma-text tabular-nums">
          {value ?? '—'}
        </span>
        {unit && (
          <span className="text-xs text-soma-muted">{unit}</span>
        )}
      </div>
    </div>
  );
}

export function HealthPlanCard({ data, isLoading }: HealthPlanCardProps) {
  const t = useTranslations();
  if (isLoading) {
    return (
      <div className="card-surface rounded-xl p-5 flex flex-col gap-4">
        <div className="h-5 w-32 bg-soma-border rounded animate-pulse" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-8 bg-soma-border rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card-surface rounded-xl p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-2">
          {t('plan.dailyPlan')}
        </p>
        <p className="text-sm text-soma-muted">{t('plan.noData')}</p>
      </div>
    );
  }

  const workout = data.workout_recommendation;
  // Support both nested nutrition_targets and flat fields
  const nutrition = data.nutrition_targets ?? {
    calories_target: data.calorie_target,
    protein_g: data.protein_target_g,
    water_ml: data.hydration_target_ml,
  };

  return (
    <div className="card-surface rounded-xl p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted mb-3">
        Plan du Jour
      </p>

      {/* Workout section */}
      {workout && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Dumbbell size={12} className="text-soma-accent" />
            <span className="text-xs font-semibold text-soma-accent uppercase tracking-wide">
              {t('plan.training')}
            </span>
          </div>
          <div className="space-y-0">
            {(workout.workout_type ?? workout.type) && (
              <PlanRow
                icon={Dumbbell}
                label={t('plan.type')}
                value={workout.workout_type ?? workout.type}
                accent
              />
            )}
            {workout.duration_minutes != null && (
              <PlanRow
                icon={Clock}
                label={t('plan.duration')}
                value={workout.duration_minutes}
                unit="min"
              />
            )}
            {workout.intensity && (
              <PlanRow
                icon={Flame}
                label={t('plan.intensity')}
                value={workout.intensity}
              />
            )}
          </div>
          {workout.rationale && (
            <p className="text-xs text-soma-muted mt-2 leading-relaxed">
              {workout.rationale}
            </p>
          )}
        </div>
      )}

      {/* Nutrition section */}
      {nutrition && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Utensils size={12} className="text-soma-accent" />
            <span className="text-xs font-semibold text-soma-accent uppercase tracking-wide">
              {t('plan.nutrition')}
            </span>
          </div>
          <div className="space-y-0">
            {nutrition.calories_target != null && (
              <PlanRow
                icon={Flame}
                label={t('plan.calories')}
                value={Math.round(nutrition.calories_target)}
                unit="kcal"
                accent
              />
            )}
            {nutrition.protein_g != null && (
              <PlanRow
                icon={Utensils}
                label={t('plan.proteins')}
                value={Math.round(nutrition.protein_g)}
                unit="g"
              />
            )}
            {nutrition.carbs_g != null && (
              <PlanRow
                icon={Utensils}
                label={t('plan.carbs')}
                value={Math.round(nutrition.carbs_g)}
                unit="g"
              />
            )}
            {nutrition.fat_g != null && (
              <PlanRow
                icon={Utensils}
                label={t('plan.fats')}
                value={Math.round(nutrition.fat_g)}
                unit="g"
              />
            )}
            {nutrition.water_ml != null && (
              <PlanRow
                icon={Droplets}
                label={t('dashboard.hydration')}
                value={nutrition.water_ml >= 1000
                  ? (nutrition.water_ml / 1000).toFixed(1)
                  : nutrition.water_ml}
                unit={nutrition.water_ml >= 1000 ? 'L' : 'ml'}
              />
            )}
          </div>
        </div>
      )}

      {/* Morning briefing text if present */}
      {data.morning_briefing && (
        <div className="mt-4 rounded-lg bg-soma-bg border border-soma-border p-3">
          <p className="text-xs text-soma-muted leading-relaxed line-clamp-4">
            {data.morning_briefing}
          </p>
        </div>
      )}
    </div>
  );
}
