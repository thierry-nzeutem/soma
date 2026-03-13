/// Modèle Adaptive Nutrition Engine — LOT 11.
///
/// Correspond à GET /api/v1/nutrition/adaptive-plan.
library;

/// Types de journée nutritionnelle.
class DayType {
  static const rest = 'rest';
  static const training = 'training';
  static const intenseTraining = 'intense_training';
  static const recovery = 'recovery';
  static const deload = 'deload';

  static String label(String type) => switch (type) {
        rest => 'Repos',
        training => 'Entraînement',
        intenseTraining => 'Entraînement intense',
        recovery => 'Récupération',
        deload => 'Décharge',
        _ => type,
      };

  static bool isTrainingDay(String type) =>
      type == training || type == intenseTraining;
}

/// Une cible nutritionnelle avec rationale et priorité.
class NutritionTarget {
  final double value;
  final String unit;
  final String rationale;
  final String priority; // "critical" | "high" | "normal" | "low"

  const NutritionTarget({
    required this.value,
    required this.unit,
    required this.rationale,
    required this.priority,
  });

  factory NutritionTarget.fromJson(Map<String, dynamic> json) {
    return NutritionTarget(
      value: (json['value'] as num? ?? 0).toDouble(),
      unit: json['unit'] as String? ?? '',
      rationale: json['rationale'] as String? ?? '',
      priority: json['priority'] as String? ?? 'normal',
    );
  }

  Map<String, dynamic> toJson() => {
        'value': value,
        'unit': unit,
        'rationale': rationale,
        'priority': priority,
      };
}

/// Plan nutritionnel adaptatif complet.
class AdaptiveNutritionPlan {
  final String targetDate;
  final String dayType;
  final String glycogenStatus;

  final NutritionTarget calorieTarget;
  final NutritionTarget proteinTarget;
  final NutritionTarget carbTarget;
  final NutritionTarget fatTarget;
  final NutritionTarget fiberTarget;
  final NutritionTarget hydrationTarget;

  final String mealTimingStrategy;
  final bool fastingCompatible;
  final String fastingRationale;
  final String? preWorkoutGuidance;
  final String? postWorkoutGuidance;
  final String recoveryNutritionFocus;
  final String electrolyteFocus;
  final List<String> supplementationFocus;

  final double confidence;
  final List<String> assumptions;
  final List<String> alerts;

  const AdaptiveNutritionPlan({
    required this.targetDate,
    required this.dayType,
    required this.glycogenStatus,
    required this.calorieTarget,
    required this.proteinTarget,
    required this.carbTarget,
    required this.fatTarget,
    required this.fiberTarget,
    required this.hydrationTarget,
    required this.mealTimingStrategy,
    required this.fastingCompatible,
    required this.fastingRationale,
    this.preWorkoutGuidance,
    this.postWorkoutGuidance,
    required this.recoveryNutritionFocus,
    required this.electrolyteFocus,
    required this.supplementationFocus,
    required this.confidence,
    required this.assumptions,
    required this.alerts,
  });

  factory AdaptiveNutritionPlan.fromJson(Map<String, dynamic> json) {
    NutritionTarget target(String key) =>
        NutritionTarget.fromJson(json[key] as Map<String, dynamic>? ?? {});

    return AdaptiveNutritionPlan(
      targetDate: json['target_date'] as String? ?? '',
      dayType: json['day_type'] as String? ?? 'rest',
      glycogenStatus: json['glycogen_status'] as String? ?? 'unknown',
      calorieTarget: target('calorie_target'),
      proteinTarget: target('protein_target'),
      carbTarget: target('carb_target'),
      fatTarget: target('fat_target'),
      fiberTarget: target('fiber_target'),
      hydrationTarget: target('hydration_target'),
      mealTimingStrategy:
          json['meal_timing_strategy'] as String? ?? '',
      fastingCompatible: json['fasting_compatible'] as bool? ?? false,
      fastingRationale: json['fasting_rationale'] as String? ?? '',
      preWorkoutGuidance: json['pre_workout_guidance'] as String?,
      postWorkoutGuidance: json['post_workout_guidance'] as String?,
      recoveryNutritionFocus:
          json['recovery_nutrition_focus'] as String? ?? '',
      electrolyteFocus: json['electrolyte_focus'] as String? ?? '',
      supplementationFocus:
          (json['supplementation_focus'] as List<dynamic>? ?? [])
              .map((e) => e as String)
              .toList(),
      confidence: (json['confidence'] as num? ?? 0).toDouble(),
      assumptions: (json['assumptions'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      alerts: (json['alerts'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'target_date': targetDate,
        'day_type': dayType,
        'glycogen_status': glycogenStatus,
        'calorie_target': calorieTarget.toJson(),
        'protein_target': proteinTarget.toJson(),
        'carb_target': carbTarget.toJson(),
        'fat_target': fatTarget.toJson(),
        'fiber_target': fiberTarget.toJson(),
        'hydration_target': hydrationTarget.toJson(),
        'meal_timing_strategy': mealTimingStrategy,
        'fasting_compatible': fastingCompatible,
        'fasting_rationale': fastingRationale,
        'pre_workout_guidance': preWorkoutGuidance,
        'post_workout_guidance': postWorkoutGuidance,
        'recovery_nutrition_focus': recoveryNutritionFocus,
        'electrolyte_focus': electrolyteFocus,
        'supplementation_focus': supplementationFocus,
        'confidence': confidence,
        'assumptions': assumptions,
        'alerts': alerts,
      };

  String get dayTypeLabel => DayType.label(dayType);

  bool get isTrainingDay => DayType.isTrainingDay(dayType);
}
