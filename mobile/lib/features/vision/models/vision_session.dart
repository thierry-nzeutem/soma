/// Modèle VisionSession — résumé d'une session vision complète (LOT 7).
///
/// Envoyé au backend pour persistance après validation par l'utilisateur.
library;

import 'exercise_frame.dart';
import 'movement_quality.dart';

// ── Session vision complète ───────────────────────────────────────────────────

class VisionSession {
  /// ID retourné par le backend après sauvegarde (null avant sauvegarde).
  final String? id;

  final SupportedExercise exercise;
  final int repCount;
  final int durationSeconds;
  final MovementQuality quality;
  final DateTime startedAt;

  /// ID de session workout à laquelle rattacher (optionnel).
  final String? workoutSessionId;

  /// Métadonnées supplémentaires (angles moyens, version algo…).
  final Map<String, dynamic> metadata;

  const VisionSession({
    this.id,
    required this.exercise,
    required this.repCount,
    required this.durationSeconds,
    required this.quality,
    required this.startedAt,
    this.workoutSessionId,
    this.metadata = const {},
  });

  // ── Getters utiles ────────────────────────────────────────────────────────

  String get durationLabel {
    final m = durationSeconds ~/ 60;
    final s = durationSeconds % 60;
    if (m == 0) return '${s}s';
    return '${m}m ${s.toString().padLeft(2, '0')}s';
  }

  bool get isSaved => id != null;

  // ── Sérialisation ─────────────────────────────────────────────────────────

  Map<String, dynamic> toJson() => {
        'exercise_type': exercise.nameEn.toLowerCase().replaceAll(RegExp(r'[-\s]'), '_'),
        'reps': repCount,
        'duration_seconds': durationSeconds,
        'amplitude_score': quality.amplitudeScore,
        'stability_score': quality.stabilityScore,
        'regularity_score': quality.regularityScore,
        'quality_score': quality.overallScore,
        'started_at': startedAt.toIso8601String(),
        if (workoutSessionId != null)
          'workout_session_id': workoutSessionId,
        'metadata': {
          'frames_analyzed': quality.framesAnalyzed,
          'reps_analyzed': quality.repsAnalyzed,
          'algorithm_version': 'v1.0',
          ...metadata,
        },
      };

  factory VisionSession.fromJson(Map<String, dynamic> json) {
    final exerciseStr = json['exercise_type'] as String? ?? 'squat';
    final exercise = SupportedExercise.values.firstWhere(
      (e) => e.nameEn.toLowerCase().replaceAll(RegExp(r'[-\s]'), '_') == exerciseStr,
      orElse: () => SupportedExercise.squat,
    );
    final meta = json['metadata'] as Map<String, dynamic>? ?? {};
    return VisionSession(
      id: json['id'] as String?,
      exercise: exercise,
      repCount: json['reps'] as int? ?? 0,
      durationSeconds: json['duration_seconds'] as int? ?? 0,
      quality: MovementQuality(
        amplitudeScore: (json['amplitude_score'] as num?)?.toDouble() ?? 0,
        stabilityScore: (json['stability_score'] as num?)?.toDouble() ?? 0,
        regularityScore: (json['regularity_score'] as num?)?.toDouble() ?? 0,
        overallScore: (json['quality_score'] as num?)?.toDouble() ?? 0,
        framesAnalyzed: meta['frames_analyzed'] as int? ?? 0,
        repsAnalyzed: meta['reps_analyzed'] as int? ?? 0,
      ),
      startedAt: json['started_at'] != null
          ? DateTime.parse(json['started_at'] as String)
          : json['created_at'] != null
              ? DateTime.parse(json['created_at'] as String)
              : DateTime.now(),
      workoutSessionId: json['workout_session_id'] as String?,
      metadata: meta,
    );
  }
}
