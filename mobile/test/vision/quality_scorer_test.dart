/// Tests QualityScorer — calcul des scores de qualité (LOT 7).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/features/vision/models/exercise_frame.dart';
import 'package:soma_mobile/features/vision/services/quality_scorer.dart';

void main() {
  // ── Tests initiaux ────────────────────────────────────────────────────────

  group('QualityScorer — état initial', () {
    test('compute sans données retourne score 0', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final q = scorer.compute();
      expect(q.amplitudeScore, 0.0);
      expect(q.framesAnalyzed, 0);
      expect(q.repsAnalyzed, 0);
    });

    test('hasEnoughData est false sans données', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final q = scorer.compute();
      expect(q.hasEnoughData, isFalse);
    });
  });

  // ── Score amplitude ───────────────────────────────────────────────────────

  group('QualityScorer — amplitude', () {
    test('squat avec angle parfait (90°) → score 100', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      scorer.addRep(90.0, DateTime.now()); // exactement la référence
      final q = scorer.compute();
      expect(q.amplitudeScore, closeTo(100.0, 0.1));
    });

    test('squat avec angle insuffisant (130°) → score réduit', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      scorer.addRep(130.0, DateTime.now()); // trop haut, amplitude limitée
      final q = scorer.compute();
      expect(q.amplitudeScore, lessThan(100.0));
      expect(q.amplitudeScore, greaterThan(0.0));
    });

    test('push-up avec angle parfait (75°) → score 100', () {
      final scorer = QualityScorer(exercise: SupportedExercise.pushUp);
      scorer.addRep(75.0, DateTime.now());
      final q = scorer.compute();
      expect(q.amplitudeScore, closeTo(100.0, 0.1));
    });

    test('plank avec alignement parfait (175°) → score élevé', () {
      final scorer = QualityScorer(exercise: SupportedExercise.plank);
      scorer.addRep(175.0, DateTime.now());
      final q = scorer.compute();
      expect(q.amplitudeScore, greaterThan(70.0));
    });

    test('amplitude 0 si aucune rep', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final q = scorer.compute();
      expect(q.amplitudeScore, 0.0);
    });

    test('amplitude = moyenne de plusieurs reps', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      // Angle parfait + angle insuffisant → score intermédiaire
      scorer.addRep(90.0, DateTime.now()); // score 100
      scorer.addRep(135.0, DateTime.now()); // score 30
      final q = scorer.compute();
      expect(q.amplitudeScore, greaterThan(30.0));
      expect(q.amplitudeScore, lessThan(100.0));
    });
  });

  // ── Score stabilité ───────────────────────────────────────────────────────

  group('QualityScorer — stabilité', () {
    test('frames avec alignement parfait (180°) → stabilité 100', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      for (var i = 0; i < 10; i++) {
        scorer.addFrame(
          const ExerciseAngles(bodyAlignmentAngle: 180.0),
          0.9,
        );
      }
      final q = scorer.compute();
      expect(q.stabilityScore, closeTo(100.0, 0.1));
    });

    test('frames avec déviation importante → stabilité réduite', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      for (var i = 0; i < 10; i++) {
        scorer.addFrame(
          const ExerciseAngles(bodyAlignmentAngle: 155.0), // 25° d'écart
          0.9,
        );
      }
      final q = scorer.compute();
      expect(q.stabilityScore, lessThan(100.0));
    });

    test('frames avec coverage < 0.4 ignorées', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      for (var i = 0; i < 10; i++) {
        scorer.addFrame(
          const ExerciseAngles(bodyAlignmentAngle: 150.0),
          0.3, // < 0.4 → ignoré
        );
      }
      final q = scorer.compute();
      expect(q.framesAnalyzed, 0);
    });
  });

  // ── Score régularité ──────────────────────────────────────────────────────

  group('QualityScorer — régularité', () {
    test('reps régulières (2s d\'intervalle) → score élevé', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final base = DateTime(2026, 3, 7, 10, 0, 0);
      scorer.addRep(90.0, base);
      scorer.addRep(90.0, base.add(const Duration(seconds: 2)));
      scorer.addRep(90.0, base.add(const Duration(seconds: 4)));
      scorer.addRep(90.0, base.add(const Duration(seconds: 6)));
      final q = scorer.compute();
      expect(q.regularityScore, greaterThan(80.0));
    });

    test('reps irrégulières → score réduit', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final base = DateTime(2026, 3, 7, 10, 0, 0);
      scorer.addRep(90.0, base);
      scorer.addRep(90.0, base.add(const Duration(seconds: 1)));
      scorer.addRep(90.0, base.add(const Duration(seconds: 10)));
      scorer.addRep(90.0, base.add(const Duration(seconds: 11)));
      final q = scorer.compute();
      expect(q.regularityScore, lessThan(80.0));
    });

    test('moins de 3 reps → score neutre (60)', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      scorer.addRep(90.0, DateTime.now());
      scorer.addRep(90.0, DateTime.now().add(const Duration(seconds: 2)));
      final q = scorer.compute();
      expect(q.regularityScore, closeTo(60.0, 0.1));
    });
  });

  // ── Score global ──────────────────────────────────────────────────────────

  group('QualityScorer — score global', () {
    test('overall est la combinaison pondérée des 3 scores', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      // Ajout de données pour avoir un score non-neutre
      final base = DateTime(2026, 3, 7, 10, 0, 0);
      for (var i = 0; i < 5; i++) {
        scorer.addRep(90.0, base.add(Duration(seconds: i * 2)));
        scorer.addFrame(
          const ExerciseAngles(bodyAlignmentAngle: 180.0),
          0.9,
        );
      }
      final q = scorer.compute();
      // overall = amplitude*0.4 + stability*0.35 + regularity*0.25
      final expected =
          q.amplitudeScore * 0.40 + q.stabilityScore * 0.35 + q.regularityScore * 0.25;
      expect(q.overallScore, closeTo(expected, 0.1));
    });

    test('overall clamped à [0, 100]', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final q = scorer.compute();
      expect(q.overallScore, greaterThanOrEqualTo(0.0));
      expect(q.overallScore, lessThanOrEqualTo(100.0));
    });
  });

  // ── syncFromRepState ──────────────────────────────────────────────────────

  group('QualityScorer.syncFromRepState', () {
    test('ajoute uniquement les nouvelles entrées', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      final t1 = DateTime.now();
      final t2 = t1.add(const Duration(seconds: 2));

      // Première sync : 1 rep
      scorer.syncFromRepState(peakAngles: [90.0], repTimestamps: [t1]);
      // Deuxième sync : 2 reps — ne doit ajouter que la 2ème
      scorer.syncFromRepState(
          peakAngles: [90.0, 85.0], repTimestamps: [t1, t2]);

      final q = scorer.compute();
      expect(q.repsAnalyzed, 2);
    });
  });

  // ── reset ─────────────────────────────────────────────────────────────────

  group('QualityScorer.reset', () {
    test('reset efface toutes les données', () {
      final scorer = QualityScorer(exercise: SupportedExercise.squat);
      scorer.addRep(90.0, DateTime.now());
      scorer.addFrame(
          const ExerciseAngles(bodyAlignmentAngle: 180.0), 0.9);
      scorer.reset();
      final q = scorer.compute();
      expect(q.framesAnalyzed, 0);
      expect(q.repsAnalyzed, 0);
      expect(q.amplitudeScore, 0.0);
    });
  });
}
