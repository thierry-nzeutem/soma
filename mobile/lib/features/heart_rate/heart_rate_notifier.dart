/// Heart Rate Notifier — SOMA.
///
/// Gère le state des données cardiaques (analytics + timeline).
/// Providers :
///   hrAnalyticsProvider  → analytics (avg, resting, max, min, events) pour aujourd'hui
///   hrTimelineProvider   → timeline 24h pour aujourd'hui
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/heart_rate_analytics.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

String _todayDate() {
  final now = DateTime.now();
  final y = now.year.toString().padLeft(4, '0');
  final m = now.month.toString().padLeft(2, '0');
  final d = now.day.toString().padLeft(2, '0');
  return '$y-$m-$d';
}

// ── Provider Analytics ────────────────────────────────────────────────────────

final hrAnalyticsProvider =
    AsyncNotifierProvider<HRAnalyticsNotifier, HRAnalytics?>(
  HRAnalyticsNotifier.new,
);

class HRAnalyticsNotifier extends AsyncNotifier<HRAnalytics?> {
  @override
  Future<HRAnalytics?> build() => _fetch();

  Future<HRAnalytics?> _fetch({String? date}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.hrAnalytics,
      queryParameters: {'date': date ?? _todayDate()},
    );
    final data = responseJson(response);
    return HRAnalytics.fromJson(data);
  }

  Future<void> refresh({String? date}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(date: date));
  }
}

// ── Provider Timeline ─────────────────────────────────────────────────────────

final hrTimelineProvider =
    AsyncNotifierProvider<HRTimelineNotifier, HRTimeline?>(
  HRTimelineNotifier.new,
);

class HRTimelineNotifier extends AsyncNotifier<HRTimeline?> {
  @override
  Future<HRTimeline?> build() => _fetch();

  Future<HRTimeline?> _fetch({String? date}) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.hrTimeline,
      queryParameters: {'date': date ?? _todayDate()},
    );
    final data = responseJson(response);
    return HRTimeline.fromJson(data);
  }

  Future<void> refresh({String? date}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(date: date));
  }
}
