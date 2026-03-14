// Feature codes matching backend FeatureCode enum exactly
export const FeatureCode = {
  // Free tier
  BASIC_DASHBOARD: 'basic_dashboard',
  BASIC_HEALTH_METRICS: 'basic_health_metrics',
  LOCAL_AI_TIPS: 'local_ai_tips',

  // AI tier
  AI_COACH: 'ai_coach',
  DAILY_BRIEFING: 'daily_briefing',
  ADVANCED_INSIGHTS: 'advanced_insights',
  PDF_REPORTS: 'pdf_reports',
  ANOMALY_DETECTION: 'anomaly_detection',
  BIOLOGICAL_AGE: 'biological_age',

  // Performance tier
  READINESS_SCORE: 'readiness_score',
  INJURY_PREDICTION: 'injury_prediction',
  BIOMECHANICS_VISION: 'biomechanics_vision',
  ADVANCED_VO2MAX: 'advanced_vo2max',
  TRAINING_LOAD: 'training_load',

  // Coach Module (human coaching platform)
  COACH_MODULE: 'coach_module',
  COACH_ADVANCED_ANALYSIS: 'coach_advanced_analysis',
  COACH_REPORTS: 'coach_reports',
} as const;

export type FeatureCodeType = typeof FeatureCode[keyof typeof FeatureCode];

export interface EntitlementsData {
  plan_code: string;
  plan_status: string;
  features: string[];
  plan_expires_at?: string | null;
  trial_ends_at?: string | null;
  is_trial: boolean;
  is_expired: boolean;
}

export function hasFeature(
  data: EntitlementsData | undefined,
  feature: string
): boolean {
  if (!data) return false;
  return data.features.includes(feature);
}

export function getRequiredPlan(feature: string): 'ai' | 'performance' {
  const performanceFeatures = new Set<string>([
    FeatureCode.READINESS_SCORE,
    FeatureCode.INJURY_PREDICTION,
    FeatureCode.BIOMECHANICS_VISION,
    FeatureCode.ADVANCED_VO2MAX,
    FeatureCode.TRAINING_LOAD,
    FeatureCode.COACH_ADVANCED_ANALYSIS,
  ]);
  return performanceFeatures.has(feature) ? 'performance' : 'ai';
}

export function getPlanDisplayName(planCode: string): string {
  switch (planCode) {
    case 'ai': return 'SOMA AI';
    case 'performance': return 'SOMA Performance';
    default: return 'SOMA Free';
  }
}

export function getPlanBadgeColor(planCode: string): string {
  switch (planCode) {
    case 'ai': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'performance': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}
