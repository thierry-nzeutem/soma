// ─── SOMA Desktop — Lightweight i18n ──────────────────────────────────────────
// Client-side translation system using JSON message files + Zustand locale store.

import { useLocaleStore, type SomaLocale } from '@/lib/store/locale';
import frMessages from './messages/fr.json';
import enMessages from './messages/en.json';

type Messages = typeof frMessages;

const messages: Record<SomaLocale, Messages> = {
  fr: frMessages,
  en: enMessages,
};

/**
 * Retrieves a nested translation value by dot-separated key.
 * Example: get(messages, 'nav.dashboard') → 'Dashboard'
 */
function get(obj: Record<string, unknown>, path: string): string {
  const keys = path.split('.');
  let current: unknown = obj;

  for (const key of keys) {
    if (current == null || typeof current !== 'object') return path;
    current = (current as Record<string, unknown>)[key];
  }

  return typeof current === 'string' ? current : path;
}

/**
 * React hook — returns a `t()` function scoped to a namespace.
 *
 * @example
 * const t = useTranslations('nav');
 * t('dashboard') // → 'Dashboard' | 'Dashboard'
 * t('dashboardDesc') // → 'Health overview' | 'Vue d\'ensemble santé'
 */
export function useTranslations(namespace?: string) {
  const locale = useLocaleStore((s) => s.locale);
  const msg = messages[locale];

  return (key: string): string => {
    const fullKey = namespace ? `${namespace}.${key}` : key;
    return get(msg as unknown as Record<string, unknown>, fullKey);
  };
}

/**
 * Non-hook translation function — uses store directly.
 * Useful outside of React components.
 */
export function t(key: string, locale?: SomaLocale): string {
  const effectiveLocale = locale ?? useLocaleStore.getState().locale;
  const msg = messages[effectiveLocale];
  return get(msg as unknown as Record<string, unknown>, key);
}
