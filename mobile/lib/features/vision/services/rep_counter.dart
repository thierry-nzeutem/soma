/// Service RepCounter — machine à états pour comptage de répétitions (LOT 7).
///
/// Architecture :
///   - Interface abstraite [RepCounter] implémentée par 6 exercices concrets.
///   - État immutable [RepCounterState] mis à jour à chaque frame (≈30fps).
///   - Le comptage se déclenche lors de la transition peak→ascending.
///
/// Thresholds calibrés sur des mesures empiriques en 2D normalisé.
/// Service pur sans dépendance Flutter, entièrement testable.
library;

import '../models/exercise_frame.dart';
import '../models/rep_counter_state.dart';

// ── Interface abstraite ────────────────────────────────────────────────────────

/// Compteur de répétitions basé sur une machine à états angulaire.
abstract class RepCounter {
  /// État courant (immutable).
  RepCounterState get state;

  /// Met à jour la machine à états avec les angles du frame courant.
  /// Retourne le nouvel état.
  RepCounterState update(ExerciseAngles angles);

  /// Remet le compteur à zéro.
  RepCounterState reset();
}

// ── Utilitaire interne ─────────────────────────────────────────────────────────

/// Construit un nouvel état avec une répétition comptabilisée.
RepCounterState _countRep(
  RepCounterState s,
  ExercisePhase nextPhase,
  double peakAngle,
) =>
    s.copyWith(
      phase: nextPhase,
      count: s.count + 1,
      repTimestamps: [...s.repTimestamps, DateTime.now()],
      peakAngles: [...s.peakAngles, peakAngle],
    );

// ── Squat ────────────────────────────────────────────────────────────────────
// Angle genou (hanche–genou–cheville)
// STANDING > 155°  |  BOTTOM < 115°
// Cycle : starting → descending → peak → ascending (count++) → starting

class SquatRepCounter implements RepCounter {
  static const double _kStanding = 155.0;
  static const double _kBottom = 115.0;
  static const double _kHysteresis = 10.0;

  RepCounterState _state = const RepCounterState();
  double _peakAngle = 180.0;

  @override
  RepCounterState get state => _state;

  @override
  RepCounterState update(ExerciseAngles angles) {
    final knee = angles.kneeAngle;
    if (knee == null) return _state;
    _state = _transition(_state, knee);
    return _state;
  }

  RepCounterState _transition(RepCounterState s, double knee) {
    switch (s.phase) {
      case ExercisePhase.unknown:
        if (knee >= _kStanding) {
          return s.copyWith(phase: ExercisePhase.starting);
        }
        return s;

      case ExercisePhase.starting:
        if (knee < _kStanding - _kHysteresis) {
          return s.copyWith(phase: ExercisePhase.descending);
        }
        return s;

      case ExercisePhase.descending:
        if (knee <= _kBottom) {
          _peakAngle = knee;
          return s.copyWith(phase: ExercisePhase.peak);
        }
        // Avorté — remonté sans atteindre le bas
        if (knee >= _kStanding) {
          return s.copyWith(phase: ExercisePhase.starting);
        }
        return s;

      case ExercisePhase.peak:
        if (knee < _peakAngle) _peakAngle = knee; // suivi angle minimum
        if (knee > _kBottom + _kHysteresis) {
          // Commence à remonter → compte la répétition
          return _countRep(s, ExercisePhase.ascending, _peakAngle);
        }
        return s;

      case ExercisePhase.ascending:
        if (knee >= _kStanding) {
          return s.copyWith(phase: ExercisePhase.starting);
        }
        if (knee <= _kBottom) {
          // Redescente immédiate
          _peakAngle = knee;
          return s.copyWith(phase: ExercisePhase.peak);
        }
        return s;
    }
  }

  @override
  RepCounterState reset() {
    _state = const RepCounterState();
    _peakAngle = 180.0;
    return _state;
  }
}

