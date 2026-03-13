import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';
import '../api/api_constants.dart';
import 'plan_models.dart';

final entitlementsProvider =
    AsyncNotifierProvider<EntitlementsNotifier, EntitlementsData>(
  EntitlementsNotifier.new,
);

class EntitlementsNotifier extends AsyncNotifier<EntitlementsData> {
  @override
  Future<EntitlementsData> build() => _fetch();

  Future<EntitlementsData> _fetch() async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.meEntitlements,
      );
      final data = responseJson(response);
      return EntitlementsData.fromJson(data);
    } catch (_) {
      // On error (unauthenticated, network), return free tier
      return EntitlementsData.free();
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }
}
