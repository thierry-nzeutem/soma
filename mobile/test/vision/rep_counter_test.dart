/// Tests RepCounter — machines à états pour comptage de répétitions (LOT 7).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/features/vision/models/exercise_frame.dart';
import 'package:soma_mobile/features/vision/models/rep_counter_state.dart';
import 'package:soma_mobile/features/vision/services/rep_counter.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

/// Angles avec seulement l'angle genou.
ExerciseAngles knee(double angle) =>
    ExerciseAngles(leftKneeAngle: angle, rightKneeAngle: angle);

/// Angles avec seulement l'angle coude.
ExerciseAngles elbow(double angle) =>
    ExerciseAngles(leftElbowAngle: angle, rightElbowAngle: angle);

/// Angles avec seulement l'angle hanche.
ExerciseAngles hip(double angle) =>
    ExerciseAngles(leftHipAngle: angle, rightHipAngle: angle);

/// Angles avec seulement l'alignement corps.
ExerciseAngles body(double angle) =>
    ExerciseAngles(bodyAlignmentAngle: angle);

/// Angles jumping jack.
ExerciseAngles jj(double arm, double leg) =>
    ExerciseAngles(armSpreadRatio: arm, legSpreadRatio: leg);

// ── Squat ─────────────────────────────────────────────────────────────────────

group('SquatRepCounter', () {
  late SquatRepCounter counter;

  setUp(() => counter = SquatRepCounter());

  test('état initial : unknown, count=0', () {
    expect(counter.state.phase, ExercisePhase.unknown);
    expect(counter.state.count, 0);
  });

  test('transition unknown → starting quand genou >= 155°', () {
    counter.update(knee(160.0));
    expect(counter.state.phase, ExercisePhase.starting);
  });

  test('reste unknown si genou < 155°', () {
    counter.update(knee(140.0));
    expect(counter.state.phase, ExercisePhase.unknown);
  });

  test('starting → descending quand genou < 145°', () {
    counter.update(knee(165.0)); // → starting
    counter.update(knee(140.0)); // → descending
    expect(counter.state.phase, ExercisePhase.descending);
  });

  test('descending → peak quand genou <= 115°', () {
    counter.update(knee(165.0)); // starting
    counter.update(knee(140.0)); // descending
    counter.update(knee(110.0)); // peak
    expect(counter.state.phase, ExercisePhase.peak);
  });

  test('peak → ascending avec count++ quand genou > 125°', () {
    counter.update(knee(165.0)); // starting
    counter.update(knee(140.0)); // descending
    counter.update(knee(110.0)); // peak
    counter.update(knee(130.0)); // ascending + count
    expect(counter.state.phase, ExercisePhase.ascending);
    expect(counter.state.count, 1);
  });

  test('rep complète : une remontée complète = 1 rep', () {
    counter.update(knee(165.0)); // starting
    counter.update(knee(140.0)); // descending
    counter.update(knee(110.0)); // peak
    counter.update(knee(130.0)); // ascending (count = 1)
    counter.update(knee(165.0)); // back to starting
    expect(counter.state.count, 1);
  });

  test('2 répétitions successives correctement comptées', () {
    // Rep 1
    counter.update(knee(165.0));
    counter.update(knee(140.0));
    counter.update(knee(108.0));
    counter.update(knee(130.0)); // count=1
    counter.update(knee(165.0));
    // Rep 2
    counter.update(knee(143.0));
    counter.update(knee(112.0));
    counter.update(knee(130.0)); // count=2
    expect(counter.state.count, 2);
  });

  test('peak enregistre l\'angle minimum', () {
    counter.update(knee(165.0));
    counter.update(knee(140.0));
    counter.update(knee(110.0));
    counter.update(knee(105.0)); // nouvel angle minimum au peak
    counter.update(knee(130.0)); // ascending → count
    expect(counter.state.peakAngles, [105.0]);
  });

  test('reset remet à zéro', () {
    counter.update(knee(165.0));
    counter.update(knee(140.0));
    counter.update(knee(110.0));
    counter.update(knee(130.0));
    counter.reset();
    expect(counter.state.count, 0);
    expect(counter.state.phase, ExercisePhase.unknown);
  });

  test('descente avortée sans atteindre peak → retour starting', () {
    counter.update(knee(165.0)); // starting
    counter.update(knee(140.0)); // descending
    counter.update(knee(165.0)); // remonté sans peak → starting
    expect(counter.state.phase, ExercisePhase.starting);
    expect(counter.state.count, 0);
  });

  test('angles null retournent l\'état inchangé', () {
    counter.update(knee(165.0)); // starting
    final stateBefore = counter.state;
    counter.update(ExerciseAngles.empty);
    expect(counter.state, stateBefore);
  });
});

// ── PushUp ────────────────────────────────────────────────────────────────────

group('PushUpRepCounter', () {
  late PushUpRepCounter counter;

  setUp(() => counter = PushUpRepCounter());

  test('état initial : unknown, count=0', () {
    expect(counter.state.phase, ExercisePhase.unknown);
    expect(counter.state.count, 0);
  });

  test('cycle complet = 1 rep', () {
    counter.update(elbow(160.0)); // starting (bras tendus)
    counter.update(elbow(135.0)); // descending
    counter.update(elbow(85.0));  // peak (bras fléchis)
    counter.update(elbow(105.0)); // ascending + count
    expect(counter.state.count, 1);
  });

  test('2 push-ups', () {
    void doPushUp() {
      counter.update(elbow(160.0));
      counter.update(elbow(135.0));
      counter.update(elbow(85.0));
      counter.update(elbow(105.0));
    }

    doPushUp();
    counter.update(elbow(155.0)); // retour starting
    doPushUp();
    expect(counter.state.count, 2);
  });

  test('peak enregistre l\'angle coude minimum', () {
    counter.update(elbow(160.0));
    counter.update(elbow(135.0));
    counter.update(elbow(80.0));
    counter.update(elbow(75.0)); // nouvel minimum
    counter.update(elbow(100.0));
    expect(counter.state.peakAngles.first, 75.0);
  });
});

