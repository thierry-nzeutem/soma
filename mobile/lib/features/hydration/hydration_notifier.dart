/// Notifier Riverpod — Hydratation (LOT 6).
///
/// HydrationNotifier : résumé du jour + quick-add ml.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/hydration.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final hydrationProvider =
    AsyncNotifierProvider<HydrationNotifier, HydrationSummary>(
  HydrationNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class HydrationNotifier extends AsyncNotifier<HydrationSummary> {
  @override
  Future<HydrationSummary> build() => _fetchToday();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchToday);
  }

  Future<HydrationSummary> _fetchToday() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.hydrationToday,
    );
    return HydrationSummary.fromJson(responseJson(response));
  }

  /// Ajoute une entrée hydratation (bouton rapide ou saisie manuelle).
  Future<void> addEntry({
    required int volumeMl,
    String beverageType = 'water',
    String? notes,
  }) async {
    final client = ref.read(apiClientProvider);
    await client.post<void>(
      ApiConstants.hydrationLog,
      data: {
        'volume_ml': volumeMl,
        'beverage_type': beverageType,
        if (notes != null) 'notes': notes,
      },
    );
    await refresh();
  }
}
