/// SOMA LOT 15 — Injury Risk model.
///
/// Maps to: GET /api/v1/injury/risk
import 'package:flutter/foundation.dart';

@immutable
class RiskZone {
  final String bodyPart;
  final String riskLevel;
  final double riskScore;
  final List<String> contributingFactors;
  final List<String> recommendations;

  const RiskZone({
    required this.bodyPart,
    required this.riskLevel,
    required this.riskScore,
    required this.contributingFactors,
    required this.recommendations,
  });

  factory RiskZone.fromJson(Map<String, dynamic> json) {
    return RiskZone(
      bodyPart: json['body_part'] as String? ?? '',
      riskLevel: json['risk_level'] as String? ?? 'minimal',
      riskScore: (json['risk_score'] as num?)?.toDouble() ?? 0.0,
      contributingFactors: (json['contributing_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  String get bodyPartLabel => switch (bodyPart) {
        'lower_back' => 'Dos bas',
        'knee' => 'Genou',
        'shoulder' => 'Épaule',
        'ankle' => 'Cheville',
        'hip' => 'Hanche',
        'spine' => 'Colonne',
        _ => bodyPart,
      };
}

@immutable
class InjuryRisk {
  final String analysisDate;
  final double injuryRiskScore;
  final String injuryRiskCategory;
  final double acwrRiskScore;
  final double fatigueRiskScore;
  final double asymmetryRiskScore;
  final double sleepRiskScore;
  final double monotonyRiskScore;
  final List<RiskZone> riskZones;
  final List<String> movementCompensationPatterns;
  final bool fatigueCompensationRisk;
  final bool trainingOverloadRisk;
  final List<String> recommendations;
  final List<String> immediateActions;
  final double confidence;

  const InjuryRisk({
    required this.analysisDate,
    required this.injuryRiskScore,
    required this.injuryRiskCategory,
    required this.acwrRiskScore,
    required this.fatigueRiskScore,
    required this.asymmetryRiskScore,
    required this.sleepRiskScore,
    required this.monotonyRiskScore,
    required this.riskZones,
    required this.movementCompensationPatterns,
    required this.fatigueCompensationRisk,
    required this.trainingOverloadRisk,
    required this.recommendations,
    required this.immediateActions,
    required this.confidence,
  });

  factory InjuryRisk.fromJson(Map<String, dynamic> json) {
    return InjuryRisk(
      analysisDate: json['analysis_date'] as String? ?? '',
      injuryRiskScore: (json['injury_risk_score'] as num?)?.toDouble() ?? 0.0,
      injuryRiskCategory: json['injury_risk_category'] as String? ?? 'minimal',
      acwrRiskScore: (json['acwr_risk_score'] as num?)?.toDouble() ?? 0.0,
      fatigueRiskScore: (json['fatigue_risk_score'] as num?)?.toDouble() ?? 0.0,
      asymmetryRiskScore: (json['asymmetry_risk_score'] as num?)?.toDouble() ?? 0.0,
      sleepRiskScore: (json['sleep_risk_score'] as num?)?.toDouble() ?? 0.0,
      monotonyRiskScore: (json['monotony_risk_score'] as num?)?.toDouble() ?? 0.0,
      riskZones: (json['risk_zones'] as List<dynamic>?)
              ?.map((e) => RiskZone.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      movementCompensationPatterns: (json['movement_compensation_patterns'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      fatigueCompensationRisk: json['fatigue_compensation_risk'] as bool? ?? false,
      trainingOverloadRisk: json['training_overload_risk'] as bool? ?? false,
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      immediateActions: (json['immediate_actions'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }

  bool get isCritical => injuryRiskCategory == 'critical';
  bool get isHighRisk => injuryRiskCategory == 'high' || isCritical;

  String get categoryLabel => switch (injuryRiskCategory) {
        'minimal' => 'Minimal',
        'low' => 'Faible',
        'moderate' => 'Modéré',
        'high' => 'Élevé',
        'critical' => 'Critique',
        _ => injuryRiskCategory,
      };
}
