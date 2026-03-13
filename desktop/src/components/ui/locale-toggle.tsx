'use client';

import { useLocaleStore, type SomaLocale } from '@/lib/store/locale';
import { cn } from '@/lib/utils';

const LOCALES: { code: SomaLocale; flag: string; label: string }[] = [
  { code: 'fr', flag: '🇫🇷', label: 'FR' },
  { code: 'en', flag: '🇬🇧', label: 'EN' },
];

export function LocaleToggle() {
  const { locale, setLocale } = useLocaleStore();

  return (
    <div className="flex items-center bg-soma-surface border border-soma-border rounded-md overflow-hidden">
      {LOCALES.map((l) => (
        <button
          key={l.code}
          onClick={() => setLocale(l.code)}
          className={cn(
            'flex items-center gap-1 px-2 py-1 text-xs font-medium transition-all',
            locale === l.code
              ? 'bg-soma-accent/15 text-soma-accent'
              : 'text-soma-text-muted hover:text-soma-text hover:bg-soma-surface'
          )}
          title={l.code === 'fr' ? 'Français' : 'English'}
        >
          <span className="text-sm">{l.flag}</span>
          <span>{l.label}</span>
        </button>
      ))}
    </div>
  );
}
