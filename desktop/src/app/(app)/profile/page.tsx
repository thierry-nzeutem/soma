'use client';

import { useState } from 'react';
import { User, Ruler, Weight, Target, Activity, Droplets, Footprints, Flame, Save, Loader2 } from 'lucide-react';
import { useProfile, useUpdateProfile } from '@/hooks/use-profile';
import { useTranslations } from '@/lib/i18n/config';
import { cn } from '@/lib/utils';

function Field({
  icon: Icon,
  label,
  value,
  suffix,
  editing,
  type = 'text',
  onChange,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | null | undefined;
  suffix?: string;
  editing: boolean;
  type?: string;
  onChange?: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-4 py-3 border-b border-soma-border last:border-b-0">
      <Icon size={16} className="text-soma-accent shrink-0" />
      <span className="text-sm text-soma-muted w-40 shrink-0">{label}</span>
      {editing ? (
        <input
          type={type}
          value={value ?? ''}
          onChange={(e) => onChange?.(e.target.value)}
          className="flex-1 bg-soma-surface border border-soma-border rounded-lg px-3 py-1.5 text-sm text-soma-text focus:outline-none focus:border-soma-accent"
        />
      ) : (
        <span className="flex-1 text-sm text-soma-text">
          {value != null && value !== '' ? `${value}${suffix ? ` ${suffix}` : ''}` : '\u2014'}
        </span>
      )}
    </div>
  );
}



// ─── Value translation maps ─────────────────────────────────────────────────

const SEX_KEYS: Record<string, string> = {
  male: 'profile.sexMale',
  female: 'profile.sexFemale',
};

const ACTIVITY_KEYS: Record<string, string> = {
  sedentary: 'profile.activitySedentary',
  light: 'profile.activityLight',
  moderate: 'profile.activityModerate',
  active: 'profile.activityActive',
  very_active: 'profile.activityVeryActive',
};

const GOAL_KEYS: Record<string, string> = {
  performance: 'profile.goalPerformance',
  weight_loss: 'profile.goalWeightLoss',
  muscle_gain: 'profile.goalMuscleGain',
  health: 'profile.goalHealth',
  maintenance: 'profile.goalMaintenance',
};

function translateValue(
  value: string | null | undefined,
  map: Record<string, string>,
  t: (key: string) => string,
): string | null | undefined {
  if (!value) return value;
  const key = map[value];
  return key ? t(key) : value;
}

