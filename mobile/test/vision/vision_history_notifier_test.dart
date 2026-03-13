/// Tests unitaires VisionHistoryNotifier — LOT 8.
///
/// Couvre :
///   - VisionHistoryPeriod : valeurs et labels
///   - SupportedExerciseApiKey.toApiKey() extension
///   - VisionHistoryState : construction, copyWith, sentinel nullable
///   - Parsing List<VisionSession> depuis JSON backend simulé
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/features/vision/models/exercise_frame.dart';
import 'package:soma_mobile/features/vision/models/vision_session.dart';
import 'package:soma_mobile/features/vision/providers/vision_history_notifier.dart';

void main() {
  // ── VisionHistoryPeriod ───────────────────────────────────────────────────

  group('VisionHistoryPeriod', () {
    test('week : 7 jours, label "7 jours"', () {
      expect(VisionHistoryPeriod.week.days, 7);
      expect(VisionHistoryPeriod.week.label, '7 jours');
    });

    test('month : 30 jours, label "30 jours"', () {
      expect(VisionHistoryPeriod.month.days, 30);
      expect(VisionHistoryPeriod.month.label, '30 jours');
    });

    test('quarter : 90 jours, label "90 jours"', () {
      expect(VisionHistoryPeriod.quarter.days, 90);
      expect(VisionHistoryPeriod.quarter.label, '90 jours');
    });

    test('3 périodes disponibles', () {
      expect(VisionHistoryPeriod.values.length, 3);
    });
  });

  // ── SupportedExerciseApiKey.toApiKey() ───────────────────────────────────

  group('SupportedExerciseApiKey.toApiKey()', () {
    test('"Squat" → "squat"', () {
      expect(SupportedExercise.squat.toApiKey(), 'squat');
    });

    test('"Push-up" → "push_up" (tiret)', () {
      expect(SupportedExercise.pushUp.toApiKey(), 'push_up');
    });

    test('"Plank" → "plank"', () {
      expect(SupportedExercise.plank.toApiKey(), 'plank');
    });

    test('"Jumping Jack" → "jumping_jack" (espace → underscore)', () {
      expect(SupportedExercise.jumpingJack.toApiKey(), 'jumping_jack');
    });

    test('"Lunge" → "lunge"', () {
      expect(SupportedExercise.lunge.toApiKey(), 'lunge');
    });

    test('"Sit-up" → "sit_up" (tiret)', () {
      expect(SupportedExercise.sitUp.toApiKey(), 'sit_up');
    });
  });

  // ── VisionHistoryState ────────────────────────────────────────────────────

  group('VisionHistoryState', () {
    test('construction par défaut : period=month, filter=null, data=loading', () {
      const s = VisionHistoryState();
      expect(s.period, VisionHistoryPeriod.month);
      expect(s.exerciseFilter, isNull);
      expect(s.data, isA<AsyncLoading>());
    });

    test('copyWith : changement de period', () {
      const s = VisionHistoryState();
      final s2 = s.copyWith(period: VisionHistoryPeriod.week);
      expect(s2.period, VisionHistoryPeriod.week);
      expect(s2.exerciseFilter, isNull); // inchangé
    });

    test('copyWith : changement de exerciseFilter', () {
      const s = VisionHistoryState();
      final s2 = s.copyWith(exerciseFilter: SupportedExercise.squat);
      expect(s2.exerciseFilter, SupportedExercise.squat);
      expect(s2.period, VisionHistoryPeriod.month); // inchangé
    });

    test('copyWith : exerciseFilter peut être mis à null (sentinel)', () {
      const s = VisionHistoryState(
        exerciseFilter: SupportedExercise.pushUp,
      );
      // Appel explicite avec null → doit réinitialiser le filtre
      final s2 = s.copyWith(exerciseFilter: null);
      expect(s2.exerciseFilter, isNull);
    });

    test('copyWith sans args : aucun changement', () {
      final s = VisionHistoryState(
        period: VisionHistoryPeriod.quarter,
        exerciseFilter: SupportedExercise.squat,
        data: const AsyncValue.data([]),
      );
      final s2 = s.copyWith();
      expect(s2.period, s.period);
      expect(s2.exerciseFilter, s.exerciseFilter);
    });

    test('copyWith : data AsyncError', () {
      const s = VisionHistoryState();
      final s2 = s.copyWith(
        data: AsyncValue.error('error', StackTrace.empty),
      );
      expect(s2.data, isA<AsyncError>());
    });

    test('copyWith : data AsyncData avec liste', () {
      const s = VisionHistoryState();
      final sessions = <VisionSession>[];
      final s2 = s.copyWith(data: AsyncValue.data(sessions));
      expect(s2.data, isA<AsyncData<List<VisionSession>>>());
      s2.data.whenData((v) => expect(v, isEmpty));
    });
  });

  // ── Parsing JSON backend → List<VisionSession> ────────────────────────────

  group('Parsing JSON backend', () {
    /// Simule la réponse de GET /api/v1/vision/sessions (liste directe).
    List<Map<String, dynamic>> _makeBackendJson(int count) {
      return List.generate(count, (i) {
        return {
          'id': 'vs-${i + 1}',
          'exercise_type': SupportedExercise.values[i % 6].toApiKey(),
          'reps': 10 + i,
          'duration_seconds': 60 + i * 5,
          'amplitude_score': 70.0 + i,
          'stability_score': 65.0 + i,
          'regularity_score': 60.0 + i,
          'quality_score': 66.0 + i,
          'created_at': '2026-03-0${i + 1}T09:00:00.000',
          'metadata': <String, dynamic>{
            'frames_analyzed': 200 + i * 10,
            'reps_analyzed': 10 + i,
            'algorithm_version': 'v1.0',
          },
        };
      });
    }

    test('parsing 5 sessions : count correct', () {
      final raw = _makeBackendJson(5);
      final sessions =
          raw.map((e) => VisionSession.fromJson(e)).toList();
      expect(sessions.length, 5);
    });

    test('parsing 5 sessions : exercise_type round-trip', () {
      final raw = _makeBackendJson(6); // un de chaque exercice
      final sessions =
          raw.map((e) => VisionSession.fromJson(e)).toList();
      for (var i = 0; i < 6; i++) {
        expect(sessions[i].exercise, SupportedExercise.values[i]);
      }
    });

    test('parsing : created_at utilisé comme startedAt', () {
      final raw = _makeBackendJson(1);
      final s = VisionSession.fromJson(raw.first);
      expect(s.startedAt, DateTime(2026, 3, 1, 9, 0, 0));
    });

    test('parsing : id récupéré', () {
      final raw = _makeBackendJson(3);
      final sessions = raw.map((e) => VisionSession.fromJson(e)).toList();
      expect(sessions[0].id, 'vs-1');
      expect(sessions[1].id, 'vs-2');
      expect(sessions[2].id, 'vs-3');
    });

    test('parsing : isSaved = true car id présent', () {
      final raw = _makeBackendJson(1);
      final s = VisionSession.fromJson(raw.first);
      expect(s.isSaved, isTrue);
    });

    test('parsing : jumping_jack reconnu correctement', () {
      final j = <String, dynamic>{
        'id': 'vs-jj',
        'exercise_type': 'jumping_jack',
        'reps': 20,
        'duration_seconds': 60,
        'amplitude_score': 75.0,
        'stability_score': 70.0,
        'regularity_score': 65.0,
        'quality_score': 71.0,
        'created_at': '2026-03-07T08:00:00.000',
        'metadata': <String, dynamic>{
          'frames_analyzed': 300,
          'reps_analyzed': 20,
        },
      };
      final s = VisionSession.fromJson(j);
      expect(s.exercise, SupportedExercise.jumpingJack);
      expect(s.repCount, 20);
    });
  });

  // ── Provider autoDispose ──────────────────────────────────────────────────

  group('visionHistoryProvider', () {
    test('provider est défini (non-null)', () {
      // Vérifie la compilation et l'initialisation du provider
      // Le type autoDispose est validé statiquement lors de la compilation
      expect(visionHistoryProvider, isNotNull);
    });
  });
}
