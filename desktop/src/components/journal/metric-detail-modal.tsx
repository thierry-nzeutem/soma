'use client';

import { useState } from 'react';
import {
  X, TrendingUp, TrendingDown, Minus, Info, Target, Lightbulb,
  ChevronDown, ChevronUp, Plus, Table2, BarChart3, Pencil, Check, Loader2,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { useTranslations } from '@/lib/i18n/config';
import { safeDateFormat } from '@/lib/utils';
import apiClient from '@/lib/api/client';

/* ─── Types ─────────────────────────────────────────────────────────────────── */

export interface MetricInfo {
  key: string;
  title: string;
  unit: string;
  description: string;
  goodRange: string;
  tips: string;
  color: string;
  data: { date: string; value: number | null | undefined }[];
}

interface MetricDetailModalProps {
  metric: MetricInfo | null;
  onClose: () => void;
  days: number;
  onDaysChange: (d: number) => void;
  onDataAdded?: () => void;
}

type ModalTab = 'chart' | 'table' | 'add';

/* ─── Helpers ───────────────────────────────────────────────────────────────── */

function computeStats(data: { value: number | null | undefined }[]) {
  const values = data.map((d) => d.value).filter((v): v is number => v != null && Number.isFinite(v));
  if (values.length === 0) return null;
  const avg = values.reduce((s, v) => s + v, 0) / values.length;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const latest = values[values.length - 1];
  const n = Math.min(3, Math.floor(values.length / 2));
  if (n === 0) return { avg, min, max, latest, trend: 'stable' as const };
  const first3 = values.slice(0, n).reduce((s, v) => s + v, 0) / n;
  const last3 = values.slice(-n).reduce((s, v) => s + v, 0) / n;
  const diff = last3 - first3;
  const threshold = avg * 0.03;
  const trend: 'improving' | 'stable' | 'declining' =
    diff > threshold ? 'improving' : diff < -threshold ? 'declining' : 'stable';
  return { avg, min, max, latest, trend };
}

async function saveMetricEntry(key: string, value: number, date: string) {
  const today = date || new Date().toISOString().slice(0, 10);
  switch (key) {
    case 'weight_kg':
      return apiClient.post('/api/v1/body-metrics', { weight_kg: value, measured_at: today });
    case 'steps':
      return apiClient.post('/api/v1/body-metrics', { steps_count: value, measured_at: today });
    case 'water_ml':
      return apiClient.post('/api/v1/hydration/log', { amount_ml: value, logged_at: today + 'T12:00:00' });
    case 'calories_consumed':
      return apiClient.post('/api/v1/nutrition/entries', { name: 'Saisie manuelle', calories: value, meal_type: 'snack' });
    case 'protein_g':
      return apiClient.post('/api/v1/nutrition/entries', { name: 'Saisie manuelle', protein_g: value, meal_type: 'snack' });
    case 'duration_hours':
      return apiClient.post('/api/v1/sleep', {
        start_at: today + 'T23:00:00', end_at: today + 'T23:00:00',
        duration_minutes: Math.round(value * 60), perceived_quality: 3,
      });
    default:
      return apiClient.post('/api/v1/body-metrics', { [key]: value, measured_at: today });
  }
}

/* ─── Sub-components ────────────────────────────────────────────────────────── */

const ChartTooltip = ({ active, payload, label, unit }: { active?: boolean; payload?: any[]; label?: string; unit?: string }) => {
  if (!active || !payload?.length) return null;
  const val = payload[0]?.value;
  return (
    <div className="bg-soma-surface border border-soma-border rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="text-soma-muted mb-1">{label}</p>
      <p className="font-semibold text-soma-accent">
        {val != null ? `${Number(val).toFixed(1)} ${unit || ''}` : '\u2014'}
      </p>
    </div>
  );
};

function StatCard({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="bg-soma-bg rounded-xl border border-soma-border p-3 text-center">
      <p className="text-[10px] text-soma-muted uppercase tracking-wider">{label}</p>
      <p className="text-lg font-bold text-soma-text mt-0.5 tabular-nums">{value}</p>
      <p className="text-[10px] text-soma-muted">{unit}</p>
    </div>
  );
}


function CollapsibleSection({ icon: Icon, title, content, color, defaultOpen = false }: {
  icon: React.ElementType; title: string; content: string; color: string; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (!content) return null;
  return (
    <div className="rounded-xl border border-soma-border bg-soma-bg/50 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between p-4 hover:bg-soma-bg/80 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} className={color} />
          <h3 className="text-sm font-semibold text-soma-text">{title}</h3>
        </div>
        {open ? <ChevronUp size={14} className="text-soma-muted" /> : <ChevronDown size={14} className="text-soma-muted" />}
      </button>
      {open && (
        <div className="px-4 pb-4 -mt-1">
          <p className="text-sm text-soma-muted leading-relaxed">{content}</p>
        </div>
      )}
    </div>
  );
}

function DataTable({ data, unit, t }: { data: { date: string; value: number | null | undefined }[]; unit: string; t: (k: string) => string }) {
  const sorted = [...data].filter((d) => d.value != null).reverse();
  if (sorted.length === 0) return <p className="text-sm text-soma-muted text-center py-4">{t('common.noData')}</p>;
  return (
    <div className="max-h-[300px] overflow-y-auto rounded-xl border border-soma-border">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-soma-surface">
          <tr className="border-b border-soma-border">
            <th className="text-left px-3 py-2 text-soma-muted font-medium">{t('journal.date')}</th>
            <th className="text-right px-3 py-2 text-soma-muted font-medium">{t('journal.value')} ({unit})</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d, i) => (
            <tr key={i} className="border-b border-soma-border/50 hover:bg-soma-bg/50">
              <td className="px-3 py-2 text-soma-text">{safeDateFormat(d.date, 'dd MMM yyyy')}</td>
              <td className="px-3 py-2 text-right tabular-nums font-semibold text-soma-text">
                {d.value != null ? Number(d.value).toFixed(1) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AddEntryForm({ metricKey, unit, onSave, t }: {
  metricKey: string; unit: string; onSave: (value: number, date: string) => Promise<void>; t: (k: string) => string;
}) {
  const [value, setValue] = useState('');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  async function handleSave() {
    const num = parseFloat(value);
    if (isNaN(num)) return;
    setSaving(true);
    setError('');
    try {
      await onSave(num, date);
      setSaved(true);
      setValue('');
      setTimeout(() => setSaved(false), 2000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || t('common.error'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-soma-border bg-soma-bg/50 p-4 space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Pencil size={14} className="text-soma-accent" />
        <h3 className="text-sm font-semibold text-soma-text">{t('journal.addNewEntry')}</h3>
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <label className="text-[10px] text-soma-muted uppercase tracking-wider block mb-1">{t('journal.date')}</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-soma-surface border border-soma-border rounded-lg text-soma-text focus:outline-none focus:border-soma-accent"
          />
        </div>
        <div className="flex-1">
          <label className="text-[10px] text-soma-muted uppercase tracking-wider block mb-1">{t('journal.value')} ({unit})</label>
          <input
            type="number"
            step="0.1"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={t('journal.enterValue')}
            className="w-full px-3 py-2 text-xs bg-soma-surface border border-soma-border rounded-lg text-soma-text focus:outline-none focus:border-soma-accent"
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !value}
          className="px-4 py-2 text-xs font-medium bg-soma-accent text-soma-bg rounded-lg disabled:opacity-50 hover:bg-soma-accent/90 transition-colors flex items-center gap-1.5"
        >
          {saving ? <Loader2 size={12} className="animate-spin" /> : saved ? <Check size={12} /> : <Plus size={12} />}
          {saved ? t('journal.dataSaved') : t('common.save')}
        </button>
        {error && <p className="text-xs text-soma-danger">{error}</p>}
      </div>
    </div>
  );
}


/* --- Main Modal --------------------------------------------------------------- */

export function MetricDetailModal({ metric, onClose, days, onDaysChange, onDataAdded }: MetricDetailModalProps) {
  const t = useTranslations();
  const [activeTab, setActiveTab] = useState<ModalTab>('chart');

  if (!metric) return null;

  const stats = computeStats(metric.data);
  const chartData = metric.data.map((d) => ({ date: safeDateFormat(d.date, 'd MMM', ''), value: d.value }));

  const TrendIcon = stats?.trend === 'improving' ? TrendingUp : stats?.trend === 'declining' ? TrendingDown : Minus;
  const trendColor = stats?.trend === 'improving' ? 'text-soma-success' : stats?.trend === 'declining' ? 'text-soma-danger' : 'text-soma-muted';
  const trendLabel = stats?.trend === 'improving' ? t('journal.improving') : stats?.trend === 'declining' ? t('journal.declining') : t('journal.stable');

  const periodOptions = [7, 30, 90];

  const metricKey = metric.key;

  async function handleAddEntry(value: number, date: string) {
    await saveMetricEntry(metricKey, value, date);
    onDataAdded?.();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div className="card-surface w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 pb-3">
          <div>
            <h2 className="text-lg font-bold text-soma-text">{metric.title}</h2>
            <p className="text-sm text-soma-muted">{t('journal.metricDetail')}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-soma-surface transition-colors">
            <X size={18} className="text-soma-muted" />
          </button>
        </div>

        {/* Period selector + Tabs */}
        <div className="px-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
          <div className="flex gap-1.5">
            {periodOptions.map((p) => (
              <button
                key={p}
                onClick={() => onDaysChange(p)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  days === p
                    ? 'bg-soma-accent text-soma-bg'
                    : 'bg-soma-bg text-soma-muted hover:text-soma-text border border-soma-border'
                }`}
              >
                {p}j
              </button>
            ))}
          </div>
          <div className="flex gap-1 bg-soma-bg rounded-lg p-0.5 border border-soma-border">
            <button onClick={() => setActiveTab('chart')} className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${activeTab === 'chart' ? 'bg-soma-surface text-soma-text shadow-sm' : 'text-soma-muted hover:text-soma-text'}`}>
              <BarChart3 size={12} /> {t('journal.chartView')}
            </button>
            <button onClick={() => setActiveTab('table')} className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${activeTab === 'table' ? 'bg-soma-surface text-soma-text shadow-sm' : 'text-soma-muted hover:text-soma-text'}`}>
              <Table2 size={12} /> {t('journal.tableView')}
            </button>
            <button onClick={() => setActiveTab('add')} className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${activeTab === 'add' ? 'bg-soma-surface text-soma-text shadow-sm' : 'text-soma-muted hover:text-soma-text'}`}>
              <Plus size={12} /> {t('journal.addEntry')}
            </button>
          </div>
        </div>

        <div className="px-5 pb-5 space-y-4">
          {activeTab === 'chart' && (
            <>
              <div className="rounded-xl bg-soma-bg border border-soma-border p-4">
                <div style={{ height: '200px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                      <defs>
                        <linearGradient id="detail-grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={metric.color} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={metric.color} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--soma-border)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fill: 'var(--soma-muted)', fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                      <YAxis tick={{ fill: 'var(--soma-muted)', fontSize: 11 }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
                      {stats && <ReferenceLine y={stats.avg} stroke="var(--soma-muted)" strokeDasharray="4 4" strokeOpacity={0.6} />}
                      <Tooltip content={(props) => <ChartTooltip {...(props as any)} unit={metric.unit} />} />
                      <Area type="monotone" dataKey="value" stroke={metric.color} strokeWidth={2.5} fill="url(#detail-grad)" dot={false} activeDot={{ r: 5, strokeWidth: 0, fill: metric.color }} connectNulls />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
              {stats && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatCard label={t('journal.avg')} value={stats.avg.toFixed(1)} unit={metric.unit} />
                  <StatCard label={t('journal.min')} value={stats.min.toFixed(1)} unit={metric.unit} />
                  <StatCard label={t('journal.max')} value={stats.max.toFixed(1)} unit={metric.unit} />
                  <div className="bg-soma-bg rounded-xl border border-soma-border p-3 text-center">
                    <p className="text-[10px] text-soma-muted uppercase tracking-wider">{t('journal.trend')}</p>
                    <div className="flex items-center justify-center gap-1.5 mt-1">
                      <TrendIcon size={16} className={trendColor} />
                      <span className={`text-sm font-semibold ${trendColor}`}>{trendLabel}</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === 'table' && (
            <DataTable data={metric.data} unit={metric.unit} t={t} />
          )}

          {activeTab === 'add' && (
            <AddEntryForm metricKey={metric.key} unit={metric.unit} onSave={handleAddEntry} t={t} />
          )}

          <div className="space-y-2">
            <CollapsibleSection icon={Info} title={t('journal.whatItMeans')} content={metric.description} color="text-blue-500" defaultOpen={activeTab === 'chart'} />
            <CollapsibleSection icon={Target} title={t('journal.recommendations')} content={metric.goodRange} color="text-soma-accent" />
            <CollapsibleSection icon={Lightbulb} title={t('journal.practicalTips')} content={metric.tips} color="text-yellow-500" />
          </div>
        </div>
      </div>
    </div>
  );
}
