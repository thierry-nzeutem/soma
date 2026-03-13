/// SOMA LOT 13 — Personalized Learning Profile model.
///
/// Maps to: GET /api/v1/learning/profile
import 'package:flutter/foundation.dart';

@immutable
class LearningProfile {
  final double? trueTdee;
  final double? estimatedMifflinTdee;
  final double metabolicEfficiency;
  final String metabolicTrend;
  final String recoveryProfile;
  final double recoveryFactor;
  final double avgRecoveryDays;
  final double trainingLoadTolerance;
  final double adaptationRate;
  final double optimalAcwr;
  final double carbResponse;
  final double proteinResponse;
  final double sleepRecoveryFactor;
  final double confidence;
  final int daysAnalyzed;
  final bool dataSufficient;
  final List<String> insights;

  const LearningProfile({
    this.trueTdee,
    this.estimatedMifflinTdee,
    required this.metabolicEfficiency,
    required this.metabolicTrend,
    required this.recoveryProfile,
    required this.recoveryFactor,
    required this.avgRecoveryDays,
    required this.trainingLoadTolerance,
    required this.adaptationRate,
    required this.optimalAcwr,
    required this.carbResponse,
    required this.proteinResponse,
    required this.sleepRecoveryFactor,
    required this.confidence,
    required this.daysAnalyzed,
    required this.dataSufficient,
    required this.insights,
  });

  factory LearningProfile.fromJson(Map<String, dynamic> json) {
    return LearningProfile(
      trueTdee: (json['true_tdee'] as num?)?.toDouble(),
      estimatedMifflinTdee: (json['estimated_mifflin_tdee'] as num?)?.toDouble(),
      metabolicEfficiency: (json['metabolic_efficiency'] as num?)?.toDouble() ?? 1.0,
      metabolicTrend: json['metabolic_trend'] as String? ?? 'stable',
      recoveryProfile: json['recovery_profile'] as String? ?? 'normal',
      recoveryFactor: (json['recovery_factor'] as num?)?.toDouble() ?? 1.0,
      avgRecoveryDays: (json['avg_recovery_days'] as num?)?.toDouble() ?? 1.5,
      trainingLoadTolerance: (json['training_load_tolerance'] as num?)?.toDouble() ?? 50.0,
      adaptationRate: (json['adaptation_rate'] as num?)?.toDouble() ?? 0.5,
      optimalAcwr: (json['optimal_acwr'] as num?)?.toDouble() ?? 1.1,
      carbResponse: (json['carb_response'] as num?)?.toDouble() ?? 0.0,
      proteinResponse: (json['protein_response'] as num?)?.toDouble() ?? 0.0,
      sleepRecoveryFactor: (json['sleep_recovery_factor'] as num?)?.toDouble() ?? 1.0,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      daysAnalyzed: (json['days_analyzed'] as num?)?.toInt() ?? 0,
      dataSufficient: json['data_sufficient'] as bool? ?? false,
      insights: (json['insights'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() => {
        'true_tdee': trueTdee,
        'estimated_mifflin_tdee': estimatedMifflinTdee,
        'metabolic_efficiency': metabolicEfficiency,
        'metabolic_trend': metabolicTrend,
        'recovery_profile': recoveryProfile,
        'recovery_factor': recoveryFactor,
        'avg_recovery_days': avgRecoveryDays,
        'training_load_tolerance': trainingLoadTolerance,
        'adaptation_rate': adaptationRate,
        'optimal_acwr': optimalAcwr,
        'carb_response': carbResponse,
        'protein_response': proteinResponse,
        'sleep_recovery_factor': sleepRecoveryFactor,
        'confidence': confidence,
        'days_analyzed': daysAnalyzed,
        'data_sufficient': dataSufficient,
        'insights': insights,
      };

  bool get isFastMetabolizer => metabolicEfficiency > 1.05;
  bool get isSlowMetabolizer => metabolicEfficiency < 0.95;
  bool get isFastRecoverer => recoveryProfile == 'fast';
  bool get isSlowRecoverer => recoveryProfile == 'slow';
  bool get hasGoodCarbResponse => carbResponse > 0.2;

  String get metabolicEfficiencyLabel {
    if (isFastMetabolizer) return 'Rapide';
    if (isSlowMetabolizer) return 'Lent';
    return 'Normal';
  }

  String get recoveryProfileLabel => switch (recoveryProfile) {
        'fast' => 'Rapide',
        'slow' => 'Lente',
        _ => 'Normale',
      };
}

@immutable
class LearningInsight {
  final String insightType;
  final String title;
  final String description;
  final double confidence;
  final bool actionable;

  const LearningInsight({
    required this.insightType,
    required this.title,
    required this.description,
    required this.confidence,
    required this.actionable,
  });

  factory LearningInsight.fromJson(Map<String, dynamic> json) {
    return LearningInsight(
      insightType: json['insight_type'] as String? ?? 'general',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      actionable: json['actionable'] as bool? ?? true,
    );
  }
}
