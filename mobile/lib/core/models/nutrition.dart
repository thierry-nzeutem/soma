/// Modèles Nutrition — SOMA LOT 6.
///
/// FoodItem, NutritionEntry, DailyNutritionSummary, NutritionPhoto.
library;

// ── Aliment ───────────────────────────────────────────────────────────────────

class FoodItem {
  final String id;
  final String name;
  final String? nameFr;
  final double caloriesPer100g;
  final double proteinGPer100g;
  final double carbsGPer100g;
  final double fatGPer100g;
  final double? fiberGPer100g;
  final String? foodGroup;
  final String? source;

  const FoodItem({
    required this.id,
    required this.name,
    this.nameFr,
    required this.caloriesPer100g,
    required this.proteinGPer100g,
    required this.carbsGPer100g,
    required this.fatGPer100g,
    this.fiberGPer100g,
    this.foodGroup,
    this.source,
  });

  factory FoodItem.fromJson(Map<String, dynamic> json) => FoodItem(
        id: json['id'] as String,
        name: json['name'] as String,
        nameFr: json['name_fr'] as String?,
        caloriesPer100g: (json['calories_per_100g'] as num).toDouble(),
        proteinGPer100g: (json['protein_g_per_100g'] as num).toDouble(),
        carbsGPer100g: (json['carbs_g_per_100g'] as num).toDouble(),
        fatGPer100g: (json['fat_g_per_100g'] as num).toDouble(),
        fiberGPer100g: (json['fiber_g_per_100g'] as num?)?.toDouble(),
        foodGroup: json['food_group'] as String?,
        source: json['source'] as String?,
      );

  String get displayName => nameFr ?? name;

  /// Macros pour une quantité donnée en grammes.
  double calories(double quantityG) => caloriesPer100g * quantityG / 100;
  double protein(double quantityG) => proteinGPer100g * quantityG / 100;
  double carbs(double quantityG) => carbsGPer100g * quantityG / 100;
  double fat(double quantityG) => fatGPer100g * quantityG / 100;
}

// ── Entrée nutrition ──────────────────────────────────────────────────────────

class NutritionEntry {
  final String id;
  final String loggedAt;
  final String mealType;
  final String? mealName;
  final double? calories;
  final double? proteinG;
  final double? carbsG;
  final double? fatG;
  final double? fiberG;
  final double? quantityG;
  final String? foodItemId;
  final String? foodItemName;
  final String dataQuality;
  final String? notes;

  const NutritionEntry({
    required this.id,
    required this.loggedAt,
    required this.mealType,
    this.mealName,
    this.calories,
    this.proteinG,
    this.carbsG,
    this.fatG,
    this.fiberG,
    this.quantityG,
    this.foodItemId,
    this.foodItemName,
    required this.dataQuality,
    this.notes,
  });

  factory NutritionEntry.fromJson(Map<String, dynamic> json) => NutritionEntry(
        id: json['id'] as String,
        loggedAt: json['logged_at'] as String,
        mealType: json['meal_type'] as String,
        mealName: json['meal_name'] as String?,
        calories: (json['calories'] as num?)?.toDouble(),
        proteinG: (json['protein_g'] as num?)?.toDouble(),
        carbsG: (json['carbs_g'] as num?)?.toDouble(),
        fatG: (json['fat_g'] as num?)?.toDouble(),
        fiberG: (json['fiber_g'] as num?)?.toDouble(),
        quantityG: (json['quantity_g'] as num?)?.toDouble(),
        foodItemId: json['food_item_id'] as String?,
        foodItemName: json['food_item_name'] as String?,
        dataQuality: json['data_quality'] as String? ?? 'estimated',
        notes: json['notes'] as String?,
      );

  String get mealTypeLabel {
    switch (mealType) {
      case 'breakfast':
        return 'Petit-déjeuner';
      case 'lunch':
        return 'Déjeuner';
      case 'dinner':
        return 'Dîner';
      case 'snack':
        return 'En-cas';
      default:
        return mealType;
    }
  }
}

// ── Résumé nutrition ──────────────────────────────────────────────────────────

class MacroTotals {
  final double calories;
  final double proteinG;
  final double carbsG;
  final double fatG;
  final double fiberG;

  const MacroTotals({
    required this.calories,
    required this.proteinG,
    required this.carbsG,
    required this.fatG,
    required this.fiberG,
  });

  factory MacroTotals.fromJson(Map<String, dynamic> json) => MacroTotals(
        calories: (json['calories'] as num?)?.toDouble() ?? 0,
        proteinG: (json['protein_g'] as num?)?.toDouble() ?? 0,
        carbsG: (json['carbs_g'] as num?)?.toDouble() ?? 0,
        fatG: (json['fat_g'] as num?)?.toDouble() ?? 0,
        fiberG: (json['fiber_g'] as num?)?.toDouble() ?? 0,
      );
}

