'use client';

import { useState } from 'react';
import { Search, Shield, User as UserIcon } from 'lucide-react';
import { useAdminUsers, useUpdateUserPlan } from '@/hooks/use-admin';

const PLAN_OPTIONS = ['free', 'ai', 'performance'];
const PLAN_COLORS: Record<string, string> = {
  free: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
  ai: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  performance: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
};
const STATUS_COLORS: Record<string, string> = {
  active: 'text-green-400',
  past_due: 'text-yellow-400',
  inactive: 'text-red-400',
};

export default function AdminUsersPage() {
  const [search, setSearch] = useState('');
  const [filterPlan, setFilterPlan] = useState('');
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [newPlan, setNewPlan] = useState('free');

  const { data: users, isLoading } = useAdminUsers({
    search: search || undefined,
    plan_code: filterPlan || undefined,
  });
  const updatePlan = useUpdateUserPlan();

  const handlePlanUpdate = async (userId: string) => {
    await updatePlan.mutateAsync({ userId, plan: { plan_code: newPlan } });
    setEditingUser(null);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-soma-text mb-1">Utilisateurs</h1>
        <p className="text-soma-text-muted text-sm">Gérez les plans et accès des utilisateurs</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soma-text-muted" />
          <input
            type="text"
            placeholder="Rechercher par nom ou email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-soma-surface-2 border border-soma-border rounded-lg text-sm text-soma-text placeholder:text-soma-text-muted focus:outline-none focus:border-soma-primary"
          />
        </div>
        <select
          value={filterPlan}
          onChange={e => setFilterPlan(e.target.value)}
          className="px-3 py-2 bg-soma-surface-2 border border-soma-border rounded-lg text-sm text-soma-text focus:outline-none focus:border-soma-primary"
        >
          <option value="">Tous les plans</option>
          {PLAN_OPTIONS.map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
        </select>
      </div>

      {/* Users table */}
      <div className="soma-card overflow-hidden">
        <table className="w-full">
          <thead className="border-b border-soma-border">
            <tr>
              <th className="text-left text-xs text-soma-text-muted font-medium px-4 py-3">Utilisateur</th>
              <th className="text-left text-xs text-soma-text-muted font-medium px-4 py-3">Plan</th>
              <th className="text-left text-xs text-soma-text-muted font-medium px-4 py-3">Statut</th>
              <th className="text-left text-xs text-soma-text-muted font-medium px-4 py-3">Stripe</th>
              <th className="text-left text-xs text-soma-text-muted font-medium px-4 py-3">Inscrit le</th>
              <th className="text-left text-xs text-soma-text-muted font-medium px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-soma-text-muted text-sm">
                  Chargement...
                </td>
              </tr>
            )}
            {users?.map((user) => (
              <tr key={user.id} className="border-b border-soma-border/50 hover:bg-soma-surface-2/50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {user.is_superuser ? (
                      <Shield className="w-4 h-4 text-yellow-400 shrink-0" />
                    ) : (
                      <UserIcon className="w-4 h-4 text-soma-text-muted shrink-0" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-soma-text">{user.username}</p>
                      {user.email && <p className="text-xs text-soma-text-muted">{user.email}</p>}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {editingUser === user.id ? (
                    <select
                      value={newPlan}
                      onChange={e => setNewPlan(e.target.value)}
                      className="px-2 py-1 bg-soma-surface border border-soma-primary rounded text-xs text-soma-text"
                    >
                      {PLAN_OPTIONS.map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                    </select>
                  ) : (
                    <span className={`text-xs px-2 py-1 rounded-full border font-medium ${PLAN_COLORS[user.plan_code] ?? PLAN_COLORS.free}`}>
                      {user.plan_code.toUpperCase()}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${STATUS_COLORS[user.plan_status] ?? 'text-soma-text-muted'}`}>
                    {user.plan_status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-soma-text-muted font-mono">
                    {user.stripe_customer_id ? user.stripe_customer_id.slice(0, 12) + '...' : '—'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-soma-text-muted">
                    {new Date(user.created_at).toLocaleDateString('fr-FR')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {editingUser === user.id ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handlePlanUpdate(user.id)}
                        disabled={updatePlan.isPending}
                        className="text-xs px-2 py-1 bg-soma-primary text-white rounded hover:opacity-80 transition-opacity disabled:opacity-50"
                      >
                        Sauv.
                      </button>
                      <button
                        onClick={() => setEditingUser(null)}
                        className="text-xs px-2 py-1 border border-soma-border text-soma-text-muted rounded hover:text-soma-text transition-colors"
                      >
                        Ann.
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => { setEditingUser(user.id); setNewPlan(user.plan_code); }}
                      className="text-xs px-2 py-1 border border-soma-border text-soma-text-muted rounded hover:text-soma-text hover:border-soma-primary transition-colors"
                    >
                      Modifier plan
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
