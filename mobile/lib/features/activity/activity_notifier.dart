/// SOMA — Activity Analytics Notifier.
///
/// Providers :
///   activityDayProvider    -> ActivityDayResponse
///   activityPeriodProvider -> ActivityPeriodResponse
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/activity_analytics.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

String _todayDate() {
  final now = DateTime.now();
  final y = now.year.toString().padLeft(4, '0');
  final m = now.month.toString().padLeft(2, '0');
  final d = now.day.toString().padLeft(2, '0');
  return '$y-$m-$d';
}

// ── Activity Day Provider ─────────────────────────────────────────────────────

final activityDayProvider =
    AsyncNotifierProvider<ActivityDayNotifier, ActivityDayResponse>(
  ActivityDayNotifier.new,
);

class ActivityDayNotifier extends AsyncNotifier<ActivityDayResponse> {
  @override
  Future<ActivityDayResponse> build() => _fetch();

  Future<ActivityDayResponse> _fetch({String? date}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.activityDay,
      queryParameters: {'date': date ?? _todayDate()},
    );
    return ActivityDayResponse.fromJson(responseJson(response));
  }

  Future<void> refresh({String? date}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(date: date));
  }
}

// ── Activity Period Provider (family by period) ───────────────────────────────

final activityPeriodProvider = AsyncNotifierProviderFamily<
    ActivityPeriodNotifier, ActivityPeriodResponse, String>(
  ActivityPeriodNotifier.new,
);

class ActivityPeriodNotifier
    extends FamilyAsyncNotifier<ActivityPeriodResponse, String> {
  @override
  Future<ActivityPeriodResponse> build(String arg) => _fetch(arg);

  Future<ActivityPeriodResponse> _fetch(String period) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.activityPeriod,
      queryParameters: {'period': period},
    );
    return ActivityPeriodResponse.fromJson(responseJson(response));
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(arg));
  }
}
