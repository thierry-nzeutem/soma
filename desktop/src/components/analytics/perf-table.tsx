'use client';

import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import type { ApiPerformanceStatsResponse } from '@/lib/types/api';

type PerfRow = ApiPerformanceStatsResponse['endpoints'][number];

const helper = createColumnHelper<PerfRow>();

function SortIcon({ sorted }: { sorted: false | 'asc' | 'desc' }) {
  if (!sorted) return <ArrowUpDown size={11} className="text-soma-muted" />;
  return sorted === 'asc'
    ? <ArrowUp size={11} className="text-soma-accent" />
    : <ArrowDown size={11} className="text-soma-accent" />;
}

interface PerfTableProps {
  data: ApiPerformanceStatsResponse | undefined;
  isLoading: boolean;
}

export function PerfTable({ data, isLoading }: PerfTableProps) {
  const t = useTranslations();
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'request_count', desc: true },
  ]);

  const columns = useMemo(
    () => [
      helper.accessor('endpoint', {
        header: 'Endpoint',
        cell: (info) => (
          <span className="font-mono text-[10px] text-soma-text truncate block max-w-[200px]" title={info.getValue()}>
            {info.getValue()}
          </span>
        ),
      }),
      helper.accessor('method', {
        header: 'Méthode',
        cell: (info) => (
          <span
            className={cn(
              'px-1.5 py-0.5 rounded text-[10px] font-bold',
              info.getValue() === 'GET'
                ? 'bg-soma-success/10 text-soma-success'
                : info.getValue() === 'POST'
                ? 'bg-soma-warning/10 text-soma-warning'
                : 'bg-soma-border text-soma-muted'
            )}
          >
            {info.getValue()}
          </span>
        ),
      }),
      helper.accessor('request_count', {
        header: 'Requêtes',
        cell: (info) => {
          const row = info.row.original;
          const v = row.request_count ?? row.total_calls;
          return (
            <span className="tabular-nums">
              {v?.toLocaleString('fr-FR') ?? '—'}
            </span>
          );
        },
      }),
      helper.accessor('avg_latency_ms', {
        header: 'Moy (ms)',
        cell: (info) => {
          const row = info.row.original;
          const v = row.avg_latency_ms ?? row.avg_response_ms;
          const color =
            v == null ? undefined : v < 200 ? '#34C759' : v < 1000 ? '#FF9500' : '#FF3B30';
          return (
            <span className="tabular-nums font-semibold" style={{ color }}>
              {v != null ? Math.round(v) : '—'}
            </span>
          );
        },
      }),
      helper.accessor('p95_latency_ms', {
        header: 'P95 (ms)',
        cell: (info) => {
          const row = info.row.original;
          const v = row.p95_latency_ms ?? row.p95_response_ms;
          const color =
            v == null ? undefined : v < 500 ? '#34C759' : v < 2000 ? '#FF9500' : '#FF3B30';
          return (
            <span className="tabular-nums font-semibold" style={{ color }}>
              {v != null ? Math.round(v) : '—'}
            </span>
          );
        },
      }),
      helper.accessor('error_rate', {
        header: t('common.error'),
        cell: (info) => {
          const v = info.getValue();
          const pct = v != null ? (v * 100).toFixed(1) : null;
          const color =
            v == null ? undefined : v < 0.01 ? '#34C759' : v < 0.05 ? '#FF9500' : '#FF3B30';
          return (
            <span className="tabular-nums" style={{ color }}>
              {pct != null ? `${pct}%` : '—'}
            </span>
          );
        },
      }),
    ],
    []
  );

  const tableData: PerfRow[] = data?.endpoints ?? [];

  const table = useReactTable({
    data: tableData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="card-surface rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-soma-border">
        <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
          Performance API
        </p>
        {data?.buffer_size != null && (
          <span className="text-[10px] text-soma-muted">
            {data.buffer_size.toLocaleString('fr-FR')} métriques en mémoire
          </span>
        )}
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
                    <div className="flex items-center gap-1">
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
              [...Array(6)].map((_, i) => (
                <tr key={i} className="border-b border-soma-border/50">
                  {columns.map((_, j) => (
                    <td key={j} className="px-4 py-2.5">
                      <div className="h-3 bg-soma-border rounded animate-pulse" style={{ width: `${30 + j * 10}px` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-6 text-center text-soma-muted">
                  Aucune métrique de performance disponible.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, idx) => (
                <tr
                  key={row.id}
                  className={cn(
                    'border-b border-soma-border/50 transition-colors',
                    idx % 2 === 0 ? '' : 'bg-soma-bg/20',
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
