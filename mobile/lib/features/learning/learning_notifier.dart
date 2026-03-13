/// SOMA LOT 13 — Learning Profile Notifier.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:soma_mobile/core/api/api_client.dart';
import 'package:soma_mobile/core/models/learning_profile.dart';

final learningProfileProvider =
    AsyncNotifierProvider<LearningProfileNotifier, LearningProfile>(
  LearningProfileNotifier.new,
);

class LearningProfileNotifier extends AsyncNotifier<LearningProfile> {
  @override
  Future<LearningProfile> build() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get('/learning/profile');
    return LearningProfile.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> recompute() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      await client.post('/learning/recompute', data: {});
      final response = await client.get('/learning/profile');
      state = AsyncValue.data(
        LearningProfile.fromJson(response.data as Map<String, dynamic>),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
