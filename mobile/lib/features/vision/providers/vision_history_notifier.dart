/// VisionHistoryNotifier — historique des sessions Computer Vision (LOT 8).
///
/// Charge GET /api/v1/vision/sessions avec filtres exercice + période.
/// Suit le même pattern que MetricsHistoryNotifier.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/api_constants.dart';
import '../models/exercise_frame.dart';
import '../models/vision_session.dart';

// ── Période historique ────────────────────────────────────────────────────────

enum VisionHistoryPeriod {
  week(7, '7 jours'),
  month(30, '30 jours'),
  quarter(90, '90 jours');

  final int days;
  final String label;

  const VisionHistoryPeriod(this.days, this.label);
}

// ── Extension helper API key ──────────────────────────────────────────────────

extension SupportedExerciseApiKey on SupportedExercise {
  /// Convertit l'exercice en clé API snake_case acceptée par le backend.
  /// ex. "Jumping Jack" → "jumping_jack", "Push-up" → "push_up"
  String toApiKey() =>
      nameEn.toLowerCase().replaceAll(RegExp(r'[-\s]'), '_');
}

// ── État ─────────────────────────────────────────────────────────────────────

class VisionHistoryState {
  final VisionHistoryPeriod period;
  final SupportedExercise? exerciseFilter; // null = tous les exercices
  final AsyncValue<List<VisionSession>> data;

  const VisionHistoryState({
    this.period = VisionHistoryPeriod.month,
    this.exerciseFilter,
    this.data = const AsyncValue.loading(),
  });

  VisionHistoryState copyWith({
    VisionHistoryPeriod? period,
    Object? exerciseFilter = _sentinel,
    AsyncValue<List<VisionSession>>? data,
  }) {
    return VisionHistoryState(
      period: period ?? this.period,
      exerciseFilter: exerciseFilter == _sentinel
          ? this.exerciseFilter
          : exerciseFilter as SupportedExercise?,
      data: data ?? this.data,
    );
  }

  static const _sentinel = Object();
}

// ── Notifier ─────────────────────────────────────────────────────────────────

class VisionHistoryNotifier extends StateNotifier<VisionHistoryState> {
  final Ref _ref;

  VisionHistoryNotifier(this._ref) : super(const VisionHistoryState()) {
    _load();
  }

  // ── API publique ────────────────────────────────────────────────────────

  Future<void> setExerciseFilter(SupportedExercise? exercise) async {
    state = state.copyWith(
      exerciseFilter: exercise,
      data: const AsyncValue.loading(),
    );
    await _load();
  }

  Future<void> setPeriod(VisionHistoryPeriod period) async {
    state = state.copyWith(
      period: period,
      data: const AsyncValue.loading(),
    );
    await _load();
  }

  Future<void> refresh() async {
    state = state.copyWith(data: const AsyncValue.loading());
    await _load();
  }

  // ── Chargement ──────────────────────────────────────────────────────────

  Future<void> _load() async {
    try {
      final client = _ref.read(apiClientProvider);

      // Date de début (from_date)
      final fromDate = DateTime.now()
          .subtract(Duration(days: state.period.days));
      final fromDateStr =
          '${fromDate.year.toString().padLeft(4, '0')}-'
          '${fromDate.month.toString().padLeft(2, '0')}-'
          '${fromDate.day.toString().padLeft(2, '0')}';

      final params = <String, dynamic>{
        'from_date': fromDateStr,
        'limit': 200,
        if (state.exerciseFilter != null)
          'exercise_type': state.exerciseFilter!.toApiKey(),
      };

      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.visionSessions,
        queryParameters: params,
      );

      final json = responseJson(response);
      final raw = (json['sessions'] as List<dynamic>?) ?? <dynamic>[json];
      final sessions = raw
          .map((e) => VisionSession.fromJson(e as Map<String, dynamic>))
          .toList();

      // Tri du plus récent au plus ancien (already sorted by backend DESC)
      state = state.copyWith(data: AsyncValue.data(sessions));
    } catch (e, st) {
      state = state.copyWith(data: AsyncValue.error(e, st));
    }
  }
}

// ── Provider ─────────────────────────────────────────────────────────────────

/// Provider autoDispose : se libère quand l'écran historique est quitté.
final visionHistoryProvider = StateNotifierProvider.autoDispose<
    VisionHistoryNotifier, VisionHistoryState>(
  (ref) => VisionHistoryNotifier(ref),
);
