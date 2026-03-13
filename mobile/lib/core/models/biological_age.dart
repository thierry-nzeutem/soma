/// Modèle Biological Age Engine — LOT 11.
///
/// Correspond à GET /api/v1/longevity/biological-age.
library;

/// Un composant du calcul d'âge biologique.
class BiologicalAgeComponent {
  final String factorName;
  final String displayName;
  final double score;
  final double weight;
  final double ageDeltaYears; // negative = biologically younger
  final String explanation;
  final bool isAvailable;

  const BiologicalAgeComponent({
    required this.factorName,
    required this.displayName,
    required this.score,
    required this.weight,
    required this.ageDeltaYears,
    required this.explanation,
    required this.isAvailable,
  });

  factory BiologicalAgeComponent.fromJson(Map<String, dynamic> json) {
    return BiologicalAgeComponent(
      factorName: json['factor_name'] as String? ?? '',
      displayName: json['display_name'] as String? ?? '',
      score: (json['score'] as num? ?? 0).toDouble(),
      weight: (json['weight'] as num? ?? 0).toDouble(),
      ageDeltaYears: (json['age_delta_years'] as num? ?? 0).toDouble(),
      explanation: json['explanation'] as String? ?? '',
      isAvailable: json['is_available'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'factor_name': factorName,
        'display_name': displayName,
        'score': score,
        'weight': weight,
        'age_delta_years': ageDeltaYears,
        'explanation': explanation,
        'is_available': isAvailable,
      };
}

/// Un levier d'action pour améliorer l'âge biologique.
class BiologicalAgeLever {
  final String leverId;
  final String title;
  final String description;
  final double potentialYearsGained;
  final String difficulty; // "easy" | "moderate" | "hard"
  final String timeframe;  // "weeks" | "months" | "years"
  final String component;

  const BiologicalAgeLever({
    required this.leverId,
    required this.title,
    required this.description,
    required this.potentialYearsGained,
    required this.difficulty,
    required this.timeframe,
    required this.component,
  });

  factory BiologicalAgeLever.fromJson(Map<String, dynamic> json) {
    return BiologicalAgeLever(
      leverId: json['lever_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      potentialYearsGained:
          (json['potential_years_gained'] as num? ?? 0).toDouble(),
      difficulty: json['difficulty'] as String? ?? 'moderate',
      timeframe: json['timeframe'] as String? ?? 'months',
      component: json['component'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'lever_id': leverId,
        'title': title,
        'description': description,
        'potential_years_gained': potentialYearsGained,
        'difficulty': difficulty,
        'timeframe': timeframe,
        'component': component,
      };

  String get difficultyLabel => switch (difficulty) {
        'easy' => 'Facile',
        'moderate' => 'Modéré',
        'hard' => 'Difficile',
        _ => difficulty,
      };

  String get timeframeLabel => switch (timeframe) {
        'weeks' => 'Semaines',
        'months' => 'Mois',
        'years' => 'Années',
        _ => timeframe,
      };
}

/// Résultat complet de l'analyse d'âge biologique.
class BiologicalAgeResult {
  final int chronologicalAge;
  final double biologicalAge;
  final double biologicalAgeDelta; // negative = younger
  final double longevityRiskScore;
  final String trendDirection; // "improving" | "stable" | "declining"
  final double confidence;
  final String explanation;
  final List<BiologicalAgeComponent> components;
  final List<BiologicalAgeLever> levers;

  const BiologicalAgeResult({
    required this.chronologicalAge,
    required this.biologicalAge,
    required this.biologicalAgeDelta,
    required this.longevityRiskScore,
    required this.trendDirection,
    required this.confidence,
    required this.explanation,
    required this.components,
    required this.levers,
  });

  factory BiologicalAgeResult.fromJson(Map<String, dynamic> json) {
    return BiologicalAgeResult(
      chronologicalAge: json['chronological_age'] as int? ?? 0,
      biologicalAge: (json['biological_age'] as num? ?? 0).toDouble(),
      biologicalAgeDelta:
          (json['biological_age_delta'] as num? ?? 0).toDouble(),
      longevityRiskScore:
          (json['longevity_risk_score'] as num? ?? 0).toDouble(),
      trendDirection: json['trend_direction'] as String? ?? 'stable',
      confidence: (json['confidence'] as num? ?? 0).toDouble(),
      explanation: json['explanation'] as String? ?? '',
      components: (json['components'] as List<dynamic>? ?? [])
          .map((e) =>
              BiologicalAgeComponent.fromJson(e as Map<String, dynamic>))
          .toList(),
      levers: (json['levers'] as List<dynamic>? ?? [])
          .map((e) =>
              BiologicalAgeLever.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'chronological_age': chronologicalAge,
        'biological_age': biologicalAge,
        'biological_age_delta': biologicalAgeDelta,
        'longevity_risk_score': longevityRiskScore,
        'trend_direction': trendDirection,
        'confidence': confidence,
        'explanation': explanation,
        'components': components.map((c) => c.toJson()).toList(),
        'levers': levers.map((l) => l.toJson()).toList(),
      };

  bool get isYoungerThanChrono => biologicalAgeDelta < -0.5;
  bool get isOlderThanChrono => biologicalAgeDelta > 0.5;

  String get trendLabel => switch (trendDirection) {
        'improving' => 'S\'améliore',
        'stable' => 'Stable',
        'declining' => 'Décline',
        _ => trendDirection,
      };

  String get deltaFormatted {
    final sign = biologicalAgeDelta >= 0 ? '+' : '';
    return '$sign${biologicalAgeDelta.toStringAsFixed(1)} ans';
  }
}

/// Item d'historique biologique.
class BiologicalAgeHistoryItem {
  final String snapshotDate;
  final double biologicalAge;
  final double biologicalAgeDelta;
  final String trendDirection;
  final double confidence;

  const BiologicalAgeHistoryItem({
    required this.snapshotDate,
    required this.biologicalAge,
    required this.biologicalAgeDelta,
    required this.trendDirection,
    required this.confidence,
  });

  factory BiologicalAgeHistoryItem.fromJson(Map<String, dynamic> json) {
    return BiologicalAgeHistoryItem(
      snapshotDate: json['snapshot_date'] as String? ?? '',
      biologicalAge: (json['biological_age'] as num? ?? 0).toDouble(),
      biologicalAgeDelta:
          (json['biological_age_delta'] as num? ?? 0).toDouble(),
      trendDirection: json['trend_direction'] as String? ?? 'stable',
      confidence: (json['confidence'] as num? ?? 0).toDouble(),
    );
  }
}
