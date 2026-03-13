/// Service QualityScorer — calcul des scores de qualité de mouvement (LOT 7).
///
/// Reçoit les données brutes de chaque frame et répétition pour calculer :
///   - [amplitudeScore]  : amplitude de mouvement atteinte vs référence
///   - [stabilityScore]  : cohérence de l'alignement corps entre frames
///   - [regularityScore] : régularité du rythme entre répétitions
///   - [overallScore]    : combinaison pondérée des 3 scores
///
/// Service pur sans dépendance Flutter, entièrement testable.
library;

import '../models/exercise_frame.dart';
import '../models/movement_quality.dart';

// ── Références amplitude par exercice ─────────────────────────────────────────

/// Angle de pic de référence (parfaite amplitude) pour chaque exercice.
/// Pour les exercices à ratio (JumpingJack), valeur en [0,1] multipliée par 100.
const Map<SupportedExercise, double> _kReferenceAmplitude = {
  SupportedExercise.squat: 90.0, // angle genou à 90° = parfait
  SupportedExercise.pushUp: 75.0, // angle coude à 75° = parfait
  SupportedExercise.plank: 175.0, // alignement à 175° = parfait (5° tolérance)
  SupportedExercise.jumpingJack: 0.8, // ratio ouverture bras = 0.8
  SupportedExercise.lunge: 90.0, // angle genou à 90° = parfait
  SupportedExercise.sitUp: 20.0, // angle hanche à 20° = parfait
};

/// Tolérance amplitude : ±% de l'angle de référence pour score 100.
const double _kAmplitudeTolerance = 0.20; // ±20%

/// Seuil stabilité : déviation d'alignement acceptable (degrés).
const double _kStabilityMaxDeviation = 20.0;

/// Nombre minimum de répétitions pour un score de régularité fiable.
const int _kMinRepsForRegularity = 3;

// ── QualityScorer ─────────────────────────────────────────────────────────────

class QualityScorer {
  final SupportedExercise exercise;

  // Données accumulées
  final List<double> _peakAngles = [];
  final List<DateTime> _repTimestamps = [];
  final List<double> _alignmentDeviations = []; // déviation depuis 180°
  int _framesAnalyzed = 0;

  QualityScorer({required this.exercise});

  // ── Alimentation ──────────────────────────────────────────────────────────

  /// Ajoute les données d'un frame analysé.
  ///
  /// [angles] : angles calculés du frame
  /// [coverageScore] : qualité de détection du frame [0,1]
  void addFrame(ExerciseAngles angles, double coverageScore) {
    if (coverageScore < 0.4) return; // frame trop peu fiable
    _framesAnalyzed++;

    final alignment = angles.bodyAlignmentAngle;
    if (alignment != null) {
      _alignmentDeviations.add((alignment - 180.0).abs());
    }
  }

  /// Appelé quand une répétition est comptabilisée.
  ///
  /// [peakAngle] : angle au pic de la répétition
  /// [timestamp] : moment de la répétition
  void addRep(double peakAngle, DateTime timestamp) {
    _peakAngles.add(peakAngle);
    _repTimestamps.add(timestamp);
  }

  /// Met à jour depuis l'état du RepCounter (synchronisation).
  void syncFromRepState({
    required List<double> peakAngles,
    required List<DateTime> repTimestamps,
  }) {
    // Ajoute uniquement les nouvelles entrées
    if (peakAngles.length > _peakAngles.length) {
      _peakAngles.addAll(
        peakAngles.sublist(_peakAngles.length),
      );
    }
    if (repTimestamps.length > _repTimestamps.length) {
      _repTimestamps.addAll(
        repTimestamps.sublist(_repTimestamps.length),
      );
    }
  }

  // ── Calcul scores ─────────────────────────────────────────────────────────

  /// Calcule le score de qualité final depuis les données accumulées.
  MovementQuality compute() {
    final amplitude = _computeAmplitudeScore();
    final stability = _computeStabilityScore();
    final regularity = _computeRegularityScore();
    final overall = _computeOverall(amplitude, stability, regularity);

    return MovementQuality(
      amplitudeScore: amplitude,
      stabilityScore: stability,
      regularityScore: regularity,
      overallScore: overall,
      framesAnalyzed: _framesAnalyzed,
      repsAnalyzed: _peakAngles.length,
    );
  }

  // ── Score amplitude ────────────────────────────────────────────────────────

