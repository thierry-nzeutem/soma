'use client';

import { useEffect } from 'react';
import { useThemeStore, applyThemeToDOM } from '@/lib/store/theme';

/**
 * Invisible component that :
 * 1. Applies the persisted theme on first render (SSR → client hydration).
 * 2. Listens for OS-level `prefers-color-scheme` changes when mode is 'system'.
 */
export function ThemeInitializer() {
  const mode = useThemeStore((s) => s.mode);

  useEffect(() => {
    // Apply theme on mount / mode change
    applyThemeToDOM(mode);
  }, [mode]);

  useEffect(() => {
    if (mode !== 'system') return;

    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => applyThemeToDOM('system');

    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [mode]);

  return null;
}
