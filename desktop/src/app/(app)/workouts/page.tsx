'use client';

import { useState, useCallback } from 'react';
import { Dumbbell, Plus, Clock, Flame, Loader2, Trash2, Check } from 'lucide-react';
import {
  useWorkoutSessions,
  useCreateWorkout,
  useUpdateWorkout,
  useDeleteWorkout,
} from '@/hooks/use-workout';
import type { WorkoutSession, WorkoutSessionCreate } from '@/lib/types/api';
import { useTranslations } from '@/lib/i18n/config';
import { safeDateFormat, cn } from '@/lib/utils';

// ── Constants ───────────────────────────────────────────────────────────────

const SESSION_TYPES = [
  'strength',
  'cardio',
  'hiit',
  'yoga',
  'mobility',
  'swimming',
  'walk',
  'bodyweight',
] as const;

const LOCATIONS = ['gym', 'home', 'outdoor', 'other'] as const;

const STATUS_COLORS: Record<string, string> = {
  completed: 'text-soma-success bg-soma-success/10',
  in_progress: 'text-soma-accent bg-soma-accent/10',
  cancelled: 'text-soma-danger bg-soma-danger/10',
  planned: 'text-soma-muted bg-soma-surface',
};

// ── Skeleton loader ─────────────────────────────────────────────────────────

function SessionCardSkeleton() {
  return (
    <div className="card-surface rounded-xl p-4 space-y-3 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 rounded bg-soma-border" />
        <div className="h-5 w-16 rounded-full bg-soma-border" />
      </div>
      <div className="h-3 w-32 rounded bg-soma-border" />
      <div className="grid grid-cols-3 gap-2">
        <div className="h-8 rounded bg-soma-border" />
        <div className="h-8 rounded bg-soma-border" />
        <div className="h-8 rounded bg-soma-border" />
      </div>
      <div className="h-3 w-full rounded bg-soma-border" />
    </div>
  );
}

// ── Session card ────────────────────────────────────────────────────────────

function SessionCard({
  session,
  onComplete,
  onDelete,
  isUpdating,
  isDeleting,
  t,
}: {
  session: WorkoutSession;
  onComplete: (id: string) => void;
  onDelete: (id: string) => void;
  isUpdating: boolean;
  isDeleting: boolean;
  t: (key: string) => string;
}) {
  const statusKey = session.status ?? 'planned';
  const statusClass = STATUS_COLORS[statusKey] ?? STATUS_COLORS.planned;

  return (
    <div className="card-surface rounded-xl p-4 space-y-3 transition-shadow hover:shadow-md">
      {/* Header: type + status */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-soma-text capitalize">
          {session.session_type ?? '\u2014'}
        </span>
        <span
          className={cn(
            'text-[10px] font-medium px-2 py-0.5 rounded-full capitalize',
            statusClass,
          )}
        >
          {statusKey.replace('_', ' ')}
        </span>
      </div>

      {/* Date */}
      <p className="text-xs text-soma-muted">
        {safeDateFormat(session.started_at, 'd MMM yyyy HH:mm')}
      </p>

      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {/* Duration */}
        <div className="rounded-lg bg-soma-bg px-2 py-1.5">
          <Clock size={12} className="mx-auto text-soma-muted mb-0.5" />
          <p className="text-xs font-medium text-soma-text">
            {session.duration_minutes != null ? `${session.duration_minutes}m` : '\u2014'}
          </p>
        </div>
        {/* Calories */}
        <div className="rounded-lg bg-soma-bg px-2 py-1.5">
          <Flame size={12} className="mx-auto text-soma-muted mb-0.5" />
          <p className="text-xs font-medium text-soma-text">
            {session.calories_burned_kcal != null
              ? `${session.calories_burned_kcal} kcal`
              : '\u2014'}
          </p>
        </div>
        {/* Tonnage / sets / reps */}
        <div className="rounded-lg bg-soma-bg px-2 py-1.5">
          <Dumbbell size={12} className="mx-auto text-soma-muted mb-0.5" />
          <p className="text-xs font-medium text-soma-text">
            {session.total_tonnage_kg != null
              ? `${session.total_tonnage_kg} kg`
              : session.total_sets != null
                ? `${session.total_sets}s / ${session.total_reps ?? 0}r`
                : '\u2014'}
          </p>
        </div>
      </div>

      {/* Location */}
      {session.location && (
        <p className="text-[11px] text-soma-muted capitalize">
          {session.location}
        </p>
      )}

      {/* Notes */}
      {session.notes && (
        <p className="text-xs text-soma-muted line-clamp-2">{session.notes}</p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-soma-border">
        {!session.is_completed && (
          <button
            onClick={() => onComplete(session.id)}
            disabled={isUpdating}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
              'bg-soma-accent/10 text-soma-accent hover:bg-soma-accent/20 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          >
            {isUpdating ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Check size={12} />
            )}
            {t('workouts.complete')}
          </button>
        )}
        <button
          onClick={() => onDelete(session.id)}
          disabled={isDeleting}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ml-auto',
            'bg-soma-danger/10 text-soma-danger hover:bg-soma-danger/20 transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {isDeleting ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Trash2 size={12} />
          )}
          {t('common.delete')}
        </button>
      </div>
    </div>
  );
}