// ── Push-up ──────────────────────────────────────────────────────────────────
// Angle coude (épaule–coude–poignet)
// UP > 150°  |  DOWN < 90°
// Cycle : starting → descending → peak → ascending (count++) → starting

class PushUpRepCounter implements RepCounter {
  static const double _kUp = 150.0;
  static const double _kDown = 90.0;
  static const double _kHysteresis = 10.0;

  RepCounterState _state = const RepCounterState();
  double _peakAngle = 180.0;

  @override
  RepCounterState get state => _state;

  @override
  RepCounterState update(ExerciseAngles angles) {
    final elbow = angles.elbowAngle;
    if (elbow == null) return _state;
    _state = _transition(_state, elbow);
    return _state;
  }

  RepCounterState _transition(RepCounterState s, double elbow) {
    switch (s.phase) {
      case ExercisePhase.unknown:
        if (elbow >= _kUp) {
          return s.copyWith(phase: ExercisePhase.starting);
        }
        return s;

      case ExercisePhase.starting:
        if (elbow < _kUp - _kHysteresis) {
          return s.copyWith(phase: ExercisePhase.descending);
        }
        return s;

      case ExercisePhase.descending:
        if (elbow <= _kDown) {
          _peakAngle = elbow;
          return s.copyWith(phase: ExercisePhase.peak);
        }
        if (elbow >= _kUp) {
          return s.copyWith(phase: ExercisePhase.starting);
        }
        return s;

      case ExercisePhase.peak:
        if (elbow < _peakAngle) _peakAngle = elbow;
        if (elbow > _kDown + _kHysteresis) {
          return _countRep(s, ExercisePhase.ascending, _peakAngle);
        }
        return s;

      case ExercisePhase.ascending:
        if (elbow >= _kUp) {
          return s.copyWith(phase: ExercisePhase.starting);
        }
        if (elbow <= _kDown) {
          _peakAngle = elbow;
          return s.copyWith(phase: ExercisePhase.peak);
        }
        return s;
    }
  }

  @override
  RepCounterState reset() {
    _state = const RepCounterState();
    _peakAngle = 180.0;
    return _state;
  }
}

// ── Plank ────────────────────────────────────────────────────────────────────
// bodyAlignmentAngle autour de 180° ± tolérance
// Timer-based : pas de comptage de reps, on expose [heldFrames].
// Une "rep" = 10 s tenu (300 frames @ 30fps) pour cohérence avec l'API.

class PlankRepCounter implements RepCounter {
  static const double _kAlignmentCenter = 180.0;
  static const double _kTolerance = 30.0; // ±30°
  static const int _kFramesPerRep = 300; // ~10 s @ 30fps

  RepCounterState _state = const RepCounterState();
  int _heldFrames = 0;
  double _sumDeviations = 0.0; // pour score stabilité

  @override
  RepCounterState get state => _state;

  /// Nombre de frames tenues en position correcte.
  int get heldFrames => _heldFrames;

  /// Déviation angulaire moyenne (qualité de l'alignement).
  double get avgDeviation =>
      _heldFrames > 0 ? _sumDeviations / _heldFrames : 0.0;

  @override
  RepCounterState update(ExerciseAngles angles) {
    final alignment = angles.bodyAlignmentAngle;
    if (alignment == null) return _state;

    final deviation = (alignment - _kAlignmentCenter).abs();
    final isAligned = deviation <= _kTolerance;

    if (isAligned) {
      _heldFrames++;
      _sumDeviations += deviation;
      // Chaque 300 frames tenues = 1 "rep" symbolique
      final newCount = _heldFrames ~/ _kFramesPerRep;
      if (newCount > _state.count) {
        _state = _state.copyWith(
          phase: ExercisePhase.peak,
          count: newCount,
          repTimestamps: [..._state.repTimestamps, DateTime.now()],
          peakAngles: [..._state.peakAngles, alignment],
        );
      } else {
        _state = _state.copyWith(phase: ExercisePhase.peak);
      }
    } else {
      // Hors position — pas de reset du compteur de frames intentionnel
      // (micro-déviations tolérées)
      _state = _state.copyWith(phase: ExercisePhase.starting);
    }

    return _state;
  }