export default function ProfilePage() {
  const { data: profile, isLoading, error } = useProfile();
  const mutation = useUpdateProfile();
  const t = useTranslations();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string | number | null>>({});

  function startEdit() {
    if (!profile) return;
    setForm({
      first_name: profile.first_name ?? '',
      age: profile.age ?? '',
      sex: profile.sex ?? '',
      height_cm: profile.height_cm ?? '',
      weight_kg: profile.weight_kg ?? '',
      goal_weight_kg: profile.goal_weight_kg ?? '',
      primary_goal: profile.primary_goal ?? '',
      activity_level: profile.activity_level ?? '',
      calorie_target: profile.calorie_target ?? '',
      protein_target_g: profile.protein_target_g ?? '',
      hydration_target_ml: profile.hydration_target_ml ?? '',
      steps_goal: profile.steps_goal ?? '',
    });
    setEditing(true);
  }

  function handleSave() {
    const updates: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(form)) {
      if (val === '' || val == null) continue;
      const numFields = ['age', 'height_cm', 'weight_kg', 'goal_weight_kg', 'calorie_target', 'protein_target_g', 'hydration_target_ml', 'steps_goal'];
      updates[key] = numFields.includes(key) ? Number(val) : val;
    }
    mutation.mutate(updates, {
      onSuccess: () => setEditing(false),
    });
  }

  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto">
        <div className="px-4 sm:px-6 py-5 max-w-4xl mx-auto space-y-5">
          <div className="animate-pulse space-y-4">
            <div className="h-6 w-48 bg-soma-surface rounded" />
            <div className="h-4 w-32 bg-soma-surface rounded" />
            <div className="space-y-3 mt-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-10 bg-soma-surface rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="h-full overflow-y-auto">
        <div className="px-4 sm:px-6 py-5 max-w-4xl mx-auto">
          <h1 className="text-lg font-semibold text-soma-text">{t('profile.title')}</h1>
          <p className="text-sm text-soma-muted mt-2">{t('common.error')}</p>
        </div>
      </div>
    );
  }

  const set = (key: string) => (v: string) => setForm((f) => ({ ...f, [key]: v }));

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 max-w-4xl mx-auto space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">{t('profile.title')}</h1>
            <p className="text-sm text-soma-muted">{t('profile.subtitle')}</p>
          </div>
          {editing ? (
            <button
              onClick={handleSave}
              disabled={mutation.isPending}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium',
                'bg-soma-accent text-black hover:bg-soma-accent/90 transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {mutation.isPending ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
              {t('common.save')}
            </button>
          ) : (
            <button
              onClick={startEdit}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium border border-soma-border bg-soma-surface text-soma-muted hover:text-soma-text hover:border-soma-accent/50 transition-colors"
            >
              {t('common.edit')}
            </button>
          )}
        </div>

        {/* User card */}
        <div className="card-surface p-5 space-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-full bg-soma-accent/20 flex items-center justify-center">
              <span className="text-lg font-bold text-soma-accent uppercase">
                {(profile.first_name ?? profile.username)?.[0] ?? '?'}
              </span>
            </div>
            <div>
              <div className="text-base font-semibold text-soma-text">{profile.first_name ?? profile.username}</div>
              <div className="text-xs text-soma-muted">@{profile.username}</div>
            </div>
          </div>

          <Field icon={User} label={t('profile.firstName')} value={editing ? form.first_name : profile.first_name} editing={editing} onChange={set('first_name')} />
          <Field icon={User} label={t('profile.age')} value={editing ? form.age : profile.age} suffix={t('profile.years')} editing={editing} type="number" onChange={set('age')} />
          <Field icon={User} label={t('profile.sex')} value={editing ? form.sex : translateValue(profile.sex, SEX_KEYS, t)} editing={editing} onChange={set('sex')} />
          <Field icon={Ruler} label={t('profile.height')} value={editing ? form.height_cm : profile.height_cm} suffix="cm" editing={editing} type="number" onChange={set('height_cm')} />
          <Field icon={Weight} label={t('profile.currentWeight')} value={editing ? form.weight_kg : profile.weight_kg} suffix="kg" editing={editing} type="number" onChange={set('weight_kg')} />
          <Field icon={Target} label={t('profile.goalWeight')} value={editing ? form.goal_weight_kg : profile.goal_weight_kg} suffix="kg" editing={editing} type="number" onChange={set('goal_weight_kg')} />
          <Field icon={Activity} label={t('profile.activityLevel')} value={editing ? form.activity_level : translateValue(profile.activity_level, ACTIVITY_KEYS, t)} editing={editing} onChange={set('activity_level')} />
          <Field icon={Target} label={t('profile.primaryGoal')} value={editing ? form.primary_goal : translateValue(profile.primary_goal, GOAL_KEYS, t)} editing={editing} onChange={set('primary_goal')} />
        </div>

        {/* Targets card */}
        <div className="card-surface p-5 space-y-1">
          <h2 className="text-sm font-semibold text-soma-text mb-3">{t('profile.targets')}</h2>
          <Field icon={Flame} label={t('profile.calorieTarget')} value={editing ? form.calorie_target : profile.calorie_target} suffix="kcal" editing={editing} type="number" onChange={set('calorie_target')} />
          <Field icon={Target} label={t('profile.proteinTarget')} value={editing ? form.protein_target_g : profile.protein_target_g} suffix="g" editing={editing} type="number" onChange={set('protein_target_g')} />
          <Field icon={Droplets} label={t('profile.hydrationTarget')} value={editing ? form.hydration_target_ml : profile.hydration_target_ml} suffix="ml" editing={editing} type="number" onChange={set('hydration_target_ml')} />
          <Field icon={Footprints} label={t('profile.stepsGoal')} value={editing ? form.steps_goal : profile.steps_goal} suffix={t('profile.stepsUnit')} editing={editing} type="number" onChange={set('steps_goal')} />
        </div>
      </div>
    </div>
  );
}
