/// Motion Intelligence Notifier — SOMA LOT 11.
///
/// Gère le state de l'analyse de la qualité du mouvement.
/// Providers :
///   motionProvider        → résumé motion intelligence du jour
///   motionHistoryProvider → liste des snapshots historiques
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/motion_intelligence.dart';

// ── Provider résumé motion ────────────────────────────────────────────────────

final motionProvider =
    AsyncNotifierProvider<MotionNotifier, MotionIntelligenceResult?>(
  MotionNotifier.new,
);

class MotionNotifier extends AsyncNotifier<MotionIntelligenceResult?> {
  @override
  Future<MotionIntelligenceResult?> build() => _fetchMotionSummary();

  Future<MotionIntelligenceResult?> _fetchMotionSummary({int days = 30}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.motionSummary,
      queryParameters: {'days': days},
    );
    final data = responseJson(response);
    return MotionIntelligenceResult.fromJson(data);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchMotionSummary);
  }
}

// ── Provider historique motion ────────────────────────────────────────────────

final motionHistoryProvider =
    AsyncNotifierProvider<MotionHistoryNotifier, List<MotionHistoryItem>>(
  MotionHistoryNotifier.new,
);

class MotionHistoryNotifier extends AsyncNotifier<List<MotionHistoryItem>> {
  @override
  Future<List<MotionHistoryItem>> build() => _fetchHistory();

  Future<List<MotionHistoryItem>> _fetchHistory({int days = 90}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.motionHistory,
      queryParameters: {'days': days},
    );
    final data = responseJson(response);
    final items = (data['snapshots'] as List<dynamic>? ?? [])
        .map((e) => MotionHistoryItem.fromJson(e as Map<String, dynamic>))
        .toList();
    return items;
  }

  Future<void> refresh({int days = 90}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchHistory(days: days));
  }
}
