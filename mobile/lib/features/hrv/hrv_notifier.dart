/// HRV Notifier - variabilite cardiaque et score de stress SOMA.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';

// ── Model ─────────────────────────────────────────────────────────────────────

class HRVDayPoint {
  final String date;
  final double? avgHrvMs;
  final double? minHrvMs;
  final double? maxHrvMs;
  final int sampleCount;
  const HRVDayPoint({required this.date, this.avgHrvMs, this.minHrvMs, this.maxHrvMs, this.sampleCount = 0});
  factory HRVDayPoint.fromJson(Map<String, dynamic> j) => HRVDayPoint(
    date: j['date'] as String,
    avgHrvMs: (j['avg_hrv_ms'] as num?)?.toDouble(),
    minHrvMs: (j['min_hrv_ms'] as num?)?.toDouble(),
    maxHrvMs: (j['max_hrv_ms'] as num?)?.toDouble(),
    sampleCount: (j['sample_count'] as int?) ?? 0,
  );
}

class HRVScore {
  final String date;
  final int? hrvScore;
  final double? avgHrvMs;
  final double? restingHrvMs;
  final double? trend7d;
  final int? stressScore;
  final String stressLevel;
  final String recoveryIndicator;
  final double? baseline7dMs;
  final List<HRVDayPoint> history;
  final String? recommendation;

  const HRVScore({
    required this.date,
    this.hrvScore,
    this.avgHrvMs,
    this.restingHrvMs,
    this.trend7d,
    this.stressScore,
    this.stressLevel = 'unknown',
    this.recoveryIndicator = 'unknown',
    this.baseline7dMs,
    this.history = const [],
    this.recommendation,
  });

  factory HRVScore.fromJson(Map<String, dynamic> j) => HRVScore(
    date: j['date'] as String,
    hrvScore: j['hrv_score'] as int?,
    avgHrvMs: (j['avg_hrv_ms'] as num?)?.toDouble(),
    restingHrvMs: (j['resting_hrv_ms'] as num?)?.toDouble(),
    trend7d: (j['trend_7d'] as num?)?.toDouble(),
    stressScore: j['stress_score'] as int?,
    stressLevel: j['stress_level'] as String? ?? 'unknown',
    recoveryIndicator: j['recovery_indicator'] as String? ?? 'unknown',
    baseline7dMs: (j['baseline_7d_ms'] as num?)?.toDouble(),
    history: (j['history'] as List<dynamic>? ?? []).map((e) => HRVDayPoint.fromJson(e as Map<String, dynamic>)).toList(),
    recommendation: j['recommendation'] as String?,
  );

  bool get hasData => avgHrvMs != null;
}

// ── Provider ──────────────────────────────────────────────────────────────────

final hrvScoreProvider = AsyncNotifierProvider<HRVScoreNotifier, HRVScore?>(HRVScoreNotifier.new);

class HRVScoreNotifier extends AsyncNotifier<HRVScore?> {
  @override
  Future<HRVScore?> build() => _fetch();

  Future<HRVScore?> _fetch({String? date}) async {
    final client = ref.read(apiClientProvider);
    final params = <String, dynamic>{};
    if (date != null) params['date_str'] = date;
    final response = await client.get<Map<String, dynamic>>(ApiConstants.hrvScore, queryParameters: params);
    final data = responseJson(response);
    return HRVScore.fromJson(data);
  }

  Future<void> refresh({String? date}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(date: date));
  }
}
