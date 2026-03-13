'use client';

import { Lock, Rocket } from 'lucide-react';
import { getPlanDisplayName, getRequiredPlan } from '@/lib/entitlements';

interface PaywallCardProps {
  feature: string;
  requiredPlan?: 'ai' | 'performance';
  title?: string;
  description?: string;
}

const FEATURE_LABELS: Record<string, string> = {
  ai_coach: 'Coach IA personnalisé',
  daily_briefing: 'Bilan matinal IA',
  pdf_reports: 'Rapports santé PDF',
  advanced_insights: 'Insights avancés',
  readiness_score: 'Score Readiness',
  injury_prediction: 'Prévention blessures',
  biomechanics_vision: 'Biomécanique Vision IA',
  advanced_vo2max: 'VO2max avancé',
  training_load: "Charge d'entraînement",
  biological_age: 'Âge biologique',
  anomaly_detection: "Détection d'anomalies",
};

export default function PaywallCard({
  feature,
  requiredPlan,
  title,
  description,
}: PaywallCardProps) {
  const plan = requiredPlan ?? getRequiredPlan(feature);
  const planName = getPlanDisplayName(plan);
  const featureLabel = title ?? FEATURE_LABELS[feature] ?? 'Fonctionnalité premium';
  const planColor = plan === 'performance' ? 'purple' : 'blue';

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
      <div
        className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 ${
          planColor === 'purple'
            ? 'bg-purple-500/10 border border-purple-500/20'
            : 'bg-blue-500/10 border border-blue-500/20'
        }`}
      >
        <Lock
          className={`w-8 h-8 ${planColor === 'purple' ? 'text-purple-400' : 'text-blue-400'}`}
        />
      </div>

      <h2 className="text-2xl font-bold text-foreground mb-3">
        {featureLabel}
      </h2>

      <p className="text-muted-foreground max-w-md mb-2">
        {description ?? `Cette fonctionnalité est disponible avec le plan`}
      </p>

      <p className={`font-semibold mb-8 ${planColor === 'purple' ? 'text-purple-400' : 'text-blue-400'}`}>
        {planName}
      </p>

      <div className="flex flex-col sm:flex-row gap-3">
        <a
          href="/dashboard"
          className={`inline-flex items-center gap-2 px-6 py-3 rounded-lg text-white font-medium transition-colors ${
            planColor === 'purple'
              ? 'bg-purple-600 hover:bg-purple-700'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          <Rocket className="w-4 h-4" />
          Passer au plan {planName}
        </a>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-border hover:bg-muted text-foreground font-medium transition-colors"
        >
          Retour au dashboard
        </a>
      </div>

      <div
        className={`mt-8 p-4 rounded-lg max-w-sm ${
          planColor === 'purple'
            ? 'border border-purple-500/20 bg-purple-500/5'
            : 'border border-blue-500/20 bg-blue-500/5'
        }`}
      >
        <p className="text-sm text-muted-foreground">
          <span className={`font-medium ${planColor === 'purple' ? 'text-purple-400' : 'text-blue-400'}`}>
            {planName}
          </span>{' '}
          inclut également :
          {plan === 'ai' && ' Coach IA, Bilan matinal, Rapports PDF, Insights avancés.'}
          {plan === 'performance' && ' tout le plan AI + Readiness, Prédiction blessures, VO2max avancé.'}
        </p>
      </div>
    </div>
  );
}
