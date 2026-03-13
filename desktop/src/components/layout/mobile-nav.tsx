'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MoreHorizontal, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import { PRIMARY_NAV, SECONDARY_NAV } from './nav-items';

export function MobileNav() {
  const pathname = usePathname();
  const t = useTranslations();
  const [moreOpen, setMoreOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close the "More" menu when clicking outside
  useEffect(() => {
    if (!moreOpen) return;
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [moreOpen]);

  // Close "More" menu on route change
  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  // Check if any secondary nav item is active
  const secondaryActive = SECONDARY_NAV.some((item) =>
    pathname.startsWith(item.href)
  );

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 lg:hidden" ref={menuRef}>
      {/* "More" popup menu */}
      {moreOpen && (
        <div className="absolute bottom-full left-0 right-0 bg-soma-nav-bg border-t border-soma-border shadow-lg">
          <div className="grid grid-cols-3 gap-1 p-3">
            {SECONDARY_NAV.map((item) => {
              const Icon = item.icon;
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex flex-col items-center gap-1.5 py-3 px-2 rounded-lg transition-colors',
                    active
                      ? 'bg-soma-accent/10 text-soma-accent'
                      : 'text-soma-text-secondary hover:bg-soma-surface'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-[10px] font-medium leading-tight text-center">
                    {t(item.labelKey)}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Bottom tab bar */}
      <nav className="flex items-center justify-around bg-soma-nav-bg border-t border-soma-border h-16 pb-safe">
        {PRIMARY_NAV.map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 min-w-[56px] h-full px-1 transition-colors',
                active
                  ? 'text-soma-accent'
                  : 'text-soma-text-muted'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium leading-tight">
                {t(item.labelKey)}
              </span>
            </Link>
          );
        })}

        {/* "More" button */}
        <button
          onClick={() => setMoreOpen((v) => !v)}
          className={cn(
            'flex flex-col items-center justify-center gap-0.5 min-w-[56px] h-full px-1 transition-colors',
            moreOpen || secondaryActive
              ? 'text-soma-accent'
              : 'text-soma-text-muted'
          )}
        >
          {moreOpen ? <X className="w-5 h-5" /> : <MoreHorizontal className="w-5 h-5" />}
          <span className="text-[10px] font-medium leading-tight">
            {moreOpen ? 'Fermer' : 'Plus'}
          </span>
        </button>
      </nav>
    </div>
  );
}
