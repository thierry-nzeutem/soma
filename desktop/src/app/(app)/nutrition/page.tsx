'use client';

import { useState, useCallback } from 'react';
import {
  Utensils,
  Plus,
  Flame,
  Droplets,
  Loader2,
  Trash2,
  Apple,
} from 'lucide-react';
import {
  useNutritionEntries,
  useDailyNutritionSummary,
  useCreateNutritionEntry,
  useDeleteNutritionEntry,
} from '@/hooks/use-nutrition';
import type { NutritionEntryCreate } from '@/lib/types/api';
import { useTranslations } from '@/lib/i18n/config';
import { safeDateFormat } from '@/lib/utils';

// ─── Constants ───────────────────────────────────────────────────────────────

const MEAL_TYPES = [
  'breakfast',
  'lunch',
  'dinner',
  'snack',
  'supplement',
  'drink',
] as const;

const MEAL_TYPE_COLORS: Record<string, string> = {
  breakfast:  'bg-amber-500/15 text-amber-400 border-amber-500/30',
  lunch:      'bg-green-500/15 text-green-400 border-green-500/30',
  dinner:     'bg-blue-500/15 text-blue-400 border-blue-500/30',
  snack:      'bg-purple-500/15 text-purple-400 border-purple-500/30',
  supplement: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  drink:      'bg-sky-500/15 text-sky-400 border-sky-500/30',
};

