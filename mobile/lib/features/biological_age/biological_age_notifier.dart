/// Biological Age Notifier — SOMA LOT 11.
///
/// Gère le state de l'âge biologique de l'utilisateur.
/// Providers :
///   biologicalAgeProvider        → résultat courant âge biologique
///   biologicalAgeHistoryProvider → liste des snapshots historiques
///   biologicalAgeLeversProvider  → leviers d'amélioration longevité
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/biological_age.dart';

// ── Provider âge biologique courant ──────────────────────────────────────────

final biologicalAgeProvider =
    AsyncNotifierProvider<BiologicalAgeNotifier, BiologicalAgeResult?>(
  BiologicalAgeNotifier.new,
);

class BiologicalAgeNotifier extends AsyncNotifier<BiologicalAgeResult?> {
  @override
  Future<BiologicalAgeResult?> build() => _fetchBiologicalAge();

  Future<BiologicalAgeResult?> _fetchBiologicalAge() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.biologicalAge,
    );
    final data = responseJson(response);
    return BiologicalAgeResult.fromJson(data);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchBiologicalAge);
  }
}

// ── Provider historique ───────────────────────────────────────────────────────

final biologicalAgeHistoryProvider =
    AsyncNotifierProvider<BiologicalAgeHistoryNotifier,
        List<BiologicalAgeHistoryItem>>(
  BiologicalAgeHistoryNotifier.new,
);

class BiologicalAgeHistoryNotifier
    extends AsyncNotifier<List<BiologicalAgeHistoryItem>> {
  @override
  Future<List<BiologicalAgeHistoryItem>> build() => _fetchHistory();

  Future<List<BiologicalAgeHistoryItem>> _fetchHistory({int days = 90}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.biologicalAgeHistory,
      queryParameters: {'days': days},
    );
    final data = responseJson(response);
    final items = (data['snapshots'] as List<dynamic>? ?? [])
        .map((e) =>
            BiologicalAgeHistoryItem.fromJson(e as Map<String, dynamic>))
        .toList();
    return items;
  }

  Future<void> refresh({int days = 90}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchHistory(days: days));
  }
}

// ── Provider leviers ─────────────────────────────────────────────────────────

final biologicalAgeLeversProvider =
    AsyncNotifierProvider<BiologicalAgeLeversNotifier, List<BiologicalAgeLever>>(
  BiologicalAgeLeversNotifier.new,
);

class BiologicalAgeLeversNotifier
    extends AsyncNotifier<List<BiologicalAgeLever>> {
  @override
  Future<List<BiologicalAgeLever>> build() => _fetchLevers();

  Future<List<BiologicalAgeLever>> _fetchLevers() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.biologicalAgeLevers,
    );
    final data = responseJson(response);
    final levers = (data['levers'] as List<dynamic>? ?? [])
        .map((e) => BiologicalAgeLever.fromJson(e as Map<String, dynamic>))
        .toList();
    return levers;
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchLevers);
  }
}