// ── Plank ─────────────────────────────────────────────────────────────────────

group('PlankRepCounter', () {
  late PlankRepCounter counter;

  setUp(() => counter = PlankRepCounter());

  test('alignement correct → phase peak', () {
    counter.update(body(178.0)); // ±30° autour de 180°
    expect(counter.state.phase, ExercisePhase.peak);
  });

  test('hors alignement → phase starting', () {
    counter.update(body(140.0)); // >30° d'écart
    expect(counter.state.phase, ExercisePhase.starting);
  });

  test('heldFrames compte les frames alignées', () {
    counter.update(body(178.0));
    counter.update(body(176.0));
    counter.update(body(182.0));
    expect(counter.heldFrames, 3);
  });

  test('heldFrames ne compte pas les frames hors position', () {
    counter.update(body(178.0)); // aligned
    counter.update(body(140.0)); // not aligned
    counter.update(body(178.0)); // aligned
    expect(counter.heldFrames, 2);
  });

  test('reset remet heldFrames à 0', () {
    counter.update(body(178.0));
    counter.reset();
    expect(counter.heldFrames, 0);
  });

  test('count symbolique : 300 frames tenues = 1 count', () {
    for (var i = 0; i < 300; i++) {
      counter.update(body(178.0));
    }
    expect(counter.state.count, 1);
  });
});

// ── JumpingJack ───────────────────────────────────────────────────────────────

group('JumpingJackRepCounter', () {
  late JumpingJackRepCounter counter;

  setUp(() => counter = JumpingJackRepCounter());

  test('position fermée → starting', () {
    counter.update(jj(0.1, 0.1));
    expect(counter.state.phase, ExercisePhase.starting);
  });

  test('cycle complet = 1 rep', () {
    counter.update(jj(0.1, 0.1)); // starting
    counter.update(jj(0.6, 0.6)); // peak (open)
    counter.update(jj(0.2, 0.2)); // descending → starting + count
    expect(counter.state.count, 1);
  });

  test('2 jumping jacks', () {
    void doJJ() {
      counter.update(jj(0.1, 0.1));
      counter.update(jj(0.6, 0.6));
      counter.update(jj(0.2, 0.2));
    }

    doJJ();
    doJJ();
    expect(counter.state.count, 2);
  });

  test('bras ouverts mais jambes fermées → pas de peak', () {
    counter.update(jj(0.1, 0.1)); // starting
    counter.update(jj(0.6, 0.2)); // arm open, leg closed → ascending pas peak
    expect(counter.state.phase, ExercisePhase.ascending);
  });
});

// ── Lunge ─────────────────────────────────────────────────────────────────────

group('LungeRepCounter', () {
  late LungeRepCounter counter;

  setUp(() => counter = LungeRepCounter());

  test('cycle fente = 1 rep', () {
    counter.update(knee(165.0)); // starting
    counter.update(knee(140.0)); // descending
    counter.update(knee(105.0)); // peak
    counter.update(knee(120.0)); // ascending + count
    expect(counter.state.count, 1);
  });

  test('fallback droite si gauche absent', () {
    // Utilise rightKneeAngle car leftKneeAngle est null
    final counter2 = LungeRepCounter();
    counter2.update(
        ExerciseAngles(rightKneeAngle: 165.0)); // starting via rightKnee
    expect(counter2.state.phase, ExercisePhase.starting);
  });
});

// ── SitUp ─────────────────────────────────────────────────────────────────────

group('SitUpRepCounter', () {
  late SitUpRepCounter counter;

  setUp(() => counter = SitUpRepCounter());

  test('état initial : unknown', () {
    expect(counter.state.phase, ExercisePhase.unknown);
  });

  test('position allongée → starting', () {
    counter.update(hip(75.0)); // > kLying=70°
    expect(counter.state.phase, ExercisePhase.starting);
  });

  test('cycle sit-up complet = 1 rep', () {
    counter.update(hip(75.0)); // starting (allongé)
    counter.update(hip(55.0)); // ascending (monte)
    counter.update(hip(35.0)); // peak (assis)
    counter.update(hip(50.0)); // descending
    counter.update(hip(75.0)); // retour allongé → count
    expect(counter.state.count, 1);
  });
});

// ── RepCounterFactory ─────────────────────────────────────────────────────────

group('RepCounterFactory', () {
  test('crée un SquatRepCounter pour squat', () {
    final c = RepCounterFactory.create(SupportedExercise.squat);
    expect(c, isA<SquatRepCounter>());
  });

  test('crée un PushUpRepCounter pour pushUp', () {
    final c = RepCounterFactory.create(SupportedExercise.pushUp);
    expect(c, isA<PushUpRepCounter>());
  });

  test('crée un PlankRepCounter pour plank', () {
    final c = RepCounterFactory.create(SupportedExercise.plank);
    expect(c, isA<PlankRepCounter>());
  });

  test('crée un JumpingJackRepCounter pour jumpingJack', () {
    final c = RepCounterFactory.create(SupportedExercise.jumpingJack);
    expect(c, isA<JumpingJackRepCounter>());
  });

  test('crée un LungeRepCounter pour lunge', () {
    final c = RepCounterFactory.create(SupportedExercise.lunge);
    expect(c, isA<LungeRepCounter>());
  });

  test('crée un SitUpRepCounter pour sitUp', () {
    final c = RepCounterFactory.create(SupportedExercise.sitUp);
    expect(c, isA<SitUpRepCounter>());
  });
});
