/// Modèle Digital Twin V2 — LOT 11.
///
/// Correspond à GET /api/v1/twin/today (DigitalTwinStateResponse).
library;

/// Un composant physiologique du jumeau numérique avec explainabilité totale.
class TwinComponent {
  final double value;
  final String status;
  final double confidence;
  final String explanation;
  final List<String> variablesUsed;

  const TwinComponent({
    required this.value,
    required this.status,
    required this.confidence,
    required this.explanation,
    required this.variablesUsed,
  });

  factory TwinComponent.fromJson(Map<String, dynamic> json) {
    return TwinComponent(
      value: (json['value'] as num? ?? 0).toDouble(),
      status: json['status'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num? ?? 0).toDouble(),
      explanation: json['explanation'] as String? ?? '',
      variablesUsed: (json['variables_used'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'value': value,
        'status': status,
        'confidence': confidence,
        'explanation': explanation,
        'variables_used': variablesUsed,
      };
}

/// État complet du Jumeau Numérique V2.
class DigitalTwinState {
  final String snapshotDate;

  // 12 composantes physiologiques
  final TwinComponent energyBalance;
  final TwinComponent glycogen;
  final TwinComponent carbAvailability;
  final TwinComponent proteinStatus;
  final TwinComponent hydration;
  final TwinComponent fatigue;
  final TwinComponent inflammation;
  final TwinComponent sleepDebt;
  final TwinComponent recoveryCapacity;
  final TwinComponent trainingReadiness;
  final TwinComponent stressLoad;
  final TwinComponent metabolicFlexibility;

  // Synthèse
  final bool plateauRisk;
  final bool underRecoveryRisk;
  final String overallStatus;
  final String primaryConcern;
  final double globalConfidence;
  final List<String> recommendations;

  const DigitalTwinState({
    required this.snapshotDate,
    required this.energyBalance,
    required this.glycogen,
    required this.carbAvailability,
    required this.proteinStatus,
    required this.hydration,
    required this.fatigue,
    required this.inflammation,
    required this.sleepDebt,
    required this.recoveryCapacity,
    required this.trainingReadiness,
    required this.stressLoad,
    required this.metabolicFlexibility,
    required this.plateauRisk,
    required this.underRecoveryRisk,
    required this.overallStatus,
    required this.primaryConcern,
    required this.globalConfidence,
    required this.recommendations,
  });

  factory DigitalTwinState.fromJson(Map<String, dynamic> json) {
    TwinComponent comp(String key) =>
        TwinComponent.fromJson(json[key] as Map<String, dynamic>? ?? {});

    return DigitalTwinState(
      snapshotDate: json['snapshot_date'] as String? ?? '',
      energyBalance: comp('energy_balance'),
      glycogen: comp('glycogen'),
      carbAvailability: comp('carb_availability'),
      proteinStatus: comp('protein_status'),
      hydration: comp('hydration'),
      fatigue: comp('fatigue'),
      inflammation: comp('inflammation'),
      sleepDebt: comp('sleep_debt'),
      recoveryCapacity: comp('recovery_capacity'),
      trainingReadiness: comp('training_readiness'),
      stressLoad: comp('stress_load'),
      metabolicFlexibility: comp('metabolic_flexibility'),
      plateauRisk: json['plateau_risk'] as bool? ?? false,
      underRecoveryRisk: json['under_recovery_risk'] as bool? ?? false,
      overallStatus: json['overall_status'] as String? ?? 'unknown',
      primaryConcern: json['primary_concern'] as String? ?? '',
      globalConfidence: (json['global_confidence'] as num? ?? 0).toDouble(),
      recommendations: (json['recommendations'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'snapshot_date': snapshotDate,
        'energy_balance': energyBalance.toJson(),
        'glycogen': glycogen.toJson(),
        'carb_availability': carbAvailability.toJson(),
        'protein_status': proteinStatus.toJson(),
        'hydration': hydration.toJson(),
        'fatigue': fatigue.toJson(),
        'inflammation': inflammation.toJson(),
        'sleep_debt': sleepDebt.toJson(),
        'recovery_capacity': recoveryCapacity.toJson(),
        'training_readiness': trainingReadiness.toJson(),
        'stress_load': stressLoad.toJson(),
        'metabolic_flexibility': metabolicFlexibility.toJson(),
        'plateau_risk': plateauRisk,
        'under_recovery_risk': underRecoveryRisk,
        'overall_status': overallStatus,
        'primary_concern': primaryConcern,
        'global_confidence': globalConfidence,
        'recommendations': recommendations,
      };

  /// Human-readable status label (French).
  String get overallStatusLabel => switch (overallStatus) {
        'fresh' => 'Frais',
        'good' => 'Bien',
        'moderate' => 'Modéré',
        'tired' => 'Fatigué',
        'critical' => 'Critique',
        _ => overallStatus,
      };
}

/// Item d'historique pour GET /twin/history.
class DigitalTwinHistoryItem {
  final String snapshotDate;
  final String overallStatus;
  final double trainingReadiness;
  final double fatigue;
  final double globalConfidence;

  const DigitalTwinHistoryItem({
    required this.snapshotDate,
    required this.overallStatus,
    required this.trainingReadiness,
    required this.fatigue,
    required this.globalConfidence,
  });

  factory DigitalTwinHistoryItem.fromJson(Map<String, dynamic> json) {
    return DigitalTwinHistoryItem(
      snapshotDate: json['snapshot_date'] as String? ?? '',
      overallStatus: json['overall_status'] as String? ?? 'unknown',
      trainingReadiness: (json['training_readiness'] as num? ?? 0).toDouble(),
      fatigue: (json['fatigue'] as num? ?? 0).toDouble(),
      globalConfidence: (json['global_confidence'] as num? ?? 0).toDouble(),
    );
  }
}

class DigitalTwinHistory {
  final String userId;
  final int daysRequested;
  final List<DigitalTwinHistoryItem> snapshots;
  final int totalCount;

  const DigitalTwinHistory({
    required this.userId,
    required this.daysRequested,
    required this.snapshots,
    required this.totalCount,
  });

  factory DigitalTwinHistory.fromJson(Map<String, dynamic> json) {
    return DigitalTwinHistory(
      userId: json['user_id'] as String? ?? '',
      daysRequested: json['days_requested'] as int? ?? 30,
      snapshots: (json['snapshots'] as List<dynamic>? ?? [])
          .map((e) => DigitalTwinHistoryItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalCount: json['total_count'] as int? ?? 0,
    );
  }
}
