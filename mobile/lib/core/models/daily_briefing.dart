/// Modèle DailyBriefing — LOT 18.
///
/// Correspond à GET /api/v1/daily/briefing (DailyBriefingResponse).
/// Agrège : readiness, sommeil, entraînement, nutrition, hydratation,
/// jumeau numérique, alertes, insight, conseil coach.
library;

import 'package:flutter/foundation.dart';

@immutable
class DailyBriefing {
  // ── Méta ──────────────────────────────────────────────────────────────────
  /// Date du briefing (ISO 8601 : "2026-03-08").
  final String briefingDate;

  /// Horodatage de génération (ISO 8601).
  final String generatedAt;

  // ── Readiness ─────────────────────────────────────────────────────────────
  /// Score de récupération 0–100 (null si aucune donnée).
  final double? readinessScore;

  /// Niveau textuel : "low" | "moderate" | "good" | "excellent".
  final String? readinessLevel;

  /// Couleur hex associée : "#FF3B30" | "#FF9500" | "#34C759".
  final String readinessColor;

  // ── Sommeil ───────────────────────────────────────────────────────────────
  /// Durée de sommeil en heures (ex : 7.25).
  final double? sleepDurationH;

  /// Qualité : "poor" | "fair" | "good" | "excellent" (null si aucune donnée).
  final String? sleepQualityLabel;

  // ── Entraînement ──────────────────────────────────────────────────────────
  /// Type recommandé : "rest" | "strength" | "cardio" | "recovery" | etc.
  final String? trainingType;

  /// Intensité : "low" | "moderate" | "high".
  final String? trainingIntensity;

  /// Durée recommandée en minutes.
  final int? trainingDurationMin;

  // ── Nutrition ─────────────────────────────────────────────────────────────
  /// Objectif calorique journalier (kcal).
  final double? calorieTarget;

  /// Objectif protéines (g).
  final double? proteinTargetG;

  /// Objectif glucides (g).
  final double? carbTargetG;

  // ── Hydratation ───────────────────────────────────────────────────────────
  /// Objectif hydratation journalier (ml).
  final int? hydrationTargetMl;

  // ── Jumeau Numérique ──────────────────────────────────────────────────────
  /// Statut global : "fresh" | "good" | "moderate" | "tired" | "critical".
  final String? twinStatus;

  /// Préoccupation principale du jumeau (ex : "fatigue élevée").
  final String? twinPrimaryConcern;

  // ── Alertes & Insights ────────────────────────────────────────────────────
  /// Jusqu'à 3 alertes textuelles à afficher.
  final List<String> alerts;

  /// Top insight du jour (null si aucun).
  final String? topInsight;

  /// Conseil coach (null si aucun).
  final String? coachTip;

  const DailyBriefing({
    required this.briefingDate,
    required this.generatedAt,
    this.readinessScore,
    this.readinessLevel,
    required this.readinessColor,
    this.sleepDurationH,
    this.sleepQualityLabel,
    this.trainingType,
    this.trainingIntensity,
    this.trainingDurationMin,
    this.calorieTarget,
    this.proteinTargetG,
    this.carbTargetG,
    this.hydrationTargetMl,
    this.twinStatus,
    this.twinPrimaryConcern,
    required this.alerts,
    this.topInsight,
    this.coachTip,
  });

  // ── Désérialisation JSON ───────────────────────────────────────────────────

  factory DailyBriefing.fromJson(Map<String, dynamic> json) {
    return DailyBriefing(
      briefingDate: json['briefing_date'] as String? ?? '',
      generatedAt: json['generated_at'] as String? ?? '',
      readinessScore: (json['readiness_score'] as num?)?.toDouble(),
      readinessLevel: json['readiness_level'] as String?,
      readinessColor: json['readiness_color'] as String? ?? '#FF9500',
      sleepDurationH: (json['sleep_duration_h'] as num?)?.toDouble(),
      sleepQualityLabel: json['sleep_quality_label'] as String?,
      trainingType: json['training_type'] as String?,
      trainingIntensity: json['training_intensity'] as String?,
      trainingDurationMin: json['training_duration_min'] as int?,
      calorieTarget: (json['calorie_target'] as num?)?.toDouble(),
      proteinTargetG: (json['protein_target_g'] as num?)?.toDouble(),
      carbTargetG: (json['carb_target_g'] as num?)?.toDouble(),
      hydrationTargetMl: json['hydration_target_ml'] as int?,
      twinStatus: json['twin_status'] as String?,
      twinPrimaryConcern: json['twin_primary_concern'] as String?,
      alerts: (json['alerts'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      topInsight: json['top_insight'] as String?,
      coachTip: json['coach_tip'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'briefing_date': briefingDate,
        'generated_at': generatedAt,
        'readiness_score': readinessScore,
        'readiness_level': readinessLevel,
        'readiness_color': readinessColor,
        'sleep_duration_h': sleepDurationH,
        'sleep_quality_label': sleepQualityLabel,
        'training_type': trainingType,
        'training_intensity': trainingIntensity,
        'training_duration_min': trainingDurationMin,
        'calorie_target': calorieTarget,
        'protein_target_g': proteinTargetG,
        'carb_target_g': carbTargetG,
        'hydration_target_ml': hydrationTargetMl,
        'twin_status': twinStatus,
        'twin_primary_concern': twinPrimaryConcern,
        'alerts': alerts,
        'top_insight': topInsight,
        'coach_tip': coachTip,
      };

  // ── Helpers d'affichage ───────────────────────────────────────────────────

  /// Label français du niveau de readiness.
  String get readinessLevelLabel => switch (readinessLevel) {
        'excellent' => 'Excellent',
        'good' => 'Bon',
        'moderate' => 'Modéré',
        'low' => 'Faible',
        _ => '—',
      };

  /// Label français du type d'entraînement.
  String get trainingTypeLabel => switch (trainingType) {
        'rest' => 'Repos',
        'strength' => 'Force',
        'cardio' => 'Cardio',
        'hiit' => 'HIIT',
        'recovery' => 'Récupération active',
        'mobility' => 'Mobilité',
        'deload' => 'Déload',
        _ => trainingType ?? '—',
      };

  /// Label français de l'intensité.
  String get intensityLabel => switch (trainingIntensity) {
        'low' => 'Faible',
        'moderate' => 'Modérée',
        'high' => 'Élevée',
        _ => trainingIntensity ?? '—',
      };

  /// Label français de la qualité de sommeil.
  String get sleepQualityDisplayLabel => switch (sleepQualityLabel) {
        'excellent' => 'Excellente',
        'good' => 'Bonne',
        'fair' => 'Correcte',
        'poor' => 'Mauvaise',
        _ => sleepQualityLabel ?? '—',
      };

  /// Label français du statut du jumeau numérique.
  String get twinStatusLabel => switch (twinStatus) {
        'fresh' => 'Frais',
        'good' => 'Bien',
        'moderate' => 'Modéré',
        'tired' => 'Fatigué',
        'critical' => 'Critique',
        _ => twinStatus ?? '—',
      };

  /// Vrai si le score de readiness est disponible.
  bool get hasReadiness => readinessScore != null;

  /// Vrai si des données de sommeil sont disponibles.
  bool get hasSleep => sleepDurationH != null;

  /// Vrai si un entraînement est recommandé (non null et non "rest").
  bool get hasTrainingRecommendation =>
      trainingType != null && trainingType != 'rest';

  /// Vrai si des données nutritionnelles sont disponibles.
  bool get hasNutrition => calorieTarget != null;
}
