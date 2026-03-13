/// SOMA — Cardio Fitness (VO2max) Notifier.
///
/// Provider :
///   cardioFitnessProvider -> CardioFitnessResponse?
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/cardio_fitness.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final cardioFitnessProvider =
    AsyncNotifierProvider<CardioFitnessNotifier, CardioFitnessResponse?>(
  CardioFitnessNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class CardioFitnessNotifier extends AsyncNotifier<CardioFitnessResponse?> {
  @override
  Future<CardioFitnessResponse?> build() => _fetch();

  Future<CardioFitnessResponse?> _fetch() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.cardioFitness,
    );
    final data = responseJson(response);
    return CardioFitnessResponse.fromJson(data);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }
}
