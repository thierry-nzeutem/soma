/// Tests parsing modèle VisionSession + MovementQuality — LOT 7.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/features/vision/models/exercise_frame.dart';
import 'package:soma_mobile/features/vision/models/movement_quality.dart';
import 'package:soma_mobile/features/vision/models/vision_session.dart';

void main() {
  final _now = DateTime(2026, 3, 7, 10, 0, 0);

  final _q = MovementQuality(
    amplitudeScore: 80.0,
    stabilityScore: 75.0,
    regularityScore: 70.0,
    overallScore: 76.0,
    framesAnalyzed: 300,
    repsAnalyzed: 10,
  );

  // ── VisionSession — construction ──────────────────────────────────────────

  group('VisionSession', () {
    test('construction correcte', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 12,
        durationSeconds: 90,
        quality: _q,
        startedAt: _now,
        workoutSessionId: 'ws-123',
      );
      expect(s.exercise, SupportedExercise.squat);
      expect(s.repCount, 12);
      expect(s.durationSeconds, 90);
      expect(s.workoutSessionId, 'ws-123');
      expect(s.isSaved, isFalse);
    });

    test('durationLabel : 90s → "1m 30s"', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 90,
        quality: _q,
        startedAt: _now,
      );
      expect(s.durationLabel, '1m 30s');
    });

    test('durationLabel : 45s → "45s"', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 5,
        durationSeconds: 45,
        quality: _q,
        startedAt: _now,
      );
      expect(s.durationLabel, '45s');
    });

    test('durationLabel : 180s → "3m 00s"', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 20,
        durationSeconds: 180,
        quality: _q,
        startedAt: _now,
      );
      expect(s.durationLabel, '3m 00s');
    });

    test('isSaved = false sans id', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 5,
        durationSeconds: 30,
        quality: _q,
        startedAt: _now,
      );
      expect(s.isSaved, isFalse);
    });

    test('isSaved = true avec id', () {
      final s = VisionSession(
        id: 'abc-123',
        exercise: SupportedExercise.pushUp,
        repCount: 8,
        durationSeconds: 60,
        quality: _q,
        startedAt: _now,
      );
      expect(s.isSaved, isTrue);
    });
  });

  // ── VisionSession.toJson ──────────────────────────────────────────────────

  group('VisionSession.toJson', () {
    final q = MovementQuality(
      amplitudeScore: 82.0,
      stabilityScore: 78.0,
      regularityScore: 65.0,
      overallScore: 76.0,
      framesAnalyzed: 200,
      repsAnalyzed: 8,
    );

    test('exercise_type squat', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'squat');
    });

    test('exercise_type push_up (depuis Push-up)', () {
      final s = VisionSession(
        exercise: SupportedExercise.pushUp,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      // 'Push-up' → toLowerCase() → 'push-up' → replaceAll('-','_') → 'push_up'
      expect(s.toJson()['exercise_type'], 'push_up');
    });

    test('exercise_type sit_up (depuis Sit-up)', () {
      final s = VisionSession(
        exercise: SupportedExercise.sitUp,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'sit_up');
    });

    test('reps correct', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 15,
        durationSeconds: 90,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['reps'], 15);
    });

    test('duration_seconds correct', () {
      final s = VisionSession(
        exercise: SupportedExercise.plank,
        repCount: 0,
        durationSeconds: 45,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['duration_seconds'], 45);
    });

    test('scores inclus dans json', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      final json = s.toJson();
      expect(json['amplitude_score'], 82.0);
      expect(json['stability_score'], 78.0);
      expect(json['regularity_score'], 65.0);
      expect(json['quality_score'], 76.0); // maps overallScore
    });

    test('workout_session_id inclus si fourni', () {
      final s = VisionSession(
        exercise: SupportedExercise.lunge,
        repCount: 12,
        durationSeconds: 70,
        quality: q,
        startedAt: _now,
        workoutSessionId: 'ws-abc',
      );
      expect(s.toJson()['workout_session_id'], 'ws-abc');
    });

    test('workout_session_id absent si non fourni', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson().containsKey('workout_session_id'), isFalse);
    });

    test('metadata contient algorithm_version', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      final meta = s.toJson()['metadata'] as Map<String, dynamic>;
      expect(meta['algorithm_version'], 'v1.0');
    });

    test('metadata contient frames_analyzed et reps_analyzed', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      final meta = s.toJson()['metadata'] as Map<String, dynamic>;
      expect(meta['frames_analyzed'], 200);
      expect(meta['reps_analyzed'], 8);
    });
  });

  // ── VisionSession.fromJson ────────────────────────────────────────────────

  group('VisionSession.fromJson', () {
    final json = <String, dynamic>{
      'id': 'vs-001',
      'exercise_type': 'squat',
      'reps': 12,
      'duration_seconds': 80,
      'amplitude_score': 85.0,
      'stability_score': 72.0,
      'regularity_score': 68.0,
      'quality_score': 75.0,
      'workout_session_id': null,
      'started_at': '2026-03-07T10:00:00.000',
      'metadata': <String, dynamic>{
        'frames_analyzed': 240,
        'reps_analyzed': 12,
        'algorithm_version': 'v1.0',
      },
    };

    test('parses tous les champs', () {
      final s = VisionSession.fromJson(json);
      expect(s.id, 'vs-001');
      expect(s.exercise, SupportedExercise.squat);
      expect(s.repCount, 12);
      expect(s.durationSeconds, 80);
      expect(s.quality.amplitudeScore, 85.0);
      expect(s.quality.stabilityScore, 72.0);
      expect(s.quality.overallScore, 75.0);
    });

    test('framesAnalyzed et repsAnalyzed depuis metadata', () {
      final s = VisionSession.fromJson(json);
      expect(s.quality.framesAnalyzed, 240);
      expect(s.quality.repsAnalyzed, 12);
    });

    test('isSaved = true car id présent', () {
      final s = VisionSession.fromJson(json);
      expect(s.isSaved, isTrue);
    });

    test('parse push_up → pushUp', () {
      final j = Map<String, dynamic>.from(json)
        ..['exercise_type'] = 'push_up';
      expect(VisionSession.fromJson(j).exercise, SupportedExercise.pushUp);
    });

    test('parse sit_up → sitUp', () {
      final j = Map<String, dynamic>.from(json)
        ..['exercise_type'] = 'sit_up';
      expect(VisionSession.fromJson(j).exercise, SupportedExercise.sitUp);
    });

    test('exercise inconnue → fallback squat', () {
      final j = Map<String, dynamic>.from(json)
        ..['exercise_type'] = 'burpee';
      expect(VisionSession.fromJson(j).exercise, SupportedExercise.squat);
    });

    test('workout_session_id null si absent', () {
      final s = VisionSession.fromJson(json);
      expect(s.workoutSessionId, isNull);
    });
  });

  // ── MovementQuality ───────────────────────────────────────────────────────

  group('MovementQuality', () {
    test('const MovementQuality() → tous scores à 0', () {
      const q = MovementQuality();
      expect(q.amplitudeScore, 0.0);
      expect(q.stabilityScore, 0.0);
      expect(q.regularityScore, 0.0);
      expect(q.overallScore, 0.0);
    });

    test('hasEnoughData = false si reps < 2 et frames < 30', () {
      const q = MovementQuality(repsAnalyzed: 1, framesAnalyzed: 10);
      expect(q.hasEnoughData, isFalse);
    });

    test('hasEnoughData = true si reps >= 2', () {
      const q = MovementQuality(repsAnalyzed: 2, framesAnalyzed: 5);
      expect(q.hasEnoughData, isTrue);
    });

    test('hasEnoughData = true si frames >= 30', () {
      const q = MovementQuality(repsAnalyzed: 0, framesAnalyzed: 30);
      expect(q.hasEnoughData, isTrue);
    });

    test('overallLabel "Excellent" pour score >= 80', () {
      const q = MovementQuality(overallScore: 85.0);
      expect(q.overallLabel, 'Excellent');
    });

    test('overallLabel "Bon" pour score >= 65', () {
      const q = MovementQuality(overallScore: 70.0);
      expect(q.overallLabel, 'Bon');
    });

    test('overallLabel "Correct" pour score >= 50', () {
      const q = MovementQuality(overallScore: 55.0);
      expect(q.overallLabel, 'Correct');
    });

    test('overallLabel "À améliorer" pour score >= 35', () {
      const q = MovementQuality(overallScore: 40.0);
      expect(q.overallLabel, 'À améliorer');
    });

    test('overallLabel "Insuffisant" pour score < 35', () {
      const q = MovementQuality(overallScore: 20.0);
      expect(q.overallLabel, 'Insuffisant');
    });

    test('amplitudeLabel "Complète" pour >= 80', () {
      const q = MovementQuality(amplitudeScore: 82.0);
      expect(q.amplitudeLabel, 'Complète');
    });

    test('amplitudeLabel "Bonne" pour [60,80[', () {
      const q = MovementQuality(amplitudeScore: 65.0);
      expect(q.amplitudeLabel, 'Bonne');
    });

    test('stabilityLabel "Très stable" pour >= 80', () {
      const q = MovementQuality(stabilityScore: 85.0);
      expect(q.stabilityLabel, 'Très stable');
    });

    test('regularityLabel "Très régulier" pour >= 80', () {
      const q = MovementQuality(regularityScore: 90.0);
      expect(q.regularityLabel, 'Très régulier');
    });

    test('toJson / fromJson round-trip', () {
      final q = MovementQuality(
        amplitudeScore: 85.0,
        stabilityScore: 72.0,
        regularityScore: 68.0,
        overallScore: 76.0,
        framesAnalyzed: 200,
        repsAnalyzed: 8,
      );
      final json = q.toJson();
      final q2 = MovementQuality.fromJson(json);
      expect(q2.amplitudeScore, q.amplitudeScore);
      expect(q2.stabilityScore, q.stabilityScore);
      expect(q2.overallScore, q.overallScore);
      expect(q2.repsAnalyzed, q.repsAnalyzed);
      expect(q2.framesAnalyzed, q.framesAnalyzed);
    });

    test('copyWith ne modifie que les champs spécifiés', () {
      const q = MovementQuality(
        amplitudeScore: 80.0,
        stabilityScore: 70.0,
        overallScore: 75.0,
      );
      final q2 = q.copyWith(amplitudeScore: 90.0);
      expect(q2.amplitudeScore, 90.0);
      expect(q2.stabilityScore, 70.0); // inchangé
      expect(q2.overallScore, 75.0);   // inchangé
    });
  });

  // ── JumpingJack Bugfix + created_at fallback (LOT 8) ─────────────────────

  group('JumpingJack Bugfix (LOT 8)', () {
    const q = MovementQuality(
      amplitudeScore: 72.0,
      stabilityScore: 68.0,
      regularityScore: 65.0,
      overallScore: 69.0,
      framesAnalyzed: 180,
      repsAnalyzed: 15,
    );

    // ── toJson — snake_case avec espaces ET tirets ────────────────────

    test('toJson() jumping_jack — espace remplacé par underscore', () {
      final s = VisionSession(
        exercise: SupportedExercise.jumpingJack,
        repCount: 20,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      // "Jumping Jack" → toLowerCase → "jumping jack" → regex [-\s]→_ → "jumping_jack"
      expect(s.toJson()['exercise_type'], 'jumping_jack');
    });

    test('toJson() push_up — tiret remplacé (régression)', () {
      final s = VisionSession(
        exercise: SupportedExercise.pushUp,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'push_up');
    });

    test('toJson() sit_up — tiret remplacé (régression)', () {
      final s = VisionSession(
        exercise: SupportedExercise.sitUp,
        repCount: 12,
        durationSeconds: 50,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'sit_up');
    });

    test('toJson() squat — pas de tiret ni espace (régression)', () {
      final s = VisionSession(
        exercise: SupportedExercise.squat,
        repCount: 10,
        durationSeconds: 60,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'squat');
    });

    test('toJson() plank — pas de tiret ni espace (régression)', () {
      final s = VisionSession(
        exercise: SupportedExercise.plank,
        repCount: 0,
        durationSeconds: 45,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'plank');
    });

    test('toJson() lunge — pas de tiret ni espace (régression)', () {
      final s = VisionSession(
        exercise: SupportedExercise.lunge,
        repCount: 10,
        durationSeconds: 50,
        quality: q,
        startedAt: _now,
      );
      expect(s.toJson()['exercise_type'], 'lunge');
    });

    // ── fromJson — snake_case correspondance ─────────────────────────

    test('fromJson("jumping_jack") → jumpingJack ✓', () {
      final j = <String, dynamic>{
        'exercise_type': 'jumping_jack',
        'reps': 20,
        'duration_seconds': 60,
        'amplitude_score': 70.0,
        'stability_score': 65.0,
        'regularity_score': 60.0,
        'quality_score': 66.0,
        'started_at': '2026-03-07T10:00:00.000',
        'metadata': <String, dynamic>{},
      };
      expect(
        VisionSession.fromJson(j).exercise,
        SupportedExercise.jumpingJack,
      );
    });

    test('fromJson("jumping jack") avec espace → fallback squat (ancien bug)', () {
      // L'ancien backend recevait "jumping jack" (avant le fix)
      // → ne matche pas "jumping_jack" dans fromJson → fallback squat
      final j = <String, dynamic>{
        'exercise_type': 'jumping jack',
        'reps': 10,
        'duration_seconds': 30,
        'amplitude_score': 0.0,
        'stability_score': 0.0,
        'regularity_score': 0.0,
        'quality_score': 0.0,
        'metadata': <String, dynamic>{},
      };
      expect(VisionSession.fromJson(j).exercise, SupportedExercise.squat);
    });

    // ── Round-trip toJson/fromJson pour les 6 exercices ──────────────

    for (final ex in SupportedExercise.values) {
      test('round-trip toJson/fromJson ${ex.nameEn}', () {
        final s = VisionSession(
          exercise: ex,
          repCount: 10,
          durationSeconds: 60,
          quality: q,
          startedAt: _now,
        );
        final json = s.toJson();
        json['started_at'] = _now.toIso8601String();
        final s2 = VisionSession.fromJson(json);
        expect(s2.exercise, ex);
        expect(s2.repCount, s.repCount);
        expect(s2.durationSeconds, s.durationSeconds);
      });
    }

    // ── Fallback created_at / DateTime.now() ─────────────────────────

    test('fromJson : created_at utilisé si started_at absent', () {
      final j = <String, dynamic>{
        'exercise_type': 'squat',
        'reps': 5,
        'duration_seconds': 30,
        'amplitude_score': 0.0,
        'stability_score': 0.0,
        'regularity_score': 0.0,
        'quality_score': 0.0,
        'created_at': '2026-03-01T08:30:00.000',
        'metadata': <String, dynamic>{},
      };
      final s = VisionSession.fromJson(j);
      expect(s.startedAt, DateTime(2026, 3, 1, 8, 30, 0));
    });

    test('fromJson : DateTime.now() si started_at ET created_at absents', () {
      final before = DateTime.now();
      final j = <String, dynamic>{
        'exercise_type': 'squat',
        'reps': 5,
        'duration_seconds': 30,
        'amplitude_score': 0.0,
        'stability_score': 0.0,
        'regularity_score': 0.0,
        'quality_score': 0.0,
        'metadata': <String, dynamic>{},
      };
      final s = VisionSession.fromJson(j);
      final after = DateTime.now();
      expect(
        s.startedAt.millisecondsSinceEpoch,
        greaterThanOrEqualTo(
            before.subtract(const Duration(seconds: 1)).millisecondsSinceEpoch),
      );
      expect(
        s.startedAt.millisecondsSinceEpoch,
        lessThanOrEqualTo(
            after.add(const Duration(seconds: 1)).millisecondsSinceEpoch),
      );
    });
  });
}
