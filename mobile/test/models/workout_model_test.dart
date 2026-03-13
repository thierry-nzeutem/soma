/// Tests parsing modèles Workout — LOT 6.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/workout.dart';

void main() {
  group('ExerciseLibrary', () {
    final json = {
      'id': 'ex1',
      'name': 'Bench Press',
      'name_fr': 'Développé couché',
      'category': 'strength',
      'muscle_groups': ['chest', 'triceps', 'shoulders'],
      'equipment_needed': ['barbell', 'bench'],
      'difficulty_level': 'intermediate',
    };

    test('fromJson parses all fields', () {
      final ex = ExerciseLibrary.fromJson(json);
      expect(ex.id, 'ex1');
      expect(ex.name, 'Bench Press');
      expect(ex.nameFr, 'Développé couché');
      expect(ex.muscleGroups, ['chest', 'triceps', 'shoulders']);
    });

    test('displayName returns nameFr when available', () {
      expect(ExerciseLibrary.fromJson(json).displayName, 'Développé couché');
    });

    test('displayName falls back to name', () {
      final j = Map<String, dynamic>.from(json)..remove('name_fr');
      expect(ExerciseLibrary.fromJson(j).displayName, 'Bench Press');
    });

    test('categoryLabel returns French label', () {
      expect(ExerciseLibrary.fromJson(json).categoryLabel, 'Force');
    });

    test('categoryLabel for cardio', () {
      final j = Map<String, dynamic>.from(json)..['category'] = 'cardio';
      expect(ExerciseLibrary.fromJson(j).categoryLabel, 'Cardio');
    });

    test('empty lists when missing', () {
      final minimal = {'id': 'ex2', 'name': 'Run'};
      final ex = ExerciseLibrary.fromJson(minimal);
      expect(ex.muscleGroups, isEmpty);
      expect(ex.equipmentNeeded, isEmpty);
    });
  });

  group('WorkoutSet', () {
    final json = {
      'id': 's1',
      'set_number': 1,
      'set_type': 'normal',
      'reps': 10,
      'weight_kg': 80.0,
      'is_pr': false,
      'is_deleted': false,
    };

    test('fromJson parses correctly', () {
      final s = WorkoutSet.fromJson(json);
      expect(s.reps, 10);
      expect(s.weightKg, 80.0);
      expect(s.isPr, isFalse);
    });

    test('display with weight', () {
      final s = WorkoutSet.fromJson(json);
      expect(s.display, contains('10'));
      expect(s.display, contains('80.0 kg'));
    });

    test('display without weight', () {
      final j = Map<String, dynamic>.from(json)
        ..['weight_kg'] = null
        ..['reps'] = 15;
      final s = WorkoutSet.fromJson(j);
      expect(s.display, contains('15'));
      expect(s.display, isNot(contains('kg')));
    });

    test('is_deleted defaults to false', () {
      final j = {'id': 's2', 'set_number': 1, 'set_type': 'warmup'};
      expect(WorkoutSet.fromJson(j).isDeleted, isFalse);
    });
  });

  group('ExerciseEntry', () {
    final json = {
      'id': 'ee1',
      'exercise_id': 'ex1',
      'exercise_name': 'Squat',
      'exercise_order': 1,
      'sets': [
        {
          'id': 's1',
          'set_number': 1,
          'set_type': 'normal',
          'reps': 8,
          'weight_kg': 100.0,
          'is_pr': false,
          'is_deleted': false,
        },
        {
          'id': 's2',
          'set_number': 2,
          'set_type': 'normal',
          'reps': 8,
          'weight_kg': 100.0,
          'is_pr': false,
          'is_deleted': true, // soft deleted
        },
        {
          'id': 's3',
          'set_number': 3,
          'set_type': 'normal',
          'reps': 6,
          'weight_kg': 110.0,
          'is_pr': true,
          'is_deleted': false,
        },
      ],
    };

    test('fromJson parses sets', () {
      final ee = ExerciseEntry.fromJson(json);
      expect(ee.exerciseName, 'Squat');
      // sets exclut les deleted
      expect(ee.sets.length, 2);
    });

    test('tonnage excludes deleted sets', () {
      final ee = ExerciseEntry.fromJson(json);
      // 8*100 + 6*110 = 800 + 660 = 1460
      expect(ee.tonnage, closeTo(1460.0, 0.1));
    });

    test('totalSets is count of non-deleted', () {
      final ee = ExerciseEntry.fromJson(json);
      expect(ee.totalSets, 2);
    });

    test('totalReps is sum of non-deleted', () {
      final ee = ExerciseEntry.fromJson(json);
      expect(ee.totalReps, 14);
    });
  });

  group('WorkoutSession', () {
    final json = {
      'id': 'session1',
      'session_type': 'strength',
      'location': 'gym',
      'status': 'completed',
      'started_at': '2026-03-07T09:00:00Z',
      'exercises': [],
    };

    test('fromJson parses correctly', () {
      final s = WorkoutSession.fromJson(json);
      expect(s.id, 'session1');
      expect(s.sessionType, 'strength');
      expect(s.isCompleted, isTrue);
      expect(s.isInProgress, isFalse);
    });

    test('typeLabel returns French label for strength', () {
      expect(WorkoutSession.fromJson(json).typeLabel, 'Force');
    });

    test('typeLabel for cardio', () {
      final j = Map<String, dynamic>.from(json)
        ..['session_type'] = 'cardio';
      expect(WorkoutSession.fromJson(j).typeLabel, 'Cardio');
    });

    test('statusLabel for in_progress', () {
      final j = Map<String, dynamic>.from(json)
        ..['status'] = 'in_progress';
      expect(WorkoutSession.fromJson(j).statusLabel, 'En cours');
    });

    test('locationLabel for home', () {
      final j = Map<String, dynamic>.from(json)..['location'] = 'home';
      expect(WorkoutSession.fromJson(j).locationLabel, 'Maison');
    });

    test('locationLabel for outdoor', () {
      final j = Map<String, dynamic>.from(json)
        ..['location'] = 'outdoor';
      expect(WorkoutSession.fromJson(j).locationLabel, 'Extérieur');
    });

    test('exercises list is parsed', () {
      final j = Map<String, dynamic>.from(json)
        ..['exercises'] = [
          {
            'id': 'ee1',
            'exercise_id': 'ex1',
            'exercise_name': 'Deadlift',
            'exercise_order': 1,
            'sets': [],
          },
        ];
      final s = WorkoutSession.fromJson(j);
      expect(s.exercises.length, 1);
      expect(s.exercises[0].exerciseName, 'Deadlift');
    });
  });
}
