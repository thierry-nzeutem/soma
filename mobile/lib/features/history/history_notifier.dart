/// Notifier Riverpod — Historique métriques (LOT 6).
///
/// MetricsHistoryNotifier : liste de métriques journalières sur une période.
/// Expose un sélecteur de période (7 / 30 / 90 jours).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/daily_metrics.dart';

// ── Période ───────────────────────────────────────────────────────────────────

enum HistoryPeriod {
  week(7, '7 jours'),
  month(30, '30 jours'),
  quarter(90, '90 jours');

  final int days;
  final String label;
  const HistoryPeriod(this.days, this.label);
}

// ── État ─────────────────────────────────────────────────────────────────────

class HistoryState {
  final HistoryPeriod period;
  final AsyncValue<List<DailyMetrics>> data;

  const HistoryState({
    this.period = HistoryPeriod.week,
    this.data = const AsyncLoading(),
  });

  HistoryState copyWith({
    HistoryPeriod? period,
    AsyncValue<List<DailyMetrics>>? data,
  }) =>
      HistoryState(
        period: period ?? this.period,
        data: data ?? this.data,
      );
}

// ── Provider ──────────────────────────────────────────────────────────────────

final historyProvider =
    StateNotifierProvider<MetricsHistoryNotifier, HistoryState>(
  (ref) => MetricsHistoryNotifier(ref),
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class MetricsHistoryNotifier extends StateNotifier<HistoryState> {
  final Ref _ref;

  MetricsHistoryNotifier(this._ref) : super(const HistoryState()) {
    _loadForPeriod(HistoryPeriod.week);
  }

  /// Change la période et recharge les données.
  Future<void> setPeriod(HistoryPeriod period) async {
    state = state.copyWith(period: period, data: const AsyncLoading());
    await _loadForPeriod(period);
  }

  Future<void> refresh() async {
    state = state.copyWith(data: const AsyncLoading());
    await _loadForPeriod(state.period);
  }

  Future<void> _loadForPeriod(HistoryPeriod period) async {
    try {
      final client = _ref.read(apiClientProvider);
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.metricsHistory,
        queryParameters: {'days': period.days},
      );
      final json = responseJson(response);
      final items = (json['history'] as List<dynamic>? ?? [])
          .map((e) => DailyMetrics.fromJson(e as Map<String, dynamic>))
          .toList();
      state = state.copyWith(data: AsyncData(items));
    } catch (e, st) {
      state = state.copyWith(data: AsyncError(e, st));
    }
  }
}
