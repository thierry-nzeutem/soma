'use client';
// ─── SOMA Desktop — Zustand Theme Store ──────────────────────────────────────
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

/**
 * Resolves the actual theme ('light' | 'dark') from the user's preference.
 * When mode is 'system', checks `prefers-color-scheme`.
 */
export function resolveTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
  return mode;
}

/**
 * Applies the resolved theme to the <html> element.
 * Adds or removes the `dark` class.
 */
export function applyThemeToDOM(mode: ThemeMode): void {
  if (typeof document === 'undefined') return;

  const resolved = resolveTheme(mode);
  const html = document.documentElement;

  if (resolved === 'dark') {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      mode: 'light' as ThemeMode,

      setMode: (mode: ThemeMode) => {
        applyThemeToDOM(mode);
        set({ mode });
      },
    }),
    {
      name: 'soma-theme',
      onRehydrateStorage: () => (state) => {
        // Apply theme on hydration from localStorage
        if (state?.mode) {
          applyThemeToDOM(state.mode);
        }
      },
    }
  )
);
