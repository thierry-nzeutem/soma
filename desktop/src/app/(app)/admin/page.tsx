'use client';

import { Users, CreditCard, TrendingUp, AlertCircle, BarChart3, Star } from 'lucide-react';
import { useAdminStats, useFeatureUsageStats } from '@/hooks/use-admin';

const PLAN_COLORS: Record<string, string> = {
  free: 'bg-gray-500/20 text-gray-300',
  ai: 'bg-blue-500/20 text-blue-300',
  performance: 'bg-purple-500/20 text-purple-300',
};

const EVENT_LABELS: Record<string, string> = {
  feature_used: 'Feature utilisée',
  feature_denied: 'Feature refusée',
  upgrade_cta_clicked: 'CTA upgrade cliqué',
  checkout_started: 'Checkout démarré',
  checkout_completed: 'Checkout complété',
};

export default function AdminPage() {
  const { data: stats, isLoading, error } = useAdminStats();
  const { data: usageStats } = useFeatureUsageStats(7);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-soma-text">Administration</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="soma-card p-6 animate-pulse">
              <div className="h-4 bg-soma-surface-2 rounded w-1/2 mb-4" />
              <div className="h-8 bg-soma-surface-2 rounded w-1/3" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] gap-4">
        <AlertCircle className="w-12 h-12 text-red-400" />
        <p className="text-soma-text-muted">Accès refusé ou erreur serveur</p>
        <p className="text-xs text-soma-text-muted">Vous devez être superuser pour accéder à cette page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-soma-text mb-1">Administration SOMA</h1>
        <p className="text-soma-text-muted text-sm">Vue d&apos;ensemble de l&apos;application</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="soma-card p-6">
          <div className="flex items-center gap-3 mb-3">
            <Users className="w-5 h-5 text-soma-primary" />
            <span className="text-sm text-soma-text-muted font-medium">Utilisateurs totaux</span>
          </div>
          <p className="text-3xl font-bold text-soma-text">{stats?.total_users ?? 0}</p>
        </div>
        <div className="soma-card p-6">
          <div className="flex items-center gap-3 mb-3">
            <CreditCard className="w-5 h-5 text-green-400" />
            <span className="text-sm text-soma-text-muted font-medium">Abonnements actifs</span>
          </div>
          <p className="text-3xl font-bold text-soma-text">{stats?.active_paid_subscriptions ?? 0}</p>
        </div>
        <div className="soma-card p-6">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-soma-text-muted font-medium">Taux de conversion</span>
          </div>
          <p className="text-3xl font-bold text-soma-text">
            {stats && stats.total_users > 0
              ? `${Math.round((stats.active_paid_subscriptions / stats.total_users) * 100)}%`
              : '0%'}
          </p>
        </div>
      </div>

      {/* Plan distribution */}
      <div className="soma-card p-6">
        <h2 className="text-lg font-semibold text-soma-text mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Distribution des plans
        </h2>
        <div className="space-y-3">
          {stats?.plan_distribution?.map((item) => (
            <div key={`${item.plan_code}-${item.plan_status}`} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${PLAN_COLORS[item.plan_code] ?? 'bg-gray-500/20 text-gray-300'}`}>
                  {item.plan_code.toUpperCase()}
                </span>
                <span className="text-sm text-soma-text-muted">{item.plan_status}</span>
              </div>
              <span className="text-sm font-semibold text-soma-text">{item.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Feature usage last 7 days */}
      {usageStats && usageStats.length > 0 && (
        <div className="soma-card p-6">
          <h2 className="text-lg font-semibold text-soma-text mb-4 flex items-center gap-2">
            <Star className="w-5 h-5" />
            Usage features (7 derniers jours)
          </h2>
          <div className="space-y-2">
            {usageStats.slice(0, 10).map((item) => (
              <div key={`${item.feature_code}-${item.event_type}`} className="flex items-center justify-between py-2 border-b border-soma-border last:border-0">
                <div>
                  <span className="text-sm text-soma-text font-medium">{item.feature_code}</span>
                  <span className="text-xs text-soma-text-muted ml-2">
                    {EVENT_LABELS[item.event_type] ?? item.event_type}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-semibold text-soma-text">{item.count}</span>
                  <span className="text-xs text-soma-text-muted ml-1">({item.unique_users} users)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
