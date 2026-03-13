/// Notifier Riverpod — Sommeil (LOT 6).
///
/// SleepNotifier : liste des sessions récentes + create.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/sleep_log.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final sleepProvider =
    AsyncNotifierProvider<SleepNotifier, List<SleepSession>>(
  SleepNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class SleepNotifier extends AsyncNotifier<List<SleepSession>> {
  @override
  Future<List<SleepSession>> build() => _fetchRecent();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchRecent);
  }

  Future<List<SleepSession>> _fetchRecent() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.sleepLog,
      queryParameters: {'limit': 14},
    );
    final json = responseJson(response);
    return (json['sessions'] as List<dynamic>? ?? [])
        .map((e) => SleepSession.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Enregistre une session de sommeil.
  ///
  /// [startAt] et [endAt] au format ISO-8601.
  Future<void> logSleep({
    required String startAt,
    required String endAt,
    required int perceivedQuality,
    String? notes,
  }) async {
    final client = ref.read(apiClientProvider);
    await client.post<void>(
      ApiConstants.sleepLog,
      data: {
        'start_at': startAt,
        'end_at': endAt,
        'perceived_quality': perceivedQuality,
        if (notes != null && notes.isNotEmpty) 'notes': notes,
      },
    );
    await refresh();
  }
}
