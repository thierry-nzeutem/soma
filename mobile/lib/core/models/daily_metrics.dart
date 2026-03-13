/// Modèle DailyMetrics — miroir du schéma backend SOMA.
///
/// Correspond à GET /api/v1/metrics/daily (DailyMetricsResponse).
library;

class DailyMetrics {
  final String userId;
  final String metricsDate;

  // Corps
  final double? weightKg;
  final double? bodyFatPct;

  // Nutrition
  final double? caloriesConsumed;
  final double? caloriesTarget;
  final double? proteinG;
  final double? proteinTargetG;
  final double? hydrationMl;
  final double? hydrationTargetMl;
  final int? mealCount;

  // Activité
  final int? steps;
  final double? activeCaloriesKcal;
  final double? trainingLoad;
  final int? workoutCount;
  final double? totalTonnageKg;

  // Sommeil
  final double? sleepMinutes;
  final double? sleepScore;
  final String? sleepQualityLabel;
  final double? hrvMs;
  final double? restingHeartRateBpm;

  // Score de récupération
  final double? readinessScore;
  final String? readinessLevel;

  // Méta
  final double dataCompletenessPct;
  final String computedAt;

  const DailyMetrics({
    required this.userId,
    required this.metricsDate,
    this.weightKg,
    this.bodyFatPct,
    this.caloriesConsumed,
    this.caloriesTarget,
    this.proteinG,
    this.proteinTargetG,
    this.hydrationMl,
    this.hydrationTargetMl,
    this.mealCount,
    this.steps,
    this.activeCaloriesKcal,
    this.trainingLoad,
    this.workoutCount,
    this.totalTonnageKg,
    this.sleepMinutes,
    this.sleepScore,
    this.sleepQualityLabel,
    this.hrvMs,
    this.restingHeartRateBpm,
    this.readinessScore,
    this.readinessLevel,
    this.dataCompletenessPct = 0.0,
    required this.computedAt,
  });

  factory DailyMetrics.fromJson(Map<String, dynamic> json) {
    return DailyMetrics(
      userId: json['user_id'] as String,
      metricsDate: json['metrics_date'] as String,
      weightKg: (json['weight_kg'] as num?)?.toDouble(),
      bodyFatPct: (json['body_fat_pct'] as num?)?.toDouble(),
      caloriesConsumed: (json['calories_consumed'] as num?)?.toDouble(),
      caloriesTarget: (json['calories_target'] as num?)?.toDouble(),
      proteinG: (json['protein_g'] as num?)?.toDouble(),
      proteinTargetG: (json['protein_target_g'] as num?)?.toDouble(),
      hydrationMl: (json['hydration_ml'] as num?)?.toDouble(),
      hydrationTargetMl: (json['hydration_target_ml'] as num?)?.toDouble(),
      mealCount: json['meal_count'] as int?,
      steps: json['steps'] as int?,
      activeCaloriesKcal: (json['active_calories_kcal'] as num?)?.toDouble(),
      trainingLoad: (json['training_load'] as num?)?.toDouble(),
      workoutCount: json['workout_count'] as int?,
      totalTonnageKg: (json['total_tonnage_kg'] as num?)?.toDouble(),
      sleepMinutes: (json['sleep_minutes'] as num?)?.toDouble(),
      sleepScore: (json['sleep_score'] as num?)?.toDouble(),
      sleepQualityLabel: json['sleep_quality_label'] as String?,
      hrvMs: (json['hrv_ms'] as num?)?.toDouble(),
      restingHeartRateBpm:
          (json['resting_heart_rate_bpm'] as num?)?.toDouble(),
      readinessScore: (json['readiness_score'] as num?)?.toDouble(),
      readinessLevel: json['readiness_level'] as String?,
      dataCompletenessPct:
          (json['data_completeness_pct'] as num?)?.toDouble() ?? 0.0,
      computedAt: json['computed_at'] as String,
    );
  }

  // ── Helpers calculés ──────────────────────────────────────────────────────

  double? get caloriePct {
    if (caloriesConsumed == null || caloriesTarget == null || caloriesTarget == 0) {
      return null;
    }
    return caloriesConsumed! / caloriesTarget! * 100;
  }

  double? get proteinPct {
    if (proteinG == null || proteinTargetG == null || proteinTargetG == 0) {
      return null;
    }
    return proteinG! / proteinTargetG! * 100;
  }

  double? get hydrationPct {
    if (hydrationMl == null || hydrationTargetMl == null || hydrationTargetMl == 0) {
      return null;
    }
    return hydrationMl! / hydrationTargetMl! * 100;
  }

  double? get sleepHours => sleepMinutes != null ? sleepMinutes! / 60 : null;
}
