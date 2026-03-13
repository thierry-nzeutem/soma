/// Modèle Motion Intelligence Engine — LOT 11.
///
/// Correspond à GET /api/v1/vision/motion-summary.
library;

/// Profil de mouvement par exercice.
class ExerciseMotionProfile {
  final String exerciseType;
  final int sessionsAnalyzed;
  final double avgStability;
  final double avgAmplitude;
  final double avgQuality;
  final String stabilityTrend;  // "improving" | "stable" | "declining"
  final String amplitudeTrend;
  final String qualityTrend;
  final double qualityVariance;
  final String? lastSessionDate;
  final List<String> alerts;

  const ExerciseMotionProfile({
    required this.exerciseType,
    required this.sessionsAnalyzed,
    required this.avgStability,
    required this.avgAmplitude,
    required this.avgQuality,
    required this.stabilityTrend,
    required this.amplitudeTrend,
    required this.qualityTrend,
    required this.qualityVariance,
    this.lastSessionDate,
    required this.alerts,
  });

  factory ExerciseMotionProfile.fromJson(Map<String, dynamic> json) {
    return ExerciseMotionProfile(
      exerciseType: json['exercise_type'] as String? ?? '',
      sessionsAnalyzed: json['sessions_analyzed'] as int? ?? 0,
      avgStability: (json['avg_stability'] as num? ?? 0).toDouble(),
      avgAmplitude: (json['avg_amplitude'] as num? ?? 0).toDouble(),
      avgQuality: (json['avg_quality'] as num? ?? 0).toDouble(),
      stabilityTrend: json['stability_trend'] as String? ?? 'stable',
      amplitudeTrend: json['amplitude_trend'] as String? ?? 'stable',
      qualityTrend: json['quality_trend'] as String? ?? 'stable',
      qualityVariance: (json['quality_variance'] as num? ?? 0).toDouble(),
      lastSessionDate: json['last_session_date'] as String?,
      alerts: (json['alerts'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'exercise_type': exerciseType,
        'sessions_analyzed': sessionsAnalyzed,
        'avg_stability': avgStability,
        'avg_amplitude': avgAmplitude,
        'avg_quality': avgQuality,
        'stability_trend': stabilityTrend,
        'amplitude_trend': amplitudeTrend,
        'quality_trend': qualityTrend,
        'quality_variance': qualityVariance,
        'last_session_date': lastSessionDate,
        'alerts': alerts,
      };

  String get trendLabel => switch (qualityTrend) {
        'improving' => '↑',
        'declining' => '↓',
        _ => '→',
      };

  String get exerciseDisplayName => exerciseType
      .split('_')
      .map((w) => w.isEmpty ? '' : '${w[0].toUpperCase()}${w.substring(1)}')
      .join(' ');
}

/// Résultat complet de l'analyse Motion Intelligence.
class MotionIntelligenceResult {
  final String analysisDate;
  final int sessionsAnalyzed;
  final int daysAnalyzed;
  final double movementHealthScore;
  final double stabilityScore;
  final double mobilityScore;
  final double asymmetryScore;
  final String overallQualityTrend;
  final int consecutiveQualitySessions;
  final Map<String, ExerciseMotionProfile> exerciseProfiles;
  final List<String> recommendations;
  final List<String> riskAlerts;
  final double confidence;

  const MotionIntelligenceResult({
    required this.analysisDate,
    required this.sessionsAnalyzed,
    required this.daysAnalyzed,
    required this.movementHealthScore,
    required this.stabilityScore,
    required this.mobilityScore,
    required this.asymmetryScore,
    required this.overallQualityTrend,
    required this.consecutiveQualitySessions,
    required this.exerciseProfiles,
    required this.recommendations,
    required this.riskAlerts,
    required this.confidence,
  });

  factory MotionIntelligenceResult.fromJson(Map<String, dynamic> json) {
    final profilesJson =
        json['exercise_profiles'] as Map<String, dynamic>? ?? {};
    final profiles = profilesJson.map(
      (key, value) => MapEntry(
        key,
        ExerciseMotionProfile.fromJson(value as Map<String, dynamic>),
      ),
    );

    return MotionIntelligenceResult(
      analysisDate: json['analysis_date'] as String? ?? '',
      sessionsAnalyzed: json['sessions_analyzed'] as int? ?? 0,
      daysAnalyzed: json['days_analyzed'] as int? ?? 30,
      movementHealthScore:
          (json['movement_health_score'] as num? ?? 0).toDouble(),
      stabilityScore: (json['stability_score'] as num? ?? 0).toDouble(),
      mobilityScore: (json['mobility_score'] as num? ?? 0).toDouble(),
      asymmetryScore: (json['asymmetry_score'] as num? ?? 0).toDouble(),
      overallQualityTrend:
          json['overall_quality_trend'] as String? ?? 'stable',
      consecutiveQualitySessions:
          json['consecutive_quality_sessions'] as int? ?? 0,
      exerciseProfiles: profiles,
      recommendations: (json['recommendations'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      riskAlerts: (json['risk_alerts'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      confidence: (json['confidence'] as num? ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'analysis_date': analysisDate,
        'sessions_analyzed': sessionsAnalyzed,
        'days_analyzed': daysAnalyzed,
        'movement_health_score': movementHealthScore,
        'stability_score': stabilityScore,
        'mobility_score': mobilityScore,
        'asymmetry_score': asymmetryScore,
        'overall_quality_trend': overallQualityTrend,
        'consecutive_quality_sessions': consecutiveQualitySessions,
        'exercise_profiles':
            exerciseProfiles.map((k, v) => MapEntry(k, v.toJson())),
        'recommendations': recommendations,
        'risk_alerts': riskAlerts,
        'confidence': confidence,
      };

  String get trendLabel => switch (overallQualityTrend) {
        'improving' => '↑ Amélioration',
        'declining' => '↓ Déclin',
        _ => '→ Stable',
      };

  String get asymmetryRiskLevel {
    if (asymmetryScore < 15) return 'Faible';
    if (asymmetryScore < 35) return 'Modéré';
    return 'Élevé';
  }
}

/// Item d'historique Motion.
class MotionHistoryItem {
  final String snapshotDate;
  final double movementHealthScore;
  final double stabilityScore;
  final double mobilityScore;
  final double asymmetryScore;
  final String overallQualityTrend;
  final double confidence;

  const MotionHistoryItem({
    required this.snapshotDate,
    required this.movementHealthScore,
    required this.stabilityScore,
    required this.mobilityScore,
    required this.asymmetryScore,
    required this.overallQualityTrend,
    required this.confidence,
  });

  factory MotionHistoryItem.fromJson(Map<String, dynamic> json) {
    return MotionHistoryItem(
      snapshotDate: json['snapshot_date'] as String? ?? '',
      movementHealthScore:
          (json['movement_health_score'] as num? ?? 0).toDouble(),
      stabilityScore: (json['stability_score'] as num? ?? 0).toDouble(),
      mobilityScore: (json['mobility_score'] as num? ?? 0).toDouble(),
      asymmetryScore: (json['asymmetry_score'] as num? ?? 0).toDouble(),
      overallQualityTrend:
          json['overall_quality_trend'] as String? ?? 'stable',
      confidence: (json['confidence'] as num? ?? 0).toDouble(),
    );
  }
}
