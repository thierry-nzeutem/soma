'use client';

import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { ArrowUpDown, ArrowUp, ArrowDown, Download } from 'lucide-react';
import { cn, safeDateFormat } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { DailyMetricsRecord, SleepRecord } from '@/lib/types/api';

// ── Metrics Table ─────────────────────────────────────────────────────────────

const metricsHelper = createColumnHelper<DailyMetricsRecord>();

function SortIcon({ sorted }: { sorted: false | 'asc' | 'desc' }) {
  if (!sorted) return <ArrowUpDown size={12} className="text-soma-muted" />;
  return sorted === 'asc'
    ? <ArrowUp size={12} className="text-soma-accent" />
    : <ArrowDown size={12} className="text-soma-accent" />;
}

interface MetricsTableProps {
  data: DailyMetricsRecord[] | undefined;
  isLoading: boolean;
}

export function MetricsTable({ data, isLoading }: MetricsTableProps) {
  const t = useTranslations();
  const [sorting, setSorting] = useState<SortingState>([{ id: 'date', desc: true }]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const columns = useMemo(
    () => [
      metricsHelper.accessor('date', {
        header: 'Date',
        cell: (info) => safeDateFormat(info.getValue(), 'dd MMM yyyy'),
      }),
      metricsHelper.accessor('weight_kg', {
        header: 'Poids (kg)',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? v.toFixed(1) : '—';
        },
      }),
      metricsHelper.accessor('calories_consumed', {
        header: 'Calories',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? Math.round(v) : '—';
        },
      }),
      metricsHelper.accessor('protein_g', {
        header: 'Protéines (g)',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? Math.round(v) : '—';
        },
      }),
      metricsHelper.accessor('carbs_g', {
        header: 'Glucides (g)',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? Math.round(v) : '—';
        },
      }),
      metricsHelper.accessor('fat_g', {
        header: 'Lipides (g)',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? Math.round(v) : '—';
        },
      }),
      metricsHelper.accessor('water_ml', {
        header: 'Eau (ml)',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? Math.round(v) : '—';
        },
      }),
      metricsHelper.accessor('steps_count', {
        header: 'Pas',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? v.toLocaleString('fr-FR') : '—';
        },
      }),
    ],
    []
  );

  const table = useReactTable({
    data: Array.isArray(data) ? data : [],
    columns,
    state: { sorting, columnFilters },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  function exportCSV() {
    const rows = table.getFilteredRowModel().rows;
    const headers = columns.map((c) => (typeof c.header === 'string' ? c.header : String(c.id)));
    const csvRows = [
      headers.join(','),
      ...rows.map((row) =>
        row.getAllCells().map((cell) => {
          const v = cell.getValue();
          return v != null ? String(v) : '';
        }).join(',')
      ),
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `soma-metrics-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="card-surface rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-soma-border">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          Historique Métriques
        </p>
        <button
          onClick={exportCSV}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium
            text-soma-muted border border-soma-border hover:text-soma-text hover:border-soma-accent/50
            transition-colors"
        >
          <Download size={12} />
          CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-soma-border">
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className={cn(
                      'px-4 py-2.5 text-left text-soma-muted font-medium whitespace-nowrap',
                      header.column.getCanSort() && 'cursor-pointer hover:text-soma-text select-none'
                    )}
                  >
                    <div className="flex items-center gap-1.5">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() && (
                        <SortIcon sorted={header.column.getIsSorted()} />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-soma-border/50">
                  {columns.map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-3 bg-soma-border rounded animate-pulse" style={{ width: `${40 + j * 8}px` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-soma-muted"
                >
                  {t('common.noData')}
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, idx) => (
                <tr
                  key={row.id}
                  className={cn(
                    'border-b border-soma-border/50 transition-colors',
                    idx % 2 === 0 ? 'bg-transparent' : 'bg-soma-bg/30',
                    'hover:bg-soma-accent/5'
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-4 py-2.5 text-soma-text tabular-nums whitespace-nowrap"
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!isLoading && (
        <div className="px-4 py-2 border-t border-soma-border text-xs text-soma-muted">
          {table.getFilteredRowModel().rows.length} entrée(s)
        </div>
      )}
    </div>
  );
}

// ── Sleep Table ───────────────────────────────────────────────────────────────

const sleepHelper = createColumnHelper<SleepRecord>();

interface SleepTableProps {
  data: SleepRecord[] | undefined;
  isLoading: boolean;
}

export function SleepTable({ data, isLoading }: SleepTableProps) {
  const t = useTranslations();
  const [sorting, setSorting] = useState<SortingState>([{ id: 'date', desc: true }]);

  const columns = useMemo(
    () => [
      sleepHelper.accessor('date', {
        header: 'Date',
        cell: (info) => safeDateFormat(info.getValue(), 'dd MMM yyyy'),
      }),
      sleepHelper.accessor('duration_hours', {
        header: 'Durée (h)',
        cell: (info) => {
          const v = info.getValue();
          return v != null ? v.toFixed(1) : '—';
        },
      }),
      sleepHelper.accessor('quality_score', {
        header: 'Qualité /100',
        cell: (info) => {
          const v = info.getValue();
          if (v == null) return '—';
          const color =
            v >= 80 ? '#34C759' : v >= 60 ? '#FF9500' : '#FF3B30';
          return (
            <span className="font-semibold" style={{ color }}>
              {Math.round(v)}
            </span>
          );
        },
      }),
      sleepHelper.accessor('bedtime', {
        header: 'Coucher',
        cell: (info) => info.getValue() ?? '—',
      }),
      sleepHelper.accessor('wake_time', {
        header: 'Réveil',
        cell: (info) => info.getValue() ?? '—',
      }),
    ],
    []
  );

  const table = useReactTable({
    data: Array.isArray(data) ? data : [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="card-surface rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-soma-border">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          Historique Sommeil
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-soma-border">
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className={cn(
                      'px-4 py-2.5 text-left text-soma-muted font-medium whitespace-nowrap',
                      header.column.getCanSort() && 'cursor-pointer hover:text-soma-text select-none'
                    )}
                  >
                    <div className="flex items-center gap-1.5">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() && (
                        <SortIcon sorted={header.column.getIsSorted()} />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(4)].map((_, i) => (
                <tr key={i} className="border-b border-soma-border/50">
                  {columns.map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-3 bg-soma-border rounded animate-pulse w-16" />
                    </td>
                  ))}
                </tr>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-6 text-center text-soma-muted">
                  {t('common.noData')}
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, idx) => (
                <tr
                  key={row.id}
                  className={cn(
                    'border-b border-soma-border/50 transition-colors',
                    idx % 2 === 0 ? 'bg-transparent' : 'bg-soma-bg/30',
                    'hover:bg-soma-accent/5'
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2.5 text-soma-text whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
