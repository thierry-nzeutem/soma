/// Adaptive Nutrition Notifier — SOMA LOT 11.
///
/// Gère le state du plan nutritionnel adaptatif du jour.
/// Providers :
///   adaptiveNutritionProvider → plan nutritionnel adaptatif du jour
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/adaptive_nutrition.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final adaptiveNutritionProvider =
    AsyncNotifierProvider<AdaptiveNutritionNotifier, AdaptiveNutritionPlan?>(
  AdaptiveNutritionNotifier.new,
);

// ── Notifier ─────────────────────────────────────────────────────────────────

class AdaptiveNutritionNotifier extends AsyncNotifier<AdaptiveNutritionPlan?> {
  @override
  Future<AdaptiveNutritionPlan?> build() => _fetchPlan();

  Future<AdaptiveNutritionPlan?> _fetchPlan() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.adaptiveNutritionPlan,
    );
    final data = responseJson(response);
    return AdaptiveNutritionPlan.fromJson(data);
  }

  /// Recharge le plan depuis l'API.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchPlan);
  }

  /// Force le recalcul côté serveur et recharge.
  Future<void> recompute() async {
    state = const AsyncLoading();
    try {
      final client = ref.read(apiClientProvider);
      await client.post<Map<String, dynamic>>(
        ApiConstants.adaptiveNutritionRecompute,
        data: {},
      );
      state = await AsyncValue.guard(_fetchPlan);
    } catch (e, st) {
      state = AsyncError(e, st);
    }
  }
}
