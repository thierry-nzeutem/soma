'use client';

import { RefreshCw } from 'lucide-react';
import { format } from 'date-fns';
import { fr, enUS } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { LocaleToggle } from '@/components/ui/locale-toggle';
import { useTranslations } from '@/lib/i18n/config';
import { useLocaleStore } from '@/lib/store/locale';

interface TopBarProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function TopBar({ onRefresh, isRefreshing }: TopBarProps) {
  const t = useTranslations();
  const locale = useLocaleStore((s) => s.locale);

  const dateLocale = locale === 'fr' ? fr : enUS;
  const today = format(new Date(), "EEEE d MMMM yyyy", { locale: dateLocale });

  return (
    <header className="h-14 bg-soma-nav-bg border-b border-soma-border flex items-center justify-between px-4 sm:px-6 shrink-0">
      {/* Left — date */}
      <span className="text-xs text-soma-text-secondary capitalize">{today}</span>

      {/* Right — locale + theme toggle + refresh */}
      <div className="flex items-center gap-3">
        <LocaleToggle />
        <ThemeToggle />

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
              'bg-soma-surface border border-soma-border text-soma-text-secondary',
              'hover:border-soma-accent hover:text-soma-accent',
              'disabled:opacity-40 disabled:cursor-not-allowed'
            )}
          >
            <RefreshCw className={cn('w-3.5 h-3.5', isRefreshing && 'animate-spin')} />
            {t('dashboard.refresh')}
          </button>
        )}
      </div>
    </header>
  );
}
