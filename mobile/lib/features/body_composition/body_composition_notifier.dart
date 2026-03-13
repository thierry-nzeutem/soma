/// SOMA — Body Composition Notifier.
///
/// Providers :
///   compositionTrendProvider(period) → CompositionTrendResponse
///   weightTrendProvider              → WeightTrendResponse
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/body_composition.dart';

// ── Composition Trend (family by period) ──────────────────────────────────────

final compositionTrendProvider = AsyncNotifierProviderFamily<
    CompositionTrendNotifier, CompositionTrendResponse, String>(
  CompositionTrendNotifier.new,
);

class CompositionTrendNotifier
    extends FamilyAsyncNotifier<CompositionTrendResponse, String> {
  @override
  Future<CompositionTrendResponse> build(String arg) =>
      _fetch(arg);

  Future<CompositionTrendResponse> _fetch(String period) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.bodyCompositionTrend,
      queryParameters: {'period': period},
    );
    return CompositionTrendResponse.fromJson(responseJson(response));
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(arg));
  }
}

// ── Weight Trend ──────────────────────────────────────────────────────────────

final weightTrendProvider =
    AsyncNotifierProvider<WeightTrendNotifier, WeightTrendResponse>(
  WeightTrendNotifier.new,
);

class WeightTrendNotifier extends AsyncNotifier<WeightTrendResponse> {
  @override
  Future<WeightTrendResponse> build() => _fetch();

  Future<WeightTrendResponse> _fetch({String period = 'week'}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.bodyWeightTrend,
      queryParameters: {'period': period},
    );
    return WeightTrendResponse.fromJson(responseJson(response));
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }
}
