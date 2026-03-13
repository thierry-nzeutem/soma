'use client';

import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';

const PERIOD_KEYS = [
  { labelKey: 'journal.period7', value: 7 },
  { labelKey: 'journal.period30', value: 30 },
  { labelKey: 'journal.period90', value: 90 },
] as const;

interface PeriodSelectorProps {
  value: number;
  onChange: (days: number) => void;
}

export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  const t = useTranslations();

  return (
    <div className="flex items-center gap-1 p-1 bg-soma-surface rounded-lg border border-soma-border">
      {PERIOD_KEYS.map((period) => (
        <button
          key={period.value}
          onClick={() => onChange(period.value)}
          className={cn(
            'px-3 py-1.5 rounded-md text-xs font-medium transition-all',
            value === period.value
              ? 'bg-soma-accent text-soma-bg font-semibold'
              : 'text-soma-muted hover:text-soma-text'
          )}
        >
          {t(period.labelKey)}
        </button>
      ))}
    </div>
  );
}
