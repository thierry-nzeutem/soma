/// Modele Sleep Quality Score -- SOMA.
///
/// Correspond a GET /api/v1/sleep/quality-score?date=YYYY-MM-DD
library;

/// Sous-score individuel du sommeil.
class SleepSubScore {
  final String name;
  final double score;
  final String label;

  const SleepSubScore({
    required this.name,
    required this.score,
    required this.label,
  });

  factory SleepSubScore.fromJson(Map<String, dynamic> json) {
    return SleepSubScore(
      name: json['name'] as String? ?? '',
      score: (json['score'] as num? ?? 0).toDouble(),
      label: json['label'] as String? ?? '',
    );
  }
}

/// Un segment du hypnogramme.
class SleepStageSegment {
  final String stage;
  final int startMinute;
  final int durationMinutes;

  const SleepStageSegment({
    required this.stage,
    required this.startMinute,
    required this.durationMinutes,
  });

  factory SleepStageSegment.fromJson(Map<String, dynamic> json) {
    return SleepStageSegment(
      stage: json['stage'] as String? ?? '',
      startMinute: json['start_minute'] as int? ?? 0,
      durationMinutes: json['duration_minutes'] as int? ?? 0,
    );
  }
}

/// Donnees completes de qualite du sommeil pour une nuit.
class SleepQualityData {
  final String date;
  final double? overallScore;
  final String? overallLabel;
  final int? durationMinutes;
  final int? deepSleepMinutes;
  final int? remSleepMinutes;
  final int? lightSleepMinutes;
  final int? awakeMinutes;
  final double? restingHrDuringSleep;
  final List<SleepSubScore> subScores;
  final List<SleepStageSegment> hypnogram;

  const SleepQualityData({
    required this.date,
    this.overallScore,
    this.overallLabel,
    this.durationMinutes,
    this.deepSleepMinutes,
    this.remSleepMinutes,
    this.lightSleepMinutes,
    this.awakeMinutes,
    this.restingHrDuringSleep,
    required this.subScores,
    required this.hypnogram,
  });

  factory SleepQualityData.fromJson(Map<String, dynamic> json) {
    return SleepQualityData(
      date: json['date'] as String? ?? '',
      overallScore: (json['overall_score'] as num?)?.toDouble(),
      overallLabel: json['overall_label'] as String?,
      durationMinutes: json['duration_minutes'] as int?,
      deepSleepMinutes: json['deep_sleep_minutes'] as int?,
      remSleepMinutes: json['rem_sleep_minutes'] as int?,
      lightSleepMinutes: json['light_sleep_minutes'] as int?,
      awakeMinutes: json['awake_minutes'] as int?,
      restingHrDuringSleep:
          (json['resting_hr_during_sleep'] as num?)?.toDouble(),
      subScores: (json['sub_scores'] as List<dynamic>? ?? [])
          .map((e) => SleepSubScore.fromJson(e as Map<String, dynamic>))
          .toList(),
      hypnogram: (json['hypnogram'] as List<dynamic>? ?? [])
          .map((e) => SleepStageSegment.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  String get durationFormatted {
    final mins = durationMinutes ?? 0;
    if (mins == 0) return '--';
    final h = mins ~/ 60;
    final m = mins % 60;
    if (h == 0) return '${m}m';
    if (m == 0) return '${h}h';
    return '${h}h ${m}m';
  }

  int get hypnogramTotalMinutes =>
      hypnogram.fold(0, (acc, s) => acc + s.durationMinutes);

  bool get hasData => overallScore != null;
}
