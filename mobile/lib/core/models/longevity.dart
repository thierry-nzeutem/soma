/// Modèle LongevityScore — miroir du schéma backend SOMA.
///
/// Correspond à GET /api/v1/scores/longevity (LongevityScoreResponse).
library;

class ImprovementLever {
  final String component;
  final double score;
  final String priority;
  final String suggestion;

  const ImprovementLever({
    required this.component,
    required this.score,
    required this.priority,
    required this.suggestion,
  });

  factory ImprovementLever.fromJson(Map<String, dynamic> json) {
    return ImprovementLever(
      component: json['component'] as String,
      score: (json['score'] as num).toDouble(),
      priority: json['priority'] as String? ?? 'medium',
      suggestion: json['suggestion'] as String? ?? '',
    );
  }
}

class LongevityScore {
  final String userId;
  final String scoreDate;

  // Composantes (0–100)
  final double? cardioScore;
  final double? strengthScore;
  final double? sleepScore;
  final double? nutritionScore;
  final double? weightScore;
  final double? bodyCompScore;
  final double? consistencyScore;

  // Score global et âge biologique
  final double longevityScore;
  final double? biologicalAgeEstimate;

  // Leviers d'amélioration
  final List<ImprovementLever> topImprovementLevers;

  // Méta
  final double confidence;
  final String createdAt;

  const LongevityScore({
    required this.userId,
    required this.scoreDate,
    this.cardioScore,
    this.strengthScore,
    this.sleepScore,
    this.nutritionScore,
    this.weightScore,
    this.bodyCompScore,
    this.consistencyScore,
    required this.longevityScore,
    this.biologicalAgeEstimate,
    this.topImprovementLevers = const [],
    this.confidence = 0.0,
    required this.createdAt,
  });

  factory LongevityScore.fromJson(Map<String, dynamic> json) {
    return LongevityScore(
      userId: json['user_id'] as String,
      scoreDate: json['score_date'] as String,
      cardioScore: (json['cardio_score'] as num?)?.toDouble(),
      strengthScore: (json['strength_score'] as num?)?.toDouble(),
      sleepScore: (json['sleep_score'] as num?)?.toDouble(),
      nutritionScore: (json['nutrition_score'] as num?)?.toDouble(),
      weightScore: (json['weight_score'] as num?)?.toDouble(),
      bodyCompScore: (json['body_comp_score'] as num?)?.toDouble(),
      consistencyScore: (json['consistency_score'] as num?)?.toDouble(),
      longevityScore: (json['longevity_score'] as num).toDouble(),
      biologicalAgeEstimate:
          (json['biological_age_estimate'] as num?)?.toDouble(),
      topImprovementLevers:
          (json['top_improvement_levers'] as List<dynamic>?)
              ?.map((e) =>
                  ImprovementLever.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] as String,
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  /// Toutes les composantes nommées avec leur score (pour affichage barres).
  List<({String label, double? score, String key})> get components => [
        (label: 'Cardio', score: cardioScore, key: 'cardio'),
        (label: 'Force', score: strengthScore, key: 'strength'),
        (label: 'Sommeil', score: sleepScore, key: 'sleep'),
        (label: 'Nutrition', score: nutritionScore, key: 'nutrition'),
        (label: 'Poids', score: weightScore, key: 'weight'),
        (label: 'Compo. corp.', score: bodyCompScore, key: 'body_comp'),
        (label: 'Régularité', score: consistencyScore, key: 'consistency'),
      ];
}