  double _computeAmplitudeScore() {
    if (_peakAngles.isEmpty) return 0.0;

    final reference = _kReferenceAmplitude[exercise]!;

    // Calcule la qualité amplitude pour chaque rep
    final scores = _peakAngles.map((angle) {
      return _amplitudeForAngle(angle, reference);
    }).toList();

    return scores.reduce((a, b) => a + b) / scores.length;
  }

  double _amplitudeForAngle(double angle, double reference) {
    // Pour les exercices avec angle décroissant (sit-up, push-up, squat),
    // un angle plus petit (proche de la référence) est meilleur.
    // Pour le plank, angle proche de 180° est meilleur.
    // Pour jumping jack, ratio proche de 1.0 est meilleur.

    final isJumpingJack = exercise == SupportedExercise.jumpingJack;
    final isPlank = exercise == SupportedExercise.plank;

    if (isJumpingJack) {
      // angle est un ratio [0,1] — plus proche de reference, meilleur
      return (1.0 - (angle - reference).abs() / reference).clamp(0.0, 1.0) *
          100.0;
    }

    if (isPlank) {
      // Pour le plank, angle proche de 180° — tolérance ±kTolerance*reference
      final deviation = (angle - reference).abs();
      final maxDeviation = reference * _kAmplitudeTolerance * 2;
      return (1.0 - (deviation / maxDeviation).clamp(0.0, 1.0)) * 100.0;
    }

    // Exercices où un angle plus petit = plus profond = meilleur
    // (squat, push-up, lunge, sit-up)
    // Score 100 si angle <= reference, décroît sinon
    if (angle <= reference) return 100.0;
    final excess = angle - reference;
    final maxExcess = reference * 0.5; // au-delà de +50% → score 0
    return (1.0 - (excess / maxExcess).clamp(0.0, 1.0)) * 100.0;
  }

  // ── Score stabilité ────────────────────────────────────────────────────────

  double _computeStabilityScore() {
    if (_alignmentDeviations.isEmpty) {
      // Pas de données d'alignement (ex. jumping jack : pas d'alignement corps)
      // Retour score neutre
      return 70.0;
    }

    final avg =
        _alignmentDeviations.reduce((a, b) => a + b) /
            _alignmentDeviations.length;

    // Stabilité : déviation 0° → 100, déviation ≥ maxDeviation → 0
    return (1.0 - (avg / _kStabilityMaxDeviation).clamp(0.0, 1.0)) * 100.0;
  }

  // ── Score régularité ───────────────────────────────────────────────────────

  double _computeRegularityScore() {
    if (_repTimestamps.length < _kMinRepsForRegularity) {
      // Pas assez de données — score neutre
      return 60.0;
    }

    // Calcule les intervalles entre reps (en ms)
    final intervals = <int>[];
    for (var i = 1; i < _repTimestamps.length; i++) {
      intervals.add(
        _repTimestamps[i].difference(_repTimestamps[i - 1]).inMilliseconds,
      );
    }

    final mean =
        intervals.reduce((a, b) => a + b) / intervals.length;

    if (mean < 1) return 100.0; // Edge case

    // Coefficient de variation (CV) = stdDev / mean
    final variance = intervals
        .map((x) => (x - mean) * (x - mean))
        .reduce((a, b) => a + b) /
        intervals.length;
    final stdDev = variance < 0 ? 0.0 : _sqrt(variance);
    final cv = stdDev / mean;

    // CV 0 = parfait, CV > 0.5 = très irrégulier
    return (1.0 - (cv / 0.5).clamp(0.0, 1.0)) * 100.0;
  }

  // ── Score global ───────────────────────────────────────────────────────────

  double _computeOverall(
    double amplitude,
    double stability,
    double regularity,
  ) {
    // Pondération : amplitude 40%, stabilité 35%, régularité 25%
    return (amplitude * 0.40 + stability * 0.35 + regularity * 0.25)
        .clamp(0.0, 100.0);
  }

  // ── Utilitaire ─────────────────────────────────────────────────────────────

  /// Implémentation basique de sqrt (sans import dart:math pour testabilité).
  static double _sqrt(double x) {
    if (x <= 0) return 0.0;
    double result = x;
    for (var i = 0; i < 50; i++) {
      result = (result + x / result) / 2.0;
    }
    return result;
  }

  /// Remet à zéro tous les buffers.
  void reset() {
    _peakAngles.clear();
    _repTimestamps.clear();
    _alignmentDeviations.clear();
    _framesAnalyzed = 0;
  }
}