  @override
  RepCounterState reset() {
    _state = const RepCounterState();
    _heldFrames = 0;
    _sumDeviations = 0.0;
    return _state;
  }
}

// ── Jumping Jack ─────────────────────────────────────────────────────────────
// Ratios ouverture bras + jambes [0-1]
// OPEN : arm > 0.5 && leg > 0.5
// CLOSED : arm < 0.3 && leg < 0.3
// Cycle : starting (closed) → ascending → peak (open) → descending → starting (count++)

class JumpingJackRepCounter implements RepCounter {
  static const double _kOpenThreshold = 0.5;
  static const double _kCloseThreshold = 0.3;

  RepCounterState _state = const RepCounterState();
  double _peakArmRatio = 0.0;

  @override
  RepCounterState get state => _state;

  @override
  RepCounterState update(ExerciseAngles angles) {
    final arm = angles.armSpreadRatio;
    final leg = angles.legSpreadRatio;
    if (arm == null || leg == null) return _state;
    _state = _transition(_state, arm, leg);
    return _state;
  }

  RepCounterState _transition(
    RepCounterState s,
    double arm,
    double leg,
  ) {
    final isOpen = arm >= _kOpenThreshold && leg >= _kOpenThreshold;
    final isClosed = arm <= _kCloseThreshold && leg <= _kCloseThreshold;

    switch (s.phase) {
      case ExercisePhase.unknown:
        if (isClosed) return s.copyWith(phase: ExercisePhase.starting);
        return s;

      case ExercisePhase.starting:
        if (!isClosed) {
          _peakArmRatio = arm;
          return s.copyWith(phase: ExercisePhase.ascending);
        }
        return s;

      case ExercisePhase.ascending:
        if (arm > _peakArmRatio) _peakArmRatio = arm;
        if (isOpen) return s.copyWith(phase: ExercisePhase.peak);
        if (isClosed) return s.copyWith(phase: ExercisePhase.starting); // avorté
        return s;

      case ExercisePhase.peak:
        if (!isOpen) return s.copyWith(phase: ExercisePhase.descending);
        return s;

      case ExercisePhase.descending:
        if (isClosed) {
          // Répétition complète
          return _countRep(s, ExercisePhase.starting, _peakArmRatio);
        }
        return s;
    }
  }

  @override
  RepCounterState reset() {
    _state = const RepCounterState();
    _peakArmRatio = 0.0;
    return _state;
  }
}

// ── Lunge ────────────────────────────────────────────────────────────────────
// Angle genou avant (hanche–genou–cheville)
// TOP > 155°  |  BOTTOM < 110°
// Cycle : starting → descending → peak → ascending (count++) → starting

class LungeRepCounter implements RepCounter {
  static const double _kTop = 155.0;
  static const double _kBottom = 110.0;
  static const double _kHysteresis = 10.0;

  RepCounterState _state = const RepCounterState();
  double _peakAngle = 180.0;

  @override
  RepCounterState get state => _state;

  @override
  RepCounterState update(ExerciseAngles angles) {
    // Préfère le genou gauche (jambe avant typique), fallback droite
    final knee = angles.leftKneeAngle ?? angles.rightKneeAngle;
    if (knee == null) return _state;
    _state = _transition(_state, knee);
    return _state;
  }

