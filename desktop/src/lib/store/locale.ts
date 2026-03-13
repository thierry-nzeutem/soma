'use client';
// ─── SOMA Desktop — Zustand Locale Store ──────────────────────────────────────
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type SomaLocale = 'fr' | 'en';

interface LocaleState {
  locale: SomaLocale;
  setLocale: (locale: SomaLocale) => void;
}

/**
 * Applies the locale to the <html lang="..."> attribute.
 */
export function applyLocaleToDOM(locale: SomaLocale): void {
  if (typeof document === 'undefined') return;
  document.documentElement.lang = locale;
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      locale: 'fr' as SomaLocale,

      setLocale: (locale: SomaLocale) => {
        applyLocaleToDOM(locale);
        set({ locale });
      },
    }),
    {
      name: 'soma-locale',
      onRehydrateStorage: () => (state) => {
        if (state?.locale) {
          applyLocaleToDOM(state.locale);
        }
      },
    }
  )
);
