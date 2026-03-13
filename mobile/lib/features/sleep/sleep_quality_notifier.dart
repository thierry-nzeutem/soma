/// SleepQualityNotifier - Score de qualite du sommeil SOMA.
///
/// Charge GET /api/v1/sleep/quality-score?date=YYYY-MM-DD.
/// Expose AsyncValue<SleepQualityData?>.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';

// -- Inline models ----------------------------------------------------------

class SleepSubScore {
  final String name;
  final int score;
  final String label;

  const SleepSubScore({
    required this.name,
    required this.score,
    required this.label,
  });

  factory SleepSubScore.fromJson(Map<String, dynamic> json) {
    return SleepSubScore(
      name: json['name'] as String? ?? '',
      score: json['score'] as int? ?? 0,
      label: json['label'] as String? ?? '',
    );
  }
}

class HypnogramStage {
  // Stage identifier: awake / light / deep / rem
  final String stage;
  final int startMinute;
  final int durationMinutes;

  const HypnogramStage({
    required this.stage,
    required this.startMinute,
    required this.durationMinutes,
  });

  factory HypnogramStage.fromJson(Map<String, dynamic> json) {
    return HypnogramStage(
      stage: json['stage'] as String? ?? 'light',
      startMinute: json['start_minute'] as int? ?? 0,
      durationMinutes: json['duration_minutes'] as int? ?? 0,
    );
  }
}

class SleepQualityData {
  final String date;
  final int? overallScore;
  final String? overallLabel;
  final int? durationMinutes;
  final int? deepSleepMinutes;
  final int? remSleepMinutes;
  final List<SleepSubScore> subScores;
  final List<HypnogramStage> hypnogram;

  const SleepQualityData({
    required this.date,
    this.overallScore,
    this.overallLabel,
    this.durationMinutes,
    this.deepSleepMinutes,
    this.remSleepMinutes,
    required this.subScores,
    required this.hypnogram,
  });

  factory SleepQualityData.fromJson(Map<String, dynamic> json) {
    return SleepQualityData(
      date: json['date'] as String? ?? '',
      overallScore: json['overall_score'] as int?,
      overallLabel: json['overall_label'] as String?,
      durationMinutes: json['duration_minutes'] as int?,
      deepSleepMinutes: json['deep_sleep_minutes'] as int?,
      remSleepMinutes: json['rem_sleep_minutes'] as int?,
      subScores: (json['sub_scores'] as List<dynamic>? ?? [])
          .map((e) => SleepSubScore.fromJson(e as Map<String, dynamic>))
          .toList(),
      hypnogram: (json['hypnogram'] as List<dynamic>? ?? [])
          .map((e) => HypnogramStage.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

// -- Helper -----------------------------------------------------------------

String _todayDate() {
  final now = DateTime.now();
  final y = now.year.toString().padLeft(4, '0');
  final m = now.month.toString().padLeft(2, '0');
  final d = now.day.toString().padLeft(2, '0');
  return '$y-$m-$d';
}

// -- Provider ---------------------------------------------------------------

final sleepQualityProvider =
    AsyncNotifierProvider<SleepQualityNotifier, SleepQualityData?>(
  SleepQualityNotifier.new,
);

// -- Notifier ---------------------------------------------------------------

class SleepQualityNotifier extends AsyncNotifier<SleepQualityData?> {
  @override
  Future<SleepQualityData?> build() => _fetch();

  Future<void> refresh({String? date}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(date: date));
  }

  Future<SleepQualityData?> _fetch({String? date}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.sleepQualityScore,
      queryParameters: {'date': date ?? _todayDate()},
    );
    final json = responseJson(response);
    return SleepQualityData.fromJson(json);
  }
}
