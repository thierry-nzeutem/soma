'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import {
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { NAV_ITEMS, Activity, ShieldCheck } from './nav-items';
import { useCurrentPlan } from '@/hooks/use-entitlements';
import { getPlanDisplayName, getPlanBadgeColor } from '@/lib/entitlements';


export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { username, logout } = useAuthStore();
  const t = useTranslations();
  const currentPlan = useCurrentPlan();
  const planLabel = getPlanDisplayName(currentPlan);
  const planBadgeClass = getPlanBadgeColor(currentPlan);

  function handleLogout() {
    logout();
    router.push('/login');
  }

  return (
    <aside className="hidden lg:flex w-60 h-screen flex-col bg-soma-nav-bg border-r border-soma-border shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-soma-border">
        <div className="w-8 h-8 rounded-lg bg-soma-accent flex items-center justify-center shrink-0">
          <Activity className="w-4 h-4 text-black" strokeWidth={2.5} />
        </div>
        <div>
          <div className="text-sm font-bold text-soma-text tracking-wide">{t('app.title')}</div>
          <div className="text-xs text-soma-text-muted">{t('app.subtitle')}</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all',
                active
                  ? 'bg-soma-accent/10 text-soma-accent'
                  : 'text-soma-text-secondary hover:text-soma-text hover:bg-soma-surface'
              )}
            >
              <Icon
                className={cn(
                  'w-4.5 h-4.5 shrink-0 transition-colors',
                  active ? 'text-soma-accent' : 'text-soma-text-muted group-hover:text-soma-text-secondary'
                )}
              />
              <div className="flex-1 min-w-0">
                <div className={cn('text-sm font-medium', active && 'text-soma-accent')}>
                  {t(item.labelKey)}
                </div>
                <div className="text-xs text-soma-text-muted truncate">{t(item.descKey)}</div>
              </div>
              {active && (
                <ChevronRight className="w-3.5 h-3.5 text-soma-accent shrink-0" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-soma-border space-y-1">
        {/* User info */}
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-7 h-7 rounded-full bg-soma-accent/20 flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-soma-accent uppercase">
              {username?.[0] ?? '?'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-soma-text truncate">{username ?? 'Utilisateur'}</div>
            <div className="text-xs text-soma-text-muted">{t('common.connected')}</div>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${planBadgeClass}`}>
              {planLabel}
            </span>
          </div>
        </div>

        {/* Admin link */}
        <a
          href="/admin"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-soma-text-secondary hover:text-soma-text hover:bg-soma-surface transition-all"
          title="Administration"
        >
          <ShieldCheck className="w-4 h-4 shrink-0 text-soma-text-muted" />
          <span className="text-sm font-medium">Admin</span>
        </a>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-soma-text-secondary hover:text-soma-danger hover:bg-soma-danger/10 transition-all group"
        >
          <LogOut className="w-4 h-4 shrink-0 group-hover:text-soma-danger" />
          <span className="text-sm font-medium">{t('common.logout')}</span>
        </button>
      </div>
    </aside>
  );
}
