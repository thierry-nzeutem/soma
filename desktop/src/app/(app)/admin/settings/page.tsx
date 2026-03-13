'use client';

import { useState } from 'react';
import { Save, RefreshCw, Settings, Cpu, CreditCard } from 'lucide-react';
import { useAdminSettings, useUpdateSetting } from '@/hooks/use-admin';

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  ai: <Cpu className="w-4 h-4" />,
  billing: <CreditCard className="w-4 h-4" />,
  general: <Settings className="w-4 h-4" />,
};

const CATEGORY_LABELS: Record<string, string> = {
  ai: 'Intelligence Artificielle',
  billing: 'Facturation Stripe',
  general: 'Général',
};

const SENSITIVE_KEYS = new Set([
  'stripe_price_ai_monthly',
  'stripe_price_ai_yearly',
  'stripe_price_perf_monthly',
  'stripe_price_perf_yearly',
]);

export default function AdminSettingsPage() {
  const { data: settings, isLoading, refetch } = useAdminSettings();
  const updateSetting = useUpdateSetting();
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});

  const handleSave = async (key: string) => {
    const value = editValues[key] ?? '';
    await updateSetting.mutateAsync({ key, value: value || null });
    setSaved(prev => ({ ...prev, [key]: true }));
    setTimeout(() => setSaved(prev => ({ ...prev, [key]: false })), 2000);
  };

  // Group by category
  const grouped = settings?.reduce<Record<string, typeof settings>>((acc, s) => {
    (acc[s.category] ??= []).push(s);
    return acc;
  }, {}) ?? {};

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-soma-text">Paramètres</h1>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="soma-card h-24" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-soma-text mb-1">Paramètres système</h1>
          <p className="text-soma-text-muted text-sm">
            Variables de configuration runtime. Modifiables sans redémarrer le serveur.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 border border-soma-border rounded-lg text-sm text-soma-text-muted hover:text-soma-text transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Rafraîchir
        </button>
      </div>

      {Object.entries(grouped).map(([category, items]) => (
        <div key={category} className="soma-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-soma-text flex items-center gap-2">
            {CATEGORY_ICONS[category]}
            {CATEGORY_LABELS[category] ?? category}
          </h2>
          <div className="space-y-4">
            {items.map((setting) => {
              const currentValue = editValues[setting.key] ?? setting.value ?? '';
              const isSensitive = SENSITIVE_KEYS.has(setting.key);
              return (
                <div key={setting.key} className="grid grid-cols-1 gap-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-soma-text font-mono">
                      {setting.key}
                    </label>
                    {saved[setting.key] && (
                      <span className="text-xs text-green-400">&#x2713; Sauvegardé</span>
                    )}
                  </div>
                  {setting.description && (
                    <p className="text-xs text-soma-text-muted">{setting.description}</p>
                  )}
                  <div className="flex gap-2">
                    <input
                      type={isSensitive ? 'password' : 'text'}
                      value={currentValue}
                      onChange={e => setEditValues(prev => ({ ...prev, [setting.key]: e.target.value }))}
                      placeholder={isSensitive ? '••••••••••••' : setting.value ?? '(vide)'}
                      className="flex-1 px-3 py-2 bg-soma-surface border border-soma-border rounded-lg text-sm text-soma-text placeholder:text-soma-text-muted focus:outline-none focus:border-soma-primary font-mono"
                    />
                    <button
                      onClick={() => handleSave(setting.key)}
                      disabled={updateSetting.isPending || editValues[setting.key] === undefined}
                      className="flex items-center gap-1.5 px-3 py-2 bg-soma-primary text-white rounded-lg text-sm font-medium hover:opacity-80 transition-opacity disabled:opacity-40"
                    >
                      <Save className="w-3.5 h-3.5" />
                      Sauv.
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
