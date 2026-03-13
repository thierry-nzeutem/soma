/// Modèles de données pour le flow d'onboarding SOMA.
///
/// OnboardingData : données saisies par l'utilisateur (mutable).
/// OnboardingResult : réponse du serveur après POST /profile/onboarding.
library;

import 'package:flutter/foundation.dart';

// ── Données saisies ───────────────────────────────────────────────────────────

/// Données collectées lors des 7 étapes d'onboarding.
/// Mutable — mis à jour à chaque page par [OnboardingNotifier].
class OnboardingData {
  String? firstName;

  // Page 2 — Objectif
  String primaryGoal; // 'performance'|'health'|'weight_loss'|'longevity'

  // Page 3 — Baseline
  int age;
  String sex;          // 'male'|'female'|'other'
  double heightCm;
  double weightKg;
  double? goalWeightKg;

  // Page 4 — Activité
  String activityLevel; // 'sedentary'|'moderate'|'athlete'
  int sportFrequencyPerWeek;

  // Page 5 — Sommeil
  double sleepHoursPerNight;
  String estimatedSleepQuality; // 'poor'|'fair'|'good'|'excellent'

  // Page 6 — Biomarqueurs
  bool hasBiomarkerAccess;

  // Niveau fitness (dérivé de activityLevel si non précisé)
  String fitnessLevel; // 'beginner'|'intermediate'|'advanced'|'athlete'

  OnboardingData({
    this.firstName,
    this.primaryGoal = 'health',
    this.age = 30,
    this.sex = 'male',
    this.heightCm = 175.0,
    this.weightKg = 70.0,
    this.goalWeightKg,
    this.activityLevel = 'moderate',
    this.sportFrequencyPerWeek = 3,
    this.sleepHoursPerNight = 7.5,
    this.estimatedSleepQuality = 'fair',
    this.hasBiomarkerAccess = false,
    this.fitnessLevel = 'beginner',
  });

  /// Convertit en Map pour POST /profile/onboarding.
  Map<String, dynamic> toJson() => {
        if (firstName != null && firstName!.isNotEmpty) 'first_name': firstName,
        'primary_goal': primaryGoal,
        'age': age,
        'sex': sex,
        'height_cm': heightCm,
        'weight_kg': weightKg,
        if (goalWeightKg != null) 'goal_weight_kg': goalWeightKg,
        'activity_level': activityLevel,
        'sport_frequency_per_week': sportFrequencyPerWeek,
        'sleep_hours_per_night': sleepHoursPerNight,
        'estimated_sleep_quality': estimatedSleepQuality,
        'has_biomarker_access': hasBiomarkerAccess,
        'fitness_level': fitnessLevel,
      };

  /// Copie avec overrides.
  OnboardingData copyWith({
    String? firstName,
    String? primaryGoal,
    int? age,
    String? sex,
    double? heightCm,
    double? weightKg,
    double? goalWeightKg,
    String? activityLevel,
    int? sportFrequencyPerWeek,
    double? sleepHoursPerNight,
    String? estimatedSleepQuality,
    bool? hasBiomarkerAccess,
    String? fitnessLevel,
  }) =>
      OnboardingData(
        firstName: firstName ?? this.firstName,
        primaryGoal: primaryGoal ?? this.primaryGoal,
        age: age ?? this.age,
        sex: sex ?? this.sex,
        heightCm: heightCm ?? this.heightCm,
        weightKg: weightKg ?? this.weightKg,
        goalWeightKg: goalWeightKg ?? this.goalWeightKg,
        activityLevel: activityLevel ?? this.activityLevel,
        sportFrequencyPerWeek:
            sportFrequencyPerWeek ?? this.sportFrequencyPerWeek,
        sleepHoursPerNight: sleepHoursPerNight ?? this.sleepHoursPerNight,
        estimatedSleepQuality:
            estimatedSleepQuality ?? this.estimatedSleepQuality,
        hasBiomarkerAccess: hasBiomarkerAccess ?? this.hasBiomarkerAccess,
        fitnessLevel: fitnessLevel ?? this.fitnessLevel,
      );
}

// ── Résultat serveur ──────────────────────────────────────────────────────────

/// Objectifs initiaux calculés par le serveur.
@immutable
class OnboardingInitialTargets {
  final double caloriesTargetKcal;
  final double proteinTargetG;
  final int hydrationTargetMl;
  final int stepsGoal;
  final double sleepHoursTarget;

  const OnboardingInitialTargets({
    required this.caloriesTargetKcal,
    required this.proteinTargetG,
    required this.hydrationTargetMl,
    required this.stepsGoal,
    required this.sleepHoursTarget,
  });

  factory OnboardingInitialTargets.fromJson(Map<String, dynamic> json) =>
      OnboardingInitialTargets(
        caloriesTargetKcal: (json['calories_target_kcal'] as num).toDouble(),
        proteinTargetG: (json['protein_target_g'] as num).toDouble(),
        hydrationTargetMl: (json['hydration_target_ml'] as num).toInt(),
        stepsGoal: (json['steps_goal'] as num).toInt(),
        sleepHoursTarget: (json['sleep_hours_target'] as num).toDouble(),
      );
}

/// Réponse complète du serveur après onboarding.
@immutable
class OnboardingResult {
  final bool profileUpdated;
  final bool bodyMetricLogged;
  final OnboardingInitialTargets initialTargets;
  final String nextStep;
  final String coachWelcomeMessage;

  const OnboardingResult({
    required this.profileUpdated,
    required this.bodyMetricLogged,
    required this.initialTargets,
    required this.nextStep,
    required this.coachWelcomeMessage,
  });

  factory OnboardingResult.fromJson(Map<String, dynamic> json) =>
      OnboardingResult(
        profileUpdated: json['profile_updated'] as bool? ?? false,
        bodyMetricLogged: json['body_metric_logged'] as bool? ?? false,
        initialTargets: OnboardingInitialTargets.fromJson(
          json['initial_targets'] as Map<String, dynamic>,
        ),
        nextStep: json['next_step'] as String? ?? 'explore',
        coachWelcomeMessage: json['coach_welcome_message'] as String? ?? '',
      );
}
