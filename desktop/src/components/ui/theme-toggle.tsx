'use client';

import { useThemeStore } from '@/lib/store/theme';
import { Sun, Moon, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';

const MODES = [
  { value: 'light' as const, icon: Sun, label: 'Clair' },
  { value: 'dark' as const, icon: Moon, label: 'Sombre' },
  { value: 'system' as const, icon: Monitor, label: 'Système' },
];

export function ThemeToggle() {
  const { mode, setMode } = useThemeStore();

  return (
    <div className="flex items-center bg-soma-surface border border-soma-border rounded-lg p-0.5">
      {MODES.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setMode(value)}
          title={label}
          className={cn(
            'flex items-center justify-center w-9 h-9 rounded-md transition-all',
            mode === value
              ? 'bg-soma-accent text-black'
              : 'text-soma-text-secondary hover:text-soma-text'
          )}
        >
          <Icon className="w-4 h-4" />
        </button>
      ))}
    </div>
  );
}
