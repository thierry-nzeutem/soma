/// Modèle DailyHealthPlan — miroir du schéma backend SOMA.
///
/// Correspond à GET /api/v1/health/plan/today (DailyHealthPlanResponse).
library;

class WorkoutRecommendation {
  final String type;
  final String? description;
  final int? durationMinutes;
  final String? intensity;
  final List<String> exercises;

  const WorkoutRecommendation({
    required this.type,
    this.description,
    this.durationMinutes,
    this.intensity,
    this.exercises = const [],
  });

  factory WorkoutRecommendation.fromJson(Map<String, dynamic> json) {
    return WorkoutRecommendation(
      type: json['type'] as String? ?? 'rest',
      description: json['description'] as String?,
      durationMinutes: json['duration_minutes'] as int?,
      intensity: json['intensity'] as String?,
      exercises: (json['exercises'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
    );
  }
}

class NutritionTargetsSummary {
  final double? caloriesKcal;
  final double? proteinG;
  final double? carbsG;
  final double? fatG;
  final double? fiberG;
  final double? waterMl;

  const NutritionTargetsSummary({
    this.caloriesKcal,
    this.proteinG,
    this.carbsG,
    this.fatG,
    this.fiberG,
    this.waterMl,
  });

  factory NutritionTargetsSummary.fromJson(Map<String, dynamic> json) {
    return NutritionTargetsSummary(
      caloriesKcal: (json['calories_kcal'] as num?)?.toDouble(),
      proteinG: (json['protein_g'] as num?)?.toDouble(),
      carbsG: (json['carbs_g'] as num?)?.toDouble(),
      fatG: (json['fat_g'] as num?)?.toDouble(),
      fiberG: (json['fiber_g'] as num?)?.toDouble(),
      waterMl: (json['water_ml'] as num?)?.toDouble(),
    );
  }
}

class DailyHealthPlan {
  final String targetDate;
  final String readinessLevel;
  final double? readinessScore;
  final String recommendedIntensity;
  final WorkoutRecommendation? workoutRecommendation;
  final NutritionTargetsSummary? nutritionTargets;
  final String? nutritionFocus;
  final List<String> dailyTips;
  final List<String> alerts;
  final String? fastingWindow;
  final String? eatWindow;
  final bool intermittentFasting;

  const DailyHealthPlan({
    required this.targetDate,
    required this.readinessLevel,
    this.readinessScore,
    required this.recommendedIntensity,
    this.workoutRecommendation,
    this.nutritionTargets,
    this.nutritionFocus,
    this.dailyTips = const [],
    this.alerts = const [],
    this.fastingWindow,
    this.eatWindow,
    this.intermittentFasting = false,
  });

  factory DailyHealthPlan.fromJson(Map<String, dynamic> json) {
    // nutrition_targets peut être un sous-objet ou null
    NutritionTargetsSummary? targets;
    if (json['nutrition_targets'] is Map<String, dynamic>) {
      targets = NutritionTargetsSummary.fromJson(
        json['nutrition_targets'] as Map<String, dynamic>,
      );
    }

    WorkoutRecommendation? workout;
    if (json['workout_recommendation'] is Map<String, dynamic>) {
      workout = WorkoutRecommendation.fromJson(
        json['workout_recommendation'] as Map<String, dynamic>,
      );
    }

    return DailyHealthPlan(
      targetDate: json['target_date'] as String,
      readinessLevel: json['readiness_level'] as String? ?? 'moderate',
      readinessScore: (json['readiness_score'] as num?)?.toDouble(),
      recommendedIntensity:
          json['recommended_intensity'] as String? ?? 'moderate',
      workoutRecommendation: workout,
      nutritionTargets: targets,
      nutritionFocus: json['nutrition_focus'] as String?,
      dailyTips: (json['daily_tips'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      alerts: (json['alerts'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      fastingWindow: json['fasting_window'] as String?,
      eatWindow: json['eat_window'] as String?,
      intermittentFasting: json['intermittent_fasting'] as bool? ?? false,
    );
  }
}