const INITIAL_FORM: NutritionEntryCreate = {
  meal_type: 'lunch',
  meal_name: '',
  calories: undefined,
  protein_g: undefined,
  carbs_g: undefined,
  fat_g: undefined,
  notes: '',
};

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function ProgressBar({
  value,
  max,
  color,
}: {
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="h-2 w-full rounded-full bg-soma-bg overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function SummaryCard({
  label,
  value,
  target,
  unit,
  icon,
  color,
  barColor,
}: {
  label: string;
  value: number;
  target?: number;
  unit: string;
  icon: React.ReactNode;
  color: string;
  barColor: string;
}) {
  const t = useTranslations();
  return (
    <div className="card-surface rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className={color}>{icon}</span>
        <span className="text-xs font-medium text-soma-muted uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="text-xl font-bold text-soma-text">
        {value.toLocaleString()}
        <span className="text-xs font-normal text-soma-muted ml-1">{unit}</span>
      </p>
      {target != null && target > 0 && (
        <>
          <ProgressBar value={value} max={target} color={barColor} />
          <div className="flex items-center justify-between text-[11px] text-soma-muted">
            <span>
              {t('nutrition.target')}: {target.toLocaleString()}
            </span>
            <span>
              {Math.max(0, target - value).toLocaleString()} {t('nutrition.remaining')}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function MealTypeBadge({ type }: { type?: string | null }) {
  const label = type || 'meal';
  const cls =
    MEAL_TYPE_COLORS[label] ?? 'bg-soma-surface text-soma-muted border-soma-border';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium border ${cls}`}
    >
      {label}
    </span>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function NutritionPage() {
  const t = useTranslations();

  const [selectedDate, setSelectedDate] = useState<string>(todayISO);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<NutritionEntryCreate>({ ...INITIAL_FORM });
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const entries = useNutritionEntries(selectedDate);
  const summary = useDailyNutritionSummary(selectedDate);
  const createEntry = useCreateNutritionEntry();
  const deleteEntry = useDeleteNutritionEntry();

  // ── Form helpers ───────────────────────────────────────────────────────────

  const resetForm = useCallback(() => {
    setForm({ ...INITIAL_FORM });
    setShowForm(false);
  }, []);

  const handleFieldChange = useCallback(
    (field: keyof NutritionEntryCreate, value: string | number | undefined) => {
      setForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const body: NutritionEntryCreate = {
        ...form,
        logged_at: new Date(selectedDate + 'T12:00:00').toISOString(),
      };
      await createEntry.mutateAsync(body);
      resetForm();
    },
    [form, selectedDate, createEntry, resetForm],
  );

  const handleDelete = useCallback(
    async (id: string) => {
      await deleteEntry.mutateAsync(id);
      setDeletingId(null);
    },
    [deleteEntry],
  );

  // ── Derived data ───────────────────────────────────────────────────────────

  const totals = summary.data?.totals ?? {
    calories: 0,
    protein_g: 0,
    carbs_g: 0,
    fat_g: 0,
    fiber_g: 0,
  };
  const goals = summary.data?.goals;
  const entryList = entries.data?.entries ?? [];
  const isLoading = entries.isLoading || summary.isLoading;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">
              {t('nutrition.title')}
            </h1>
            <p className="text-sm text-soma-muted">{t('nutrition.subtitle')}</p>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value || todayISO())}
              className="px-3 py-2 rounded-lg text-xs font-medium border border-soma-border bg-soma-surface text-soma-text focus:outline-none focus:border-soma-accent/50 transition-colors"
            />
            <button
              onClick={() => setShowForm((v) => !v)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-soma-accent text-white hover:bg-soma-accent/90 transition-colors"
            >
              <Plus size={13} />
              {t('nutrition.addMeal')}
            </button>
          </div>
        </div>

        {/* Delete confirmation dialog */}
        {deletingId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setDeletingId(null)}>
            <div className="card-surface w-full max-w-sm mx-4 p-5 space-y-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-sm font-semibold text-soma-text">{t('common.deleteConfirm')}</h3>
              <p className="text-xs text-soma-muted">{t('common.deleteConfirmDesc')}</p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setDeletingId(null)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-soma-muted hover:text-soma-text transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={() => handleDelete(deletingId)}
                  className="px-4 py-2 rounded-lg text-xs font-medium bg-red-500 text-white hover:bg-red-600 transition-colors"
                >
                  {t('common.delete')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Daily summary + content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 size={24} className="animate-spin text-soma-muted" />
          </div>
        ) : (
          <>
            {/* Summary cards */}
            <div>
              <h2 className="text-sm font-medium text-soma-muted mb-3">
                {t('nutrition.dailySummary')}
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <SummaryCard
                  label={t('nutrition.calories')}
                  value={totals.calories}
                  target={goals?.calories_target}
                  unit="kcal"
                  icon={<Flame size={15} />}
                  color="text-orange-400"
                  barColor="bg-orange-500"
                />
                <SummaryCard
                  label={t('nutrition.protein')}
                  value={totals.protein_g}
                  target={goals?.protein_target_g}
                  unit="g"
                  icon={<Apple size={15} />}
                  color="text-red-400"
                  barColor="bg-red-500"
                />
                <SummaryCard
                  label={t('nutrition.carbs')}
                  value={totals.carbs_g}
                  target={goals?.carbs_target_g}
                  unit="g"
                  icon={<Droplets size={15} />}
                  color="text-blue-400"
                  barColor="bg-blue-500"
                />
                <SummaryCard
                  label={t('nutrition.fats')}
                  value={totals.fat_g}
                  target={goals?.fat_target_g}
                  unit="g"
                  icon={<Droplets size={15} />}
                  color="text-yellow-400"
                  barColor="bg-yellow-500"
                />
              </div>
            </div>

            {/* Add meal form (collapsible) */}
            {showForm && (
              <form
                onSubmit={handleSubmit}
                className="card-surface rounded-xl p-4 space-y-4 border border-soma-border"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Meal type */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-soma-muted">
                      {t('nutrition.mealType')}
                    </label>
                    <select
                      value={form.meal_type ?? 'lunch'}
                      onChange={(e) => handleFieldChange('meal_type', e.target.value)}
                      className="w-full px-3 py-2 rounded-lg text-sm bg-soma-bg border border-soma-border text-soma-text focus:outline-none focus:border-soma-accent/50 transition-colors"
                    >
                      {MEAL_TYPES.map((mt) => (
                        <option key={mt} value={mt}>
                          {mt.charAt(0).toUpperCase() + mt.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Meal name */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-soma-muted">
                      {t('nutrition.mealName')}
                    </label>
                    <input
                      type="text"
                      value={form.meal_name ?? ''}
                      onChange={(e) => handleFieldChange('meal_name', e.target.value)}
                      placeholder={t('nutrition.mealName')}
                      className="w-full px-3 py-2 rounded-lg text-sm bg-soma-bg border border-soma-border text-soma-text placeholder:text-soma-muted/50 focus:outline-none focus:border-soma-accent/50 transition-colors"
                    />
                  </div>
                </div>

                {/* Macro inputs */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {([
                    ['calories', t('nutrition.calories'), 'kcal'],
                    ['protein_g', t('nutrition.protein'), 'g'],
                    ['carbs_g', t('nutrition.carbs'), 'g'],
                    ['fat_g', t('nutrition.fats'), 'g'],
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
                          value={form[field as keyof NutritionEntryCreate] ?? ''}
                          onChange={(e) =>
                            handleFieldChange(
                              field as keyof NutritionEntryCreate,
                              e.target.value === '' ? undefined : Number(e.target.value),
                            )
                          }
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

                {/* Notes */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-soma-muted">Notes</label>
                  <textarea
                    value={form.notes ?? ''}
                    onChange={(e) => handleFieldChange('notes', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 rounded-lg text-sm bg-soma-bg border border-soma-border text-soma-text placeholder:text-soma-muted/50 focus:outline-none focus:border-soma-accent/50 transition-colors resize-none"
                  />
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="px-4 py-2 rounded-lg text-xs font-medium border border-soma-border bg-soma-surface text-soma-muted hover:text-soma-text transition-colors"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={createEntry.isPending}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium bg-soma-accent text-white hover:bg-soma-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {createEntry.isPending && (
                      <Loader2 size={12} className="animate-spin" />
                    )}
                    {t('common.save')}
                  </button>
                </div>
              </form>
            )}

            {/* Entries list */}
            <div className="space-y-2">
              {entryList.length === 0 ? (
                <div className="card-surface rounded-xl py-12 flex flex-col items-center gap-3 text-soma-muted">
                  <Utensils size={32} className="opacity-40" />
                  <p className="text-sm">{t('nutrition.noEntries')}</p>
                </div>
              ) : (
                entryList.map((entry) => (
                  <div
                    key={entry.id}
                    className="card-surface rounded-xl px-4 py-3 flex items-center gap-3 group"
                  >
                    <MealTypeBadge type={entry.meal_type} />

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-soma-text truncate">
                        {entry.meal_name || entry.meal_type || '\u2014'}
                      </p>
                      <p className="text-[11px] text-soma-muted">
                        {safeDateFormat(entry.logged_at, 'HH:mm')}
                      </p>
                    </div>

                    {/* Macros -- desktop */}
                    <div className="hidden sm:flex items-center gap-4 text-xs text-soma-muted">
                      {entry.calories != null && (
                        <span className="flex items-center gap-1">
                          <Flame size={11} className="text-orange-400" />
                          {entry.calories} kcal
                        </span>
                      )}
                      {entry.protein_g != null && (
                        <span className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                          {entry.protein_g}g P
                        </span>
                      )}
                      {entry.carbs_g != null && (
                        <span className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                          {entry.carbs_g}g C
                        </span>
                      )}
                      {entry.fat_g != null && (
                        <span className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                          {entry.fat_g}g F
                        </span>
                      )}
                    </div>

                    {/* Macros -- mobile */}
                    <div className="flex sm:hidden items-center gap-1 text-[10px] text-soma-muted">
                      {entry.calories != null && (
                        <span>{entry.calories} kcal</span>
                      )}
                    </div>

                    <button
                      onClick={() => setDeletingId(entry.id)}
                      disabled={deleteEntry.isPending}
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
