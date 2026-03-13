/// Modèles Profil Utilisateur — SOMA LOT 6.
library;

class ComputedMetrics {
  final double? bmi;
  final double? bmrKcal;
  final double? tdeeKcal;
  final double? targetCaloriesKcal;
  final double? targetProteinG;
  final double? targetHydrationMl;

  const ComputedMetrics({
    this.bmi,
    this.bmrKcal,
    this.tdeeKcal,
    this.targetCaloriesKcal,
    this.targetProteinG,
    this.targetHydrationMl,
  });

  factory ComputedMetrics.fromJson(Map<String, dynamic> json) =>
      ComputedMetrics(
        bmi: (json['bmi'] as num?)?.toDouble(),
        bmrKcal: (json['bmr_kcal'] as num?)?.toDouble(),
        tdeeKcal: (json['tdee_kcal'] as num?)?.toDouble(),
        targetCaloriesKcal: (json['target_calories_kcal'] as num?)?.toDouble(),
        targetProteinG: (json['target_protein_g'] as num?)?.toDouble(),
        targetHydrationMl: (json['target_hydration_ml'] as num?)?.toDouble(),
      );

  Map<String, dynamic> toJson() => {
        if (bmi != null) 'bmi': bmi,
        if (bmrKcal != null) 'bmr_kcal': bmrKcal,
        if (tdeeKcal != null) 'tdee_kcal': tdeeKcal,
        if (targetCaloriesKcal != null)
          'target_calories_kcal': targetCaloriesKcal,
        if (targetProteinG != null) 'target_protein_g': targetProteinG,
        if (targetHydrationMl != null)
          'target_hydration_ml': targetHydrationMl,
      };
}

class UserProfile {
  final String id;
  final String? firstName;
  final int? age;
  final String? sex;
  final double? heightCm;
  final double? currentWeightKg;
  final double? goalWeightKg;
  final String? primaryGoal;
  final String? activityLevel;
  final String? fitnessLevel;
  final String? dietaryRegime;
  final bool intermittentFasting;
  final String? fastingProtocol;
  final int? mealsPerDay;
  final List<String> homeEquipment;
  final bool gymAccess;
  final ComputedMetrics computed;
  final double profileCompletenessScore;

  const UserProfile({
    required this.id,
    this.firstName,
    this.age,
    this.sex,
    this.heightCm,
    this.currentWeightKg,
    this.goalWeightKg,
    this.primaryGoal,
    this.activityLevel,
    this.fitnessLevel,
    this.dietaryRegime,
    required this.intermittentFasting,
    this.fastingProtocol,
    this.mealsPerDay,
    required this.homeEquipment,
    required this.gymAccess,
    required this.computed,
    required this.profileCompletenessScore,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        id: json['id'] as String,
        firstName: json['first_name'] as String?,
        age: json['age'] as int?,
        sex: json['sex'] as String?,
        heightCm: (json['height_cm'] as num?)?.toDouble(),
        currentWeightKg: (json['current_weight_kg'] as num?)?.toDouble(),
        goalWeightKg: (json['goal_weight_kg'] as num?)?.toDouble(),
        primaryGoal: json['primary_goal'] as String?,
        activityLevel: json['activity_level'] as String?,
        fitnessLevel: json['fitness_level'] as String?,
        dietaryRegime: json['dietary_regime'] as String?,
        intermittentFasting: json['intermittent_fasting'] as bool? ?? false,
        fastingProtocol: json['fasting_protocol'] as String?,
        mealsPerDay: json['meals_per_day'] as int?,
        homeEquipment:
            (json['home_equipment'] as List<dynamic>? ?? []).cast<String>(),
        gymAccess: json['gym_access'] as bool? ?? false,
        computed: ComputedMetrics.fromJson(
            json['computed'] as Map<String, dynamic>? ?? {}),
        profileCompletenessScore:
            (json['profile_completeness_score'] as num?)?.toDouble() ?? 0,
      );

  String get displayName => firstName ?? 'Utilisateur';

  String? get goalLabel {
    switch (primaryGoal) {
      case 'weight_loss':
        return 'Perte de poids';
      case 'maintenance':
        return 'Maintien';
      case 'muscle_gain':
        return 'Prise de masse';
      case 'endurance':
        return 'Endurance';
      case 'general_health':
        return 'Santé générale';
      case 'longevity':
        return 'Longévité';
      default:
        return primaryGoal;
    }
  }

  String? get activityLabel {
    switch (activityLevel) {
      case 'sedentary':
        return 'Sédentaire';
      case 'lightly_active':
        return 'Légèrement actif';
      case 'moderate':
        return 'Modérément actif';
      case 'very_active':
        return 'Très actif';
      case 'extremely_active':
        return 'Extrêmement actif';
      default:
        return activityLevel;
    }
  }

  String? get fitnessLabel {
    switch (fitnessLevel) {
      case 'beginner':
        return 'Débutant';
      case 'intermediate':
        return 'Intermédiaire';
      case 'advanced':
        return 'Avancé';
      case 'athlete':
        return 'Athlète';
      default:
        return fitnessLevel;
    }
  }
}
