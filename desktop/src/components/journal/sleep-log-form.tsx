'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Moon, X, Star } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { showToast } from '@/components/ui/toaster';
import { useTranslations } from '@/lib/i18n/config';

interface SleepLogFormProps {
  onClose: () => void;
}

async function logSleep(data: {
  start_at: string;
  end_at: string;
  perceived_quality: number;
  notes?: string;
}) {
  const { data: resp } = await apiClient.post('/api/v1/sleep', data);
  return resp;
}

export function SleepLogForm({ onClose }: SleepLogFormProps) {
  const queryClient = useQueryClient();
  const t = useTranslations();

  // Default: yesterday 23:00 → today 07:00
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const [bedDate, setBedDate] = useState(yesterday.toISOString().slice(0, 10));
  const [bedTime, setBedTime] = useState('23:00');
  const [wakeDate, setWakeDate] = useState(today.toISOString().slice(0, 10));
  const [wakeTime, setWakeTime] = useState('07:00');
  const [quality, setQuality] = useState(4);
  const [notes, setNotes] = useState('');

  const mutation = useMutation({
    mutationFn: logSleep,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sleep-history'] });
      queryClient.invalidateQueries({ queryKey: ['sleep-analysis'] });
      queryClient.invalidateQueries({ queryKey: ['home-summary'] });
      showToast('Sommeil enregistré', 'success');
      onClose();
    },
  });

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const start_at = `${bedDate}T${bedTime}:00`;
    const end_at = `${wakeDate}T${wakeTime}:00`;
    mutation.mutate({
      start_at,
      end_at,
      perceived_quality: quality,
      ...(notes.trim() ? { notes: notes.trim() } : {}),
    });
  }

  const qualityLabels = ['', t('quality.1'), t('quality.2'), t('quality.3'), t('quality.4'), t('quality.5')];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="card-surface w-full max-w-md mx-4 p-6 space-y-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Moon size={18} className="text-soma-accent" />
            <h2 className="text-base font-semibold text-soma-text">{t('sleep.logTitle')}</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-soma-surface transition-colors">
            <X size={16} className="text-soma-muted" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Bedtime */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-soma-muted uppercase tracking-wide">{t('sleep.bedtime')}</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={bedDate}
                onChange={(e) => setBedDate(e.target.value)}
                className="flex-1 bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-sm text-soma-text focus:outline-none focus:border-soma-accent"
              />
              <input
                type="time"
                value={bedTime}
                onChange={(e) => setBedTime(e.target.value)}
                className="w-28 bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-sm text-soma-text focus:outline-none focus:border-soma-accent"
              />
            </div>
          </div>

          {/* Wake time */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-soma-muted uppercase tracking-wide">{t('sleep.wakeTime')}</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={wakeDate}
                onChange={(e) => setWakeDate(e.target.value)}
                className="flex-1 bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-sm text-soma-text focus:outline-none focus:border-soma-accent"
              />
              <input
                type="time"
                value={wakeTime}
                onChange={(e) => setWakeTime(e.target.value)}
                className="w-28 bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-sm text-soma-text focus:outline-none focus:border-soma-accent"
              />
            </div>
          </div>

          {/* Quality */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-soma-muted uppercase tracking-wide">
              {t('sleep.quality')} · {qualityLabels[quality]}
            </label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setQuality(v)}
                  className="p-1.5 rounded-md transition-colors hover:bg-soma-surface"
                >
                  <Star
                    size={22}
                    className={v <= quality ? 'text-soma-accent fill-soma-accent' : 'text-soma-border'}
                    fill={v <= quality ? 'currentColor' : 'none'}
                  />
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-soma-muted uppercase tracking-wide">{t('sleep.notes')}</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={t('sleep.notesPlaceholder')}
              rows={2}
              className="w-full bg-soma-surface border border-soma-border rounded-lg px-3 py-2 text-sm text-soma-text placeholder:text-soma-muted resize-none focus:outline-none focus:border-soma-accent"
            />
          </div>

          {/* Error */}
          {mutation.isError && (
            <p className="text-xs text-[#FF3B30]">
              {t('common.error')}
            </p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-soma-muted hover:text-soma-text transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-5 py-2 rounded-lg text-sm font-medium bg-soma-accent text-white hover:bg-soma-accent-dim transition-colors disabled:opacity-50"
            >
              {mutation.isPending ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
