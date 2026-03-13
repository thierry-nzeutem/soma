/// Notifiers Riverpod — Workout (LOT 6).
///
/// WorkoutSessionsNotifier : liste des sessions + create
/// sessionDetailProvider   : FutureProvider.family pour une session
/// ExercisesNotifier       : bibliothèque d'exercices (lazy load + search)
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/workout.dart';

// ── Liste des sessions ────────────────────────────────────────────────────────

final workoutSessionsProvider =
    AsyncNotifierProvider<WorkoutSessionsNotifier, List<WorkoutSession>>(
  WorkoutSessionsNotifier.new,
);

class WorkoutSessionsNotifier extends AsyncNotifier<List<WorkoutSession>> {
  @override
  Future<List<WorkoutSession>> build() => _fetchSessions();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchSessions);
  }

  Future<List<WorkoutSession>> _fetchSessions() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.sessions,
      queryParameters: {'limit': 30},
    );
    final json = responseJson(response);
    final items = (json['sessions'] as List<dynamic>? ?? [])
        .map((e) => WorkoutSession.fromJson(e as Map<String, dynamic>))
        .toList();
    return items;
  }

  /// Crée une nouvelle session et rafraîchit la liste.
  Future<String?> createSession(Map<String, dynamic> payload) async {
    final client = ref.read(apiClientProvider);
    final response = await client.post<Map<String, dynamic>>(
      ApiConstants.sessions,
      data: payload,
    );
    final created = WorkoutSession.fromJson(responseJson(response));
    await refresh();
    return created.id;
  }

  /// Complète une session (PATCH status=completed).
  Future<void> completeSession(String sessionId) async {
    final client = ref.read(apiClientProvider);
    await client.patch<void>(
      '${ApiConstants.sessions}/$sessionId',
      data: {'status': 'completed'},
    );
    await refresh();
  }
}

// ── Détail d'une session ──────────────────────────────────────────────────────

final sessionDetailProvider =
    FutureProvider.autoDispose.family<WorkoutSession, String>(
  (ref, sessionId) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      '${ApiConstants.sessions}/$sessionId',
    );
    return WorkoutSession.fromJson(responseJson(response));
  },
);

// ── Ajout d'un exercice dans une session ─────────────────────────────────────

/// Ajoute un exercice à une session ouverte et invalide le détail.
Future<void> addExerciseToSession(
  WidgetRef ref,
  String sessionId,
  Map<String, dynamic> payload,
) async {
  final client = ref.read(apiClientProvider);
  await client.post<void>(
    '${ApiConstants.sessions}/$sessionId/exercises',
    data: payload,
  );
  ref.invalidate(sessionDetailProvider(sessionId));
}

/// Enregistre une série dans un exercice de session.
Future<void> addSetToExercise(
  WidgetRef ref,
  String sessionId,
  String exerciseEntryId,
  Map<String, dynamic> payload,
) async {
  final client = ref.read(apiClientProvider);
  await client.post<void>(
    '${ApiConstants.sessions}/$sessionId/exercises/$exerciseEntryId/sets',
    data: payload,
  );
  ref.invalidate(sessionDetailProvider(sessionId));
}

// ── Bibliothèque d'exercices ──────────────────────────────────────────────────

/// État bibliothèque exercices (cache + filtre texte).
class ExercisesState {
  final bool isLoading;
  final List<ExerciseLibrary> all;
  final String filter;
  final String? error;

  const ExercisesState({
    this.isLoading = false,
    this.all = const [],
    this.filter = '',
    this.error,
  });

  List<ExerciseLibrary> get filtered {
    if (filter.isEmpty) return all;
    final q = filter.toLowerCase();
    return all
        .where((e) =>
            e.displayName.toLowerCase().contains(q) ||
            (e.category?.toLowerCase().contains(q) ?? false))
        .toList();
  }

  ExercisesState copyWith({
    bool? isLoading,
    List<ExerciseLibrary>? all,
    String? filter,
    String? error,
  }) =>
      ExercisesState(
        isLoading: isLoading ?? this.isLoading,
        all: all ?? this.all,
        filter: filter ?? this.filter,
        error: error,
      );
}

final exercisesProvider =
    StateNotifierProvider<ExercisesNotifier, ExercisesState>(
  (ref) => ExercisesNotifier(ref),
);

class ExercisesNotifier extends StateNotifier<ExercisesState> {
  final Ref _ref;

  ExercisesNotifier(this._ref) : super(const ExercisesState()) {
    _load();
  }

  Future<void> _load() async {
    if (state.all.isNotEmpty) return;
    state = state.copyWith(isLoading: true, error: null);
    try {
      final client = _ref.read(apiClientProvider);
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.exercises,
        queryParameters: {'limit': 500},
      );
      final json = responseJson(response);
      final items = (json['exercises'] as List<dynamic>? ?? [])
          .map((e) => ExerciseLibrary.fromJson(e as Map<String, dynamic>))
          .toList();
      state = state.copyWith(all: items, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setFilter(String q) => state = state.copyWith(filter: q);

  Future<void> reload() async {
    state = const ExercisesState();
    await _load();
  }
}