// ── Empty state ─────────────────────────────────────────────────────────────

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-soma-muted">
      <Dumbbell size={40} strokeWidth={1.2} className="mb-4 opacity-40" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ── Create form ─────────────────────────────────────────────────────────────

function CreateSessionForm({
  onSubmit,
  onCancel,
  isPending,
  t,
}: {
  onSubmit: (data: WorkoutSessionCreate) => void;
  onCancel: () => void;
  isPending: boolean;
  t: (key: string) => string;
}) {
  const [sessionType, setSessionType] = useState<string>(SESSION_TYPES[0]);
  const [location, setLocation] = useState<string>(LOCATIONS[0]);
  const [notes, setNotes] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      session_type: sessionType,
      location: location || undefined,
      notes: notes.trim() || undefined,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="card-surface rounded-xl p-4 space-y-4 border border-soma-accent/30"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Type */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-soma-muted">
            {t('workouts.type')}
          </label>
          <select
            value={sessionType}
            onChange={(e) => setSessionType(e.target.value)}
            className={cn(
              'w-full rounded-lg border border-soma-border bg-soma-bg px-3 py-2',
              'text-sm text-soma-text focus:outline-none focus:ring-1 focus:ring-soma-accent',
              'capitalize',
            )}
          >
            {SESSION_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        {/* Location */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-soma-muted">
            {t('workouts.location')}
          </label>
          <select
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className={cn(
              'w-full rounded-lg border border-soma-border bg-soma-bg px-3 py-2',
              'text-sm text-soma-text focus:outline-none focus:ring-1 focus:ring-soma-accent',
              'capitalize',
            )}
          >
            {LOCATIONS.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Notes */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-soma-muted">
          {t('workouts.notes')}
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t('workouts.notesPlaceholder')}
          rows={2}
          className={cn(
            'w-full rounded-lg border border-soma-border bg-soma-bg px-3 py-2',
            'text-sm text-soma-text placeholder:text-soma-muted/50 resize-none',
            'focus:outline-none focus:ring-1 focus:ring-soma-accent',
          )}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={isPending}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium',
            'bg-soma-accent text-white hover:bg-soma-accent/90 transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {isPending && <Loader2 size={13} className="animate-spin" />}
          {t('workouts.startSession')}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg text-xs font-medium text-soma-muted hover:text-soma-text transition-colors"
        >
          {t('common.cancel')}
        </button>
      </div>
    </form>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function WorkoutsPage() {
  const [showForm, setShowForm] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const t = useTranslations();
  const { data, isLoading } = useWorkoutSessions();
  const createMutation = useCreateWorkout();
  const updateMutation = useUpdateWorkout();
  const deleteMutation = useDeleteWorkout();

  const sessions: WorkoutSession[] = data?.sessions ?? [];

  const handleCreate = useCallback(
    (body: WorkoutSessionCreate) => {
      createMutation.mutate(body, {
        onSuccess: () => setShowForm(false),
      });
    },
    [createMutation],
  );

  const handleComplete = useCallback(
    (id: string) => {
      setUpdatingId(id);
      updateMutation.mutate(
        {
          id,
          body: {
            status: 'completed',
            ended_at: new Date().toISOString(),
          },
        },
        { onSettled: () => setUpdatingId(null) },
      );
    },
    [updateMutation],
  );

  const handleDelete = useCallback(
    (id: string) => {
      setDeletingId(id);
      deleteMutation.mutate(id, {
        onSettled: () => setDeletingId(null),
      });
    },
    [deleteMutation],
  );

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-5 space-y-5 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-soma-text">
              {t('workouts.title')}
            </h1>
            <p className="text-sm text-soma-muted">{t('workouts.subtitle')}</p>
          </div>
          <button
            onClick={() => setShowForm((prev) => !prev)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium',
              'border border-soma-border bg-soma-surface text-soma-muted',
              'hover:text-soma-text hover:border-soma-accent/50 transition-colors',
            )}
          >
            <Plus size={13} />
            {t('workouts.newSession')}
          </button>
        </div>

        {/* Collapsible create form */}
        {showForm && (
          <CreateSessionForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            isPending={createMutation.isPending}
            t={t}
          />
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <SessionCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && sessions.length === 0 && (
          <EmptyState message={t('workouts.noSessions')} />
        )}

        {/* Session grid */}
        {!isLoading && sessions.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {sessions.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                onComplete={handleComplete}
                onDelete={handleDelete}
                isUpdating={updatingId === session.id}
                isDeleting={deletingId === session.id}
                t={t}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
