/// SOMA — Body Composition models.
///
/// Maps to:
///   GET /api/v1/body/composition/trend
///   GET /api/v1/body/weight/trend
library;

// Pure Dart — no Flutter import.

class CompositionPoint {
  final String date;
  final double? bodyFatPct;
  final double? muscleMassPct;
  final double? boneMassKg;
  final double? visceralFatIndex;
  final double? waterPct;
  final int? metabolicAge;
  final double? trunkFatPct;
  final double? trunkMusclePct;

  const CompositionPoint({
    required this.date,
    this.bodyFatPct,
    this.muscleMassPct,
    this.boneMassKg,
    this.visceralFatIndex,
    this.waterPct,
    this.metabolicAge,
    this.trunkFatPct,
    this.trunkMusclePct,
  });

  factory CompositionPoint.fromJson(Map<String, dynamic> json) {
    return CompositionPoint(
      date: json['date'] as String? ?? '',
      bodyFatPct: (json['body_fat_pct'] as num?)?.toDouble(),
      muscleMassPct: (json['muscle_mass_pct'] as num?)?.toDouble(),
      boneMassKg: (json['bone_mass_kg'] as num?)?.toDouble(),
      visceralFatIndex: (json['visceral_fat_index'] as num?)?.toDouble(),
      waterPct: (json['water_pct'] as num?)?.toDouble(),
      metabolicAge: (json['metabolic_age'] as num?)?.toInt(),
      trunkFatPct: (json['trunk_fat_pct'] as num?)?.toDouble(),
      trunkMusclePct: (json['trunk_muscle_pct'] as num?)?.toDouble(),
    );
  }
}

class CompositionTrendResponse {
  final String period;
  final List<CompositionPoint> points;
  final Map<String, dynamic> segmentationAvg;

  const CompositionTrendResponse({
    required this.period,
    required this.points,
    required this.segmentationAvg,
  });

  factory CompositionTrendResponse.fromJson(Map<String, dynamic> json) {
    return CompositionTrendResponse(
      period: json['period'] as String? ?? '',
      points: (json['points'] as List<dynamic>? ?? [])
          .map((e) => CompositionPoint.fromJson(e as Map<String, dynamic>))
          .toList(),
      segmentationAvg:
          json['segmentation_avg'] as Map<String, dynamic>? ?? {},
    );
  }

  double? get avgBodyFatPct =>
      (segmentationAvg['body_fat_pct'] as num?)?.toDouble();
  double? get avgMuscleMassPct =>
      (segmentationAvg['muscle_mass_pct'] as num?)?.toDouble();
  double? get avgBoneMassKg =>
      (segmentationAvg['bone_mass_kg'] as num?)?.toDouble();
  double? get avgVisceralFatIndex =>
      (segmentationAvg['visceral_fat_index'] as num?)?.toDouble();
  double? get avgWaterPct =>
      (segmentationAvg['water_pct'] as num?)?.toDouble();
  int? get avgMetabolicAge =>
      (segmentationAvg['metabolic_age'] as num?)?.toInt();
}

class WeightPoint {
  final String date;
  final double? weightKg;
  final double? bmi;
  final double? bmrKcal;
  final int? metabolicAge;

  const WeightPoint({
    required this.date,
    this.weightKg,
    this.bmi,
    this.bmrKcal,
    this.metabolicAge,
  });

  factory WeightPoint.fromJson(Map<String, dynamic> json) {
    return WeightPoint(
      date: json['date'] as String? ?? '',
      weightKg: (json['weight_kg'] as num?)?.toDouble(),
      bmi: (json['bmi'] as num?)?.toDouble(),
      bmrKcal: (json['bmr_kcal'] as num?)?.toDouble(),
      metabolicAge: (json['metabolic_age'] as num?)?.toInt(),
    );
  }
}

class WeightTrendResponse {
  final String period;
  final List<WeightPoint> points;
  final double? avgWeightKg;
  final double? minWeightKg;
  final double? maxWeightKg;
  final double? avgBmi;

  const WeightTrendResponse({
    required this.period,
    required this.points,
    this.avgWeightKg,
    this.minWeightKg,
    this.maxWeightKg,
    this.avgBmi,
  });

  factory WeightTrendResponse.fromJson(Map<String, dynamic> json) {
    return WeightTrendResponse(
      period: json['period'] as String? ?? '',
      points: (json['points'] as List<dynamic>? ?? [])
          .map((e) => WeightPoint.fromJson(e as Map<String, dynamic>))
          .toList(),
      avgWeightKg: (json['avg_weight_kg'] as num?)?.toDouble(),
      minWeightKg: (json['min_weight_kg'] as num?)?.toDouble(),
      maxWeightKg: (json['max_weight_kg'] as num?)?.toDouble(),
      avgBmi: (json['avg_bmi'] as num?)?.toDouble(),
    );
  }

  WeightPoint? get latest => points.isNotEmpty ? points.last : null;
}
