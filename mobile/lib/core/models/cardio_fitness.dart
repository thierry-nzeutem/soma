/// SOMA — Cardio Fitness (VO2max) model.
///
/// Maps to: GET /api/v1/fitness/cardio-fitness
library;

// Pure Dart — no Flutter import.

class CardioFitnessResponse {
  final double? vo2max;
  final String? category;
  final double? percentile;
  final String? ageGroup;
  final String? sex;
  final String? improvementSuggestion;
  final List<Map<String, dynamic>> referenceBars;

  const CardioFitnessResponse({
    this.vo2max,
    this.category,
    this.percentile,
    this.ageGroup,
    this.sex,
    this.improvementSuggestion,
    this.referenceBars = const [],
  });

  factory CardioFitnessResponse.fromJson(Map<String, dynamic> json) {
    return CardioFitnessResponse(
      vo2max: (json['vo2max'] as num?)?.toDouble(),
      category: json['category'] as String?,
      percentile: (json['percentile'] as num?)?.toDouble(),
      ageGroup: json['age_group'] as String?,
      sex: json['sex'] as String?,
      improvementSuggestion: json['improvement_suggestion'] as String?,
      referenceBars: (json['reference_bars'] as List<dynamic>? ?? [])
          .map((e) => e as Map<String, dynamic>)
          .toList(),
    );
  }

  /// Normalized category key for color mapping.
  /// Returns one of: poor | fair | good | excellent | unknown
  String get categoryKey {
    final raw = (category ?? '').toLowerCase();
    if (raw.contains('poor') || raw.contains('faible') || raw.contains('mauvais')) {
      return 'poor';
    }
    if (raw.contains('fair') || raw.contains('moyen') || raw.contains('passable')) {
      return 'fair';
    }
    if (raw.contains('good') || raw.contains('bon') || raw.contains('bien')) {
      return 'good';
    }
    if (raw.contains('excellent') || raw.contains('superior') ||
        raw.contains('elite') || raw.contains('superieur')) {
      return 'excellent';
    }
    return 'unknown';
  }
}
