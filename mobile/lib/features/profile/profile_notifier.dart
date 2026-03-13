/// Notifier Riverpod — Profil utilisateur (LOT 6).
///
/// ProfileNotifier : chargement + mise à jour partielle (PATCH).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/profile.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final profileProvider =
    AsyncNotifierProvider<ProfileNotifier, UserProfile>(
  ProfileNotifier.new,
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class ProfileNotifier extends AsyncNotifier<UserProfile> {
  @override
  Future<UserProfile> build() => _fetchProfile();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchProfile);
  }

  Future<UserProfile> _fetchProfile() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.profile,
    );
    return UserProfile.fromJson(responseJson(response));
  }

  /// Met à jour les champs fournis dans [fields] (PATCH partiel).
  ///
  /// Exemple : `await ref.read(profileProvider.notifier).updateProfile({'first_name': 'Alice'})`
  Future<void> updateProfile(Map<String, dynamic> fields) async {
    final client = ref.read(apiClientProvider);
    final response = await client.patch<Map<String, dynamic>>(
      ApiConstants.profile,
      data: fields,
    );
    final updated = UserProfile.fromJson(responseJson(response));
    state = AsyncData(updated);
  }
}
