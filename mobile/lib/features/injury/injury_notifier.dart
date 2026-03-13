/// SOMA LOT 15 — Injury Risk Notifier.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:soma_mobile/core/api/api_client.dart';
import 'package:soma_mobile/core/models/injury_risk.dart';

final injuryRiskProvider =
    AsyncNotifierProvider<InjuryRiskNotifier, InjuryRisk>(
  InjuryRiskNotifier.new,
);

class InjuryRiskNotifier extends AsyncNotifier<InjuryRisk> {
  @override
  Future<InjuryRisk> build() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get('/injury/risk');
    return InjuryRisk.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.get('/injury/risk');
      state = AsyncValue.data(
        InjuryRisk.fromJson(response.data as Map<String, dynamic>),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
