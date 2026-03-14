'use client';

import { use } from 'react';
import { ArrowLeft, CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';
import Link from 'next/link';
import { useAthleteFullProfile, useAthleteRecommendations } from '@/hooks/use-coach-platform';
import type { CoachRecommendation } from '@/lib/api/coach-platform';

export default function AthleteDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: profile, isLoading } = useAthleteFullProfile(id);
  const { data: recommendations } = useAthleteRecommendations(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <p>Profil non trouvé.</p>
        <Link href="/coach-platform" className="text-primary hover:underline text-sm mt-2 block">
          ← Retour au dashboard
        </Link>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    active: 'text-green-400',
    paused: 'text-orange-400',
    archived: 'text-muted-foreground',
    revoked: 'text-red-400',
  };

  const statusLabels: Record<string, string> = {
    active: 'Actif',
    paused: 'En pause',
    archived: 'Archivé',
    revoked: 'Révoqué',
  };

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-4xl">
      {/* Back link */}
      <Link
        href="/coach-platform"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Dashboard coach
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{profile.display_name}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {profile.sport ?? 'Sport non renseigné'}
            {profile.goal ? ` · ${profile.goal}` : ''}
          </p>
        </div>
        <span className={`text-sm font-medium ${statusColors[profile.link_status] ?? ''}`}>
          {statusLabels[profile.link_status] ?? profile.link_status}
        </span>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Identity */}
        <InfoCard title="Identité">
          {profile.age != null && <InfoRow label="Âge" value={`${profile.age} ans`} />}
          {profile.sex && <InfoRow label="Sexe" value={sexLabel(profile.sex)} />}
          {profile.height_cm != null && (
            <InfoRow label="Taille" value={`${profile.height_cm.toFixed(0)} cm`} />
          )}
          {profile.activity_level && (
            <InfoRow label="Activité" value={activityLabel(profile.activity_level)} />
          )}
          {profile.fitness_level && (
            <InfoRow label="Niveau" value={fitnessLabel(profile.fitness_level)} />
          )}
        </InfoCard>

        {/* Relation */}
        <InfoCard title="Relation coaching">
          <InfoRow label="Statut" value={statusLabels[profile.link_status] ?? profile.link_status} />
          {profile.linked_at && (
            <InfoRow label="Depuis" value={formatDate(profile.linked_at)} />
          )}
          {profile.relationship_notes && (
            <InfoRow label="Notes" value={profile.relationship_notes} />
          )}
          <InfoRow label="Notes rédigées" value={String(profile.recent_notes_count)} />
          <InfoRow label="Recommandations actives" value={String(profile.pending_recommendations_count)} />
        </InfoCard>
      </div>

      {/* Recommendations */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Recommandations</h2>
        {!recommendations?.length ? (
          <div className="text-center py-8 text-muted-foreground text-sm border border-dashed border-border rounded-xl">
            Aucune recommandation pour cet athlète.
          </div>
        ) : (
          <div className="space-y-2">
            {recommendations.map((rec) => (
              <RecommendationRow key={rec.id} rec={rec} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// -- Recommendation Row

function RecommendationRow({ rec }: { rec: CoachRecommendation }) {
  const priorityColors: Record<string, string> = {
    urgent: 'text-red-400',
    high: 'text-orange-400',
    normal: 'text-blue-400',
    low: 'text-muted-foreground',
  };

  const StatusIcon = {
    pending: <Clock className="h-4 w-4 text-orange-400" />,
    in_progress: <AlertCircle className="h-4 w-4 text-blue-400" />,
    completed: <CheckCircle className="h-4 w-4 text-green-400" />,
    dismissed: <XCircle className="h-4 w-4 text-muted-foreground" />,
  }[rec.status];

  return (
    <div className="flex items-start gap-3 p-4 rounded-xl border border-border bg-card">
      <div className="mt-0.5">{StatusIcon}</div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{rec.title}</p>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{rec.description}</p>
        {rec.target_date && (
          <p className="text-xs text-muted-foreground mt-1">
            Échéance : {formatDate(rec.target_date)}
          </p>
        )}
      </div>
      <span className={`text-xs font-medium flex-shrink-0 ${priorityColors[rec.priority] ?? ''}`}>
        {recTypeLabel(rec.rec_type)}
      </span>
    </div>
  );
}

// -- Helper components

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-2">
      <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 text-sm">
      <span className="text-muted-foreground w-32 flex-shrink-0">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

// -- Helpers

function sexLabel(sex: string): string {
  return { male: 'Homme', female: 'Femme' }[sex] ?? sex;
}

function activityLabel(level: string): string {
  return {
    sedentary: 'Sédentaire',
    light: 'Légèrement actif',
    moderate: 'Modérément actif',
    active: 'Actif',
    very_active: 'Très actif',
  }[level] ?? level;
}

function fitnessLabel(level: string): string {
  return {
    beginner: 'Débutant',
    intermediate: 'Intermédiaire',
    advanced: 'Avancé',
    athlete: 'Athlète',
  }[level] ?? level;
}

function recTypeLabel(type: string): string {
  return {
    training: 'Entraînement',
    nutrition: 'Nutrition',
    recovery: 'Récupération',
    medical: 'Médical',
    lifestyle: 'Mode de vie',
    mental: 'Mental',
    general: 'Général',
  }[type] ?? type;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
