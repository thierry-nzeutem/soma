/// Modèle MovementQuality — scores qualité du mouvement (LOT 7).
///
/// Scores V1 simplifiés, non médicaux, entre 0 et 100.
/// Basés sur : amplitude, stabilité, régularité.
library;

// ── Scores qualité ────────────────────────────────────────────────────────────

/// Scores qualité du mouvement pour une session vision.
class MovementQuality {
  /// Amplitude du mouvement — profondeur/hauteur atteinte [0, 100].
  /// Ex : squat : angle au bas ≤ 90° = 100, ≥ 130° = 20.
  final double amplitudeScore;

  /// Stabilité corporelle — faible variance des angles = haute stabilité [0, 100].
  final double stabilityScore;

  /// Régularité des répétitions — durées similaires = haute régularité [0, 100].
  final double regularityScore;

  /// Score global pondéré [0, 100].
  final double overallScore;

  /// Nombre de frames analysés (pour la confiance).
  final int framesAnalyzed;

  /// Nombre de répétitions complètes analysées.
  final int repsAnalyzed;

  const MovementQuality({
    this.amplitudeScore = 0,
    this.stabilityScore = 0,
    this.regularityScore = 0,
    this.overallScore = 0,
    this.framesAnalyzed = 0,
    this.repsAnalyzed = 0,
  });

  static const MovementQuality zero = MovementQuality();

  /// Retourne un score initial (avant assez de données).
  static const MovementQuality initial = MovementQuality(
    amplitudeScore: 0,
    stabilityScore: 0,
    regularityScore: 0,
    overallScore: 0,
  );

  // ── Labels d'interprétation ───────────────────────────────────────────────

  String get overallLabel {
    if (overallScore >= 80) return 'Excellent';
    if (overallScore >= 65) return 'Bon';
    if (overallScore >= 50) return 'Correct';
    if (overallScore >= 35) return 'À améliorer';
    return 'Insuffisant';
  }

  String get amplitudeLabel {
    if (amplitudeScore >= 80) return 'Complète';
    if (amplitudeScore >= 60) return 'Bonne';
    if (amplitudeScore >= 40) return 'Partielle';
    return 'Insuffisante';
  }

  String get stabilityLabel {
    if (stabilityScore >= 80) return 'Très stable';
    if (stabilityScore >= 60) return 'Stable';
    if (stabilityScore >= 40) return 'Modéré';
    return 'Instable';
  }

  String get regularityLabel {
    if (regularityScore >= 80) return 'Très régulier';
    if (regularityScore >= 60) return 'Régulier';
    if (regularityScore >= 40) return 'Irrégulier';
    return 'Très irrégulier';
  }

  bool get hasEnoughData => repsAnalyzed >= 2 || framesAnalyzed >= 30;

  MovementQuality copyWith({
    double? amplitudeScore,
    double? stabilityScore,
    double? regularityScore,
    double? overallScore,
    int? framesAnalyzed,
    int? repsAnalyzed,
  }) =>
      MovementQuality(
        amplitudeScore: amplitudeScore ?? this.amplitudeScore,
        stabilityScore: stabilityScore ?? this.stabilityScore,
        regularityScore: regularityScore ?? this.regularityScore,
        overallScore: overallScore ?? this.overallScore,
        framesAnalyzed: framesAnalyzed ?? this.framesAnalyzed,
        repsAnalyzed: repsAnalyzed ?? this.repsAnalyzed,
      );

  Map<String, dynamic> toJson() => {
        'amplitude_score': amplitudeScore,
        'stability_score': stabilityScore,
        'regularity_score': regularityScore,
        'overall_score': overallScore,
        'frames_analyzed': framesAnalyzed,
        'reps_analyzed': repsAnalyzed,
      };

  factory MovementQuality.fromJson(Map<String, dynamic> json) =>
      MovementQuality(
        amplitudeScore: (json['amplitude_score'] as num?)?.toDouble() ?? 0,
        stabilityScore: (json['stability_score'] as num?)?.toDouble() ?? 0,
        regularityScore: (json['regularity_score'] as num?)?.toDouble() ?? 0,
        overallScore: (json['overall_score'] as num?)?.toDouble() ?? 0,
        framesAnalyzed: json['frames_analyzed'] as int? ?? 0,
        repsAnalyzed: json['reps_analyzed'] as int? ?? 0,
      );
}
