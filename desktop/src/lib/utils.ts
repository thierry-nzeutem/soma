import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Safe date formatting — never throws. Returns fallback on invalid input. */
export function safeDateFormat(
  dateStr: string | null | undefined,
  pattern: string = 'd MMM',
  fallback: string = '—'
): string {
  if (!dateStr) return fallback;
  try {
    return format(parseISO(dateStr), pattern, { locale: fr });
  } catch {
    return dateStr || fallback;
  }
}

/** Safe number — ensures a value is a finite number or returns fallback */
export function safeNum(v: unknown, fallback: number = 0): number {
  if (typeof v === 'number' && Number.isFinite(v)) return v;
  if (typeof v === 'string') {
    const parsed = Number(v);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

/** Format a number with locale-aware formatting */
export function fmt(n: number | null | undefined, decimals = 0): string {
  if (n == null) return '—';
  return n.toLocaleString('fr-FR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Return a color class based on a 0-100 score */
export function scoreColor(score: number | null | undefined): string {
  if (score == null) return 'text-soma-text-secondary';
  if (score >= 75) return 'text-soma-success';
  if (score >= 50) return 'text-soma-warning';
  return 'text-soma-danger';
}

/** Return a background color string for readiness */
export function readinessHexColor(score: number | null | undefined): string {
  if (score == null) return '#888888';
  if (score >= 75) return '#34C759';
  if (score >= 50) return '#FF9500';
  return '#FF3B30';
}

/** Format percentage */
export function fmtPct(n: number | null | undefined, decimals = 1): string {
  if (n == null) return '—';
  return `${n.toFixed(decimals)}%`;
}

/** Format ms as human-readable */
export function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—';
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