class MacroGoals {
  final double? caloriesTarget;
  final double? proteinTargetG;

  const MacroGoals({this.caloriesTarget, this.proteinTargetG});

  factory MacroGoals.fromJson(Map<String, dynamic> json) => MacroGoals(
        caloriesTarget: (json['calories_target'] as num?)?.toDouble(),
        proteinTargetG: (json['protein_target_g'] as num?)?.toDouble(),
      );
}

class DailyNutritionSummary {
  final String date;
  final int mealCount;
  final MacroTotals totals;
  final MacroGoals goals;
  final List<NutritionEntry> meals;
  final double dataCompletenessPct;

  const DailyNutritionSummary({
    required this.date,
    required this.mealCount,
    required this.totals,
    required this.goals,
    required this.meals,
    required this.dataCompletenessPct,
  });

  factory DailyNutritionSummary.fromJson(Map<String, dynamic> json) {
    final mealsRaw = json['meals'] as List<dynamic>? ?? [];
    return DailyNutritionSummary(
      date: json['date'] as String,
      mealCount: json['meal_count'] as int? ?? 0,
      totals: MacroTotals.fromJson(
          json['totals'] as Map<String, dynamic>? ?? {}),
      goals: MacroGoals.fromJson(
          json['goals'] as Map<String, dynamic>? ?? {}),
      meals: mealsRaw
          .map((e) => NutritionEntry.fromJson(e as Map<String, dynamic>))
          .toList(),
      dataCompletenessPct:
          (json['data_completeness_pct'] as num?)?.toDouble() ?? 0,
    );
  }

  double get caloriePct {
    final t = goals.caloriesTarget;
    if (t == null || t == 0) return 0;
    return (totals.calories / t * 100).clamp(0, 100);
  }

  double get proteinPct {
    final t = goals.proteinTargetG;
    if (t == null || t == 0) return 0;
    return (totals.proteinG / t * 100).clamp(0, 100);
  }
}

// ── Photo repas ───────────────────────────────────────────────────────────────

class DetectedFood {
  final String name;
  final double? quantityG;
  final double? caloriesEstimated;
  final double? confidence;

  const DetectedFood({
    required this.name,
    this.quantityG,
    this.caloriesEstimated,
    this.confidence,
  });

  factory DetectedFood.fromJson(Map<String, dynamic> json) => DetectedFood(
        name: json['name'] as String,
        quantityG: (json['quantity_g'] as num?)?.toDouble(),
        caloriesEstimated: (json['calories_estimated'] as num?)?.toDouble(),
        confidence: (json['confidence'] as num?)?.toDouble(),
      );
}

class NutritionPhoto {
  final String photoId;
  final String analysisStatus; // pending|analyzing|analyzed|failed
  final List<DetectedFood> identifiedFoods;
  final double? estimatedCalories;
  final double? estimatedProteinG;
  final double? estimatedCarbsG;
  final double? estimatedFatG;
  final double? overallConfidence;
  final String? mealTypeGuess;

  const NutritionPhoto({
    required this.photoId,
    required this.analysisStatus,
    required this.identifiedFoods,
    this.estimatedCalories,
    this.estimatedProteinG,
    this.estimatedCarbsG,
    this.estimatedFatG,
    this.overallConfidence,
    this.mealTypeGuess,
  });

  factory NutritionPhoto.fromJson(Map<String, dynamic> json) {
    final foods = json['identified_foods'] as List<dynamic>? ?? [];
    return NutritionPhoto(
      photoId: json['photo_id'] as String,
      analysisStatus: json['analysis_status'] as String? ?? 'pending',
      identifiedFoods: foods
          .map((e) => DetectedFood.fromJson(e as Map<String, dynamic>))
          .toList(),
      estimatedCalories: (json['estimated_calories'] as num?)?.toDouble(),
      estimatedProteinG: (json['estimated_protein_g'] as num?)?.toDouble(),
      estimatedCarbsG: (json['estimated_carbs_g'] as num?)?.toDouble(),
      estimatedFatG: (json['estimated_fat_g'] as num?)?.toDouble(),
      overallConfidence: (json['overall_confidence'] as num?)?.toDouble(),
      mealTypeGuess: json['meal_type_guess'] as String?,
    );
  }

  bool get isAnalyzed => analysisStatus == 'analyzed';
  bool get isFailed => analysisStatus == 'failed';
  bool get isPending =>
      analysisStatus == 'pending' || analysisStatus == 'analyzing';
}
