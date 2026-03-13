/// Notifier Riverpod — Analyse du Sommeil (BATCH 6).
///
/// Fetches `GET /sleep/analysis` and exposes [SleepAnalysisResult].
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/sleep_analysis.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final sleepAnalysisProvider =
    AsyncNotifierProvider<SleepAnalysisNotifier, SleepAnalysisResult>(
  SleepAnalysisNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class SleepAnalysisNotifier extends AsyncNotifier<SleepAnalysisResult> {
  @override
  Future<SleepAnalysisResult> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<SleepAnalysisResult> _fetch({int days = 14}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.sleepAnalysis,
      queryParameters: {'days': days},
    );
    final json = responseJson(response);
    return SleepAnalysisResult.fromJson(json);
  }
}
