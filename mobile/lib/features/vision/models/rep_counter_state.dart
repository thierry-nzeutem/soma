/// Modèle RepCounterState — état de la machine à états du compteur (LOT 7).
library;

// ── Phase d'exercice ──────────────────────────────────────────────────────────

/// Phase de la machine à états pour le comptage de répétitions.
enum ExercisePhase {
  /// Pose non détectée ou exercice non démarré.
  unknown,

  /// Position de départ / repos (debout pour squat, bras fermés pour JJ…).
  starting,

  /// En train d'aller vers la position de travail (descente squat, descente push-up…).
  descending,

  /// Position de travail maximale (bas du squat, bas de la pompe…).
  peak,

  /// En train de revenir (remontée squat, remontée pompe…).
  ascending,
}

// ── Extensions d'affichage ────────────────────────────────────────────────────

extension ExercisePhaseDisplay on ExercisePhase {
  String get label {
    switch (this) {
      case ExercisePhase.unknown:
        return 'Position non détectée';
      case ExercisePhase.starting:
        return 'Position départ';
      case ExercisePhase.descending:
        return 'Descente…';
      case ExercisePhase.peak:
        return 'Position basse';
      case ExercisePhase.ascending:
        return 'Remontée…';
    }
  }

  bool get isActive =>
      this == ExercisePhase.descending ||
      this == ExercisePhase.peak ||
      this == ExercisePhase.ascending;
}

// ── État complet du compteur ──────────────────────────────────────────────────

/// État immutable du compteur de répétitions.
class RepCounterState {
  final int count;
  final ExercisePhase phase;

  /// Timestamps des dernières répétitions (pour calcul régularité).
  final List<DateTime> repTimestamps;

  /// Angles au pic de chaque répétition (pour score amplitude).
  final List<double> peakAngles;

  const RepCounterState({
    this.count = 0,
    this.phase = ExercisePhase.unknown,
    this.repTimestamps = const [],
    this.peakAngles = const [],
  });

  RepCounterState copyWith({
    int? count,
    ExercisePhase? phase,
    List<DateTime>? repTimestamps,
    List<double>? peakAngles,
  }) =>
      RepCounterState(
        count: count ?? this.count,
        phase: phase ?? this.phase,
        repTimestamps: repTimestamps ?? this.repTimestamps,
        peakAngles: peakAngles ?? this.peakAngles,
      );

  /// Durée moyenne entre répétitions (null si < 2 reps).
  Duration? get avgRepDuration {
    if (repTimestamps.length < 2) return null;
    final diffs = <int>[];
    for (var i = 1; i < repTimestamps.length; i++) {
      diffs.add(repTimestamps[i]
          .difference(repTimestamps[i - 1])
          .inMilliseconds);
    }
    final avg = diffs.reduce((a, b) => a + b) / diffs.length;
    return Duration(milliseconds: avg.round());
  }
}
