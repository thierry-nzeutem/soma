/// Notifier Riverpod pour le Score Longévité.
///
/// Charge GET /api/v1/scores/longevity?days=30 au démarrage.
/// Expose AsyncValue<LongevityScore> pour l'UI.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/longevity.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final longevityProvider =
    AsyncNotifierProvider<LongevityNotifier, LongevityScore>(
  LongevityNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class LongevityNotifier extends AsyncNotifier<LongevityScore> {
  @override
  Future<LongevityScore> build() => _fetchScore();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchScore);
  }

  Future<LongevityScore> _fetchScore({int days = 30}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.longevity,
      queryParameters: {'days': days},
    );
    final json = responseJson(response);
    return LongevityScore.fromJson(json);
  }
}