  RepCounterState _transition(RepCounterState s, double knee) {
    switch (s.phase) {
      case ExercisePhase.unknown:
        if (knee >= _kTop) return s.copyWith(phase: ExercisePhase.starting);
        return s;

      case ExercisePhase.starting:
        if (knee < _kTop - _kHysteresis) {
          return s.copyWith(phase: ExercisePhase.descending);
        }
        return s;

      case ExercisePhase.descending:
        if (knee <= _kBottom) {
          _peakAngle = knee;
          return s.copyWith(phase: ExercisePhase.peak);
        }
        if (knee >= _kTop) return s.copyWith(phase: ExercisePhase.starting);
        return s;

      case ExercisePhase.peak:
        if (knee < _peakAngle) _peakAngle = knee;
        if (knee > _kBottom + _kHysteresis) {
          return _countRep(s, ExercisePhase.ascending, _peakAngle);
        }
        return s;

      case ExercisePhase.ascending:
        if (knee >= _kTop) return s.copyWith(phase: ExercisePhase.starting);
        if (knee <= _kBottom) {
          _peakAngle = knee;
          return s.copyWith(phase: ExercisePhase.peak);
        }
        return s;
    }
  }

  @override
  RepCounterState reset() {
    _state = const RepCounterState();
    _peakAngle = 180.0;
    return _state;
  }
}

// ── Sit-up ───────────────────────────────────────────────────────────────────
// Angle hanche (épaule–hanche–genou)
// LYING > 70°  |  UP < 40°
// Cycle : starting (lying) → ascending (rising) → peak (up) → descending → starting (count++)
// Note : l'angle DIMINUE quand on monte (tronc se redresse).

class SitUpRepCounter implements RepCounter {
  static const double _kLying = 70.0;
  static const double _kUp = 40.0;
  static const double _kHysteresis = 8.0;

  RepCounterState _state = const RepCounterState();
  double _peakAngle = 90.0; // angle minimum atteint (le plus petit = le mieux)

  @override
  RepCounterState get state => _state;

  @override
  RepCounterState update(ExerciseAngles angles) {
    final hip = angles.hipAngle;
    if (hip == null) return _state;
    _state = _transition(_state, hip);
    return _state;
  }

  RepCounterState _transition(RepCounterState s, double hip) {
    switch (s.phase) {
      case ExercisePhase.unknown:
        // Position allongée = angle > kLying
        if (hip >= _kLying) return s.copyWith(phase: ExercisePhase.starting);
        return s;

      case ExercisePhase.starting:
        // On commence à monter quand l'angle diminue
        if (hip < _kLying - _kHysteresis) {
          _peakAngle = hip;
          return s.copyWith(phase: ExercisePhase.ascending);
        }
        return s;

      case ExercisePhase.ascending:
        if (hip < _peakAngle) _peakAngle = hip;
        if (hip <= _kUp) {
          return s.copyWith(phase: ExercisePhase.peak);
        }
        // Avorté — redescendu
        if (hip >= _kLying) return s.copyWith(phase: ExercisePhase.starting);
        return s;

      case ExercisePhase.peak:
        if (hip > _kUp + _kHysteresis) {
          return s.copyWith(phase: ExercisePhase.descending);
        }
        return s;

      case ExercisePhase.descending:
        if (hip >= _kLying) {
          // Retour en position allongée → rep complète
          return _countRep(s, ExercisePhase.starting, _peakAngle);
        }
        return s;
    }
  }

  @override
  RepCounterState reset() {
    _state = const RepCounterState();
    _peakAngle = 90.0;
    return _state;
  }
}

// ── Factory ───────────────────────────────────────────────────────────────────

/// Crée le compteur approprié pour l'exercice donné.
class RepCounterFactory {
  RepCounterFactory._();

  static RepCounter create(SupportedExercise exercise) {
    return switch (exercise) {
      SupportedExercise.squat => SquatRepCounter(),
      SupportedExercise.pushUp => PushUpRepCounter(),
      SupportedExercise.plank => PlankRepCounter(),
      SupportedExercise.jumpingJack => JumpingJackRepCounter(),
      SupportedExercise.lunge => LungeRepCounter(),
      SupportedExercise.sitUp => SitUpRepCounter(),
    };
  }
}
