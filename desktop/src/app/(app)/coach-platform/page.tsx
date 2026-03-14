'use client';

import { useState } from 'react';
import { Users, AlertTriangle, UserPlus, Link2, RefreshCw } from 'lucide-react';
import { useEntitlement } from '@/hooks/use-entitlements';
import { FeatureCode } from '@/lib/entitlements';
import PaywallCard from '@/components/PaywallCard';
import {
  useCoachProfile,
  useCoachDashboard,
  useInvitations,
  useCreateInvitation,
  useCancelInvitation,
  useRegisterCoach,
} from '@/hooks/use-coach-platform';
import type { AthleteSummary, CoachInvitation } from '@/lib/api/coach-platform';
import Link from 'next/link';

export default function CoachPlatformPage() {
  const canUse = useEntitlement(FeatureCode.COACH_MODULE);

  if (!canUse) {
    return <PaywallCard feature={FeatureCode.COACH_MODULE} />;
  }

  return <CoachPlatformDashboard />;
}

function CoachPlatformDashboard() {
  const { data: profile, isLoading: profileLoading, error: profileError } = useCoachProfile();
  const { data: dashboard, isLoading: dashLoading, refetch } = useCoachDashboard();
  const [activeTab, setActiveTab] = useState<'athletes' | 'invitations'>('athletes');

  if (profileLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  // Not registered as coach yet
  if (profileError) {
    return <CoachRegistrationPrompt />;
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Espace Coach</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {profile?.name} · {profile?.athlete_count ?? 0} athlète{(profile?.athlete_count ?? 0) > 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
          title="Actualiser"
        >
          <RefreshCw className={`h-4 w-4 ${dashLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          icon={<Users className="h-5 w-5" />}
          label="Athlètes"
          value={String(dashboard?.total_athletes ?? 0)}
          color="blue"
        />
        <KpiCard
          icon={<AlertTriangle className="h-5 w-5" />}
          label="À risque"
          value={String(dashboard?.athletes_at_risk ?? 0)}
          color={dashboard && dashboard.athletes_at_risk > 0 ? 'orange' : 'green'}
        />
        <KpiCard
          icon={<Link2 className="h-5 w-5" />}
          label="Invitations"
          value="—"
          color="purple"
        />
        <KpiCard
          icon={<UserPlus className="h-5 w-5" />}
          label="Plan max"
          value={String(profile?.max_athletes ?? 50)}
          color="gray"
        />
      </div>

      {/* Tab switch */}
      <div className="flex gap-2 border-b border-border">
        <TabButton
          label="Mes athlètes"
          active={activeTab === 'athletes'}
          onClick={() => setActiveTab('athletes')}
        />
        <TabButton
          label="Invitations"
          active={activeTab === 'invitations'}
          onClick={() => setActiveTab('invitations')}
        />
      </div>

      {activeTab === 'athletes' && (
        <AthletesTab athletes={dashboard?.athletes_summary ?? []} loading={dashLoading} />
      )}
      {activeTab === 'invitations' && <InvitationsTab />}
    </div>
  );
}

// -- KPI Card

function KpiCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'blue' | 'orange' | 'green' | 'purple' | 'gray';
}) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    orange: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    green: 'bg-green-500/10 text-green-400 border-green-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    gray: 'bg-muted/50 text-muted-foreground border-border',
  };

  return (
    <div className={`rounded-xl border p-4 ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-xs font-medium">{label}</span></div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

// -- Tab Button

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'
      }`}
    >
      {label}
    </button>
  );
}

// -- Athletes Tab

function AthletesTab({
  athletes,
  loading,
}: {
  athletes: AthleteSummary[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 rounded-xl bg-muted/30 animate-pulse" />
        ))}
      </div>
    );
  }

  if (athletes.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <Users className="h-12 w-12 mx-auto mb-4 opacity-40" />
        <p className="font-medium">Aucun athlète pour l&apos;instant</p>
        <p className="text-sm mt-1">Créez une invitation pour ajouter votre premier athlète.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {athletes.map((athlete) => (
        <AthleteRow key={athlete.athlete_id} athlete={athlete} />
      ))}
    </div>
  );
}

function AthleteRow({ athlete }: { athlete: AthleteSummary }) {
  const riskColors = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  };

  return (
    <Link
      href={`/coach-platform/athlete/${athlete.athlete_id}`}
      className="flex items-center gap-4 p-4 rounded-xl border border-border bg-card hover:bg-muted/30 transition-colors"
    >
      {/* Risk indicator */}
      <div
        className={`h-3 w-3 rounded-full flex-shrink-0 ${riskColors[athlete.risk_level]}`}
        title={`Risque: ${athlete.risk_level}`}
      />

      {/* Name + alerts */}
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{athlete.athlete_name}</p>
        {athlete.alerts.length > 0 && (
          <p className="text-xs text-orange-400 truncate mt-0.5">
            ⚠ {athlete.alerts[0]}{athlete.alerts.length > 1 ? ` +${athlete.alerts.length - 1}` : ''}
          </p>
        )}
      </div>

      {/* Metrics */}
      <div className="flex gap-4 text-xs text-muted-foreground flex-shrink-0">
        {athlete.readiness_score != null && (
          <div className="text-center">
            <div className="font-bold text-foreground">{Math.round(athlete.readiness_score)}</div>
            <div>Readiness</div>
          </div>
        )}
        {athlete.days_since_last_session != null && (
          <div className="text-center">
            <div className="font-bold text-foreground">{athlete.days_since_last_session}j</div>
            <div>Inactivité</div>
          </div>
        )}
      </div>

      {/* Arrow */}
      <span className="text-muted-foreground">›</span>
    </Link>
  );
}

// -- Invitations Tab

function InvitationsTab() {
  const { data: invitations, isLoading } = useInvitations();
  const createMut = useCreateInvitation();
  const cancelMut = useCancelInvitation();
  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [newInvite, setNewInvite] = useState<CoachInvitation | null>(null);

  const handleCreate = async () => {
    const inv = await createMut.mutateAsync({
      invitee_email: email.trim() || undefined,
      message: message.trim() || undefined,
      expire_days: 7,
    });
    setNewInvite(inv);
    setShowForm(false);
    setEmail('');
    setMessage('');
  };

  const handleCancel = async (id: string) => {
    if (confirm('Annuler cette invitation ?')) {
      await cancelMut.mutateAsync(id);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    alert(`${label} copié !`);
  };

  return (
    <div className="space-y-4">
      {/* New invite success */}
      {newInvite && (
        <div className="p-4 rounded-xl border border-green-500/30 bg-green-500/10">
          <p className="font-semibold text-green-400 mb-2">✓ Invitation créée !</p>
          <div className="flex items-center gap-3">
            <code className="text-lg font-bold tracking-widest text-foreground">
              {newInvite.invite_code}
            </code>
            <button
              onClick={() => copyToClipboard(newInvite.invite_code, 'Code')}
              className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80 transition-colors"
            >
              Copier le code
            </button>
            <button
              onClick={() => copyToClipboard(newInvite.invite_link, 'Lien')}
              className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80 transition-colors"
            >
              Copier le lien
            </button>
            <button
              onClick={() => setNewInvite(null)}
              className="ml-auto text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      {showForm ? (
        <div className="p-4 rounded-xl border border-border bg-card space-y-3">
          <p className="font-medium">Nouvelle invitation</p>
          <input
            type="email"
            placeholder="Email de l'athlète (optionnel)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
          />
          <textarea
            placeholder="Message d'accompagnement..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={createMut.isPending}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {createMut.isPending ? 'Création...' : 'Créer'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded-lg border border-border text-sm"
            >
              Annuler
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-dashed border-border text-muted-foreground hover:text-foreground hover:border-primary transition-colors text-sm"
        >
          <UserPlus className="h-4 w-4" />
          Nouvelle invitation
        </button>
      )}

      {/* Invitation list */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-muted/30 animate-pulse" />
          ))}
        </div>
      ) : !invitations?.length ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          Aucune invitation pour l&apos;instant.
        </div>
      ) : (
        <div className="space-y-2">
          {invitations.map((inv) => (
            <InvitationRow
              key={inv.id}
              invitation={inv}
              onCancel={() => handleCancel(inv.id)}
              onCopyCode={() => copyToClipboard(inv.invite_code, 'Code')}
              onCopyLink={() => copyToClipboard(inv.invite_link, 'Lien')}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function InvitationRow({
  invitation,
  onCancel,
  onCopyCode,
  onCopyLink,
}: {
  invitation: CoachInvitation;
  onCancel: () => void;
  onCopyCode: () => void;
  onCopyLink: () => void;
}) {
  const statusColors: Record<string, string> = {
    pending: 'text-orange-400 bg-orange-500/10',
    accepted: 'text-green-400 bg-green-500/10',
    expired: 'text-red-400 bg-red-500/10',
    cancelled: 'text-muted-foreground bg-muted/30',
  };
  const statusLabels: Record<string, string> = {
    pending: 'En attente',
    accepted: 'Acceptée',
    expired: 'Expirée',
    cancelled: 'Annulée',
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl border border-border bg-card">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">
          {invitation.invitee_email ?? 'Lien ouvert'}
        </p>
        <p className="text-xs text-muted-foreground font-mono">{invitation.invite_code}</p>
      </div>
      <span
        className={`text-xs px-2 py-0.5 rounded-full ${statusColors[invitation.status] ?? ''}`}
      >
        {statusLabels[invitation.status] ?? invitation.status}
      </span>
      {invitation.status === 'pending' && (
        <div className="flex gap-1">
          <button
            onClick={onCopyCode}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            title="Copier le code"
          >
            <span className="text-xs">Code</span>
          </button>
          <button
            onClick={onCopyLink}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            title="Copier le lien"
          >
            <Link2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={onCancel}
            className="p-1.5 rounded hover:bg-muted text-red-400 hover:text-red-300 transition-colors"
            title="Annuler"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}

// -- Registration Prompt

function CoachRegistrationPrompt() {
  const register = useRegisterCoach();
  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    await register.mutateAsync({ name: name.trim(), bio: bio.trim() || undefined });
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="text-green-400 text-4xl">✓</div>
        <p className="font-medium">Profil coach créé ! Rechargez la page.</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-16 p-6 rounded-2xl border border-border bg-card space-y-4">
      <h2 className="text-xl font-bold">Créer votre profil coach</h2>
      <p className="text-muted-foreground text-sm">
        Vous n&apos;avez pas encore de profil coach. Renseignez votre nom pour commencer.
      </p>
      <input
        type="text"
        placeholder="Nom complet *"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full px-3 py-2 rounded-lg border border-border bg-background"
      />
      <textarea
        placeholder="Bio (optionnel)"
        value={bio}
        onChange={(e) => setBio(e.target.value)}
        rows={3}
        className="w-full px-3 py-2 rounded-lg border border-border bg-background resize-none"
      />
      <button
        onClick={handleSubmit}
        disabled={!name.trim() || register.isPending}
        className="w-full py-2 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50"
      >
        {register.isPending ? 'Création...' : 'Créer mon profil coach'}
      </button>
    </div>
  );
}
