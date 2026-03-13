/// Service ExerciseClassifier — validation de la position dans le cadre (LOT 7).
///
/// V1 : l'utilisateur choisit l'exercice manuellement (pas d'auto-détection).
/// Ce service valide uniquement que :
///   1. La pose est détectable (landmarks suffisants)
///   2. Les landmarks requis pour l'exercice sont présents et fiables
///   3. L'orientation / position de base semble correcte
///
/// Retourne un [ClassificationResult] avec feedback lisible.
/// Service pur sans dépendance Flutter, entièrement testable.
library;

import '../models/exercise_frame.dart';
import '../models/pose_landmark.dart';

// ── Résultat de classification ─────────────────────────────────────────────────

/// Résultat de la validation de position pour un exercice.
class ClassificationResult {
  /// Exercice sélectionné par l'utilisateur.
  final SupportedExercise exercise;

  /// Vrai si la pose est exploitable pour cet exercice.
  final bool isValid;

  /// Score de confiance de la détection [0, 1].
  final double confidence;

  /// Message de feedback à afficher à l'utilisateur.
  final String feedback;

  const ClassificationResult({
    required this.exercise,
    required this.isValid,
    required this.confidence,
    required this.feedback,
  });

  /// Pose insuffisamment détectée (landmarks manquants).
  const ClassificationResult.noPose(SupportedExercise ex)
      : exercise = ex,
        isValid = false,
        confidence = 0.0,
        feedback = 'Position non détectée. Reculez et restez dans le cadre.';
}

// ── Landmarks requis par exercice ─────────────────────────────────────────────

const Map<SupportedExercise, List<VisionLandmarkType>> _kRequiredLandmarks = {
  SupportedExercise.squat: [
    VisionLandmarkType.leftHip,
    VisionLandmarkType.leftKnee,
    VisionLandmarkType.leftAnkle,
  ],
  SupportedExercise.pushUp: [
    VisionLandmarkType.leftShoulder,
    VisionLandmarkType.leftElbow,
    VisionLandmarkType.leftWrist,
  ],
  SupportedExercise.plank: [
    VisionLandmarkType.leftShoulder,
    VisionLandmarkType.leftHip,
    VisionLandmarkType.leftAnkle,
  ],
  SupportedExercise.jumpingJack: [
    VisionLandmarkType.leftWrist,
    VisionLandmarkType.rightWrist,
    VisionLandmarkType.leftShoulder,
    VisionLandmarkType.rightShoulder,
    VisionLandmarkType.leftAnkle,
    VisionLandmarkType.rightAnkle,
  ],
  SupportedExercise.lunge: [
    VisionLandmarkType.leftHip,
    VisionLandmarkType.leftKnee,
    VisionLandmarkType.leftAnkle,
  ],
  SupportedExercise.sitUp: [
    VisionLandmarkType.leftShoulder,
    VisionLandmarkType.leftHip,
    VisionLandmarkType.leftKnee,
  ],
};

// ── ExerciseClassifier ────────────────────────────────────────────────────────

class ExerciseClassifier {
  ExerciseClassifier._();

  /// Valide que la [pose] est exploitable pour l'[exercise] choisi.
  static ClassificationResult validate(
    DetectedPose pose,
    SupportedExercise exercise,
  ) {
    // 1. Vérification couverture globale
    if (!pose.isUsable) {
      return ClassificationResult.noPose(exercise);
    }

    // 2. Vérification landmarks requis
    final required = _kRequiredLandmarks[exercise]!;
    final missingCount = required
        .where((type) => !(pose.landmarks[type]?.isReliable ?? false))
        .length;

    if (missingCount > 0) {
      return ClassificationResult(
        exercise: exercise,
        isValid: false,
        confidence: 1.0 - (missingCount / required.length),
        feedback: _missingFeedback(exercise, missingCount, required.length),
      );
    }

    // 3. Validation de base par exercice
    final specificFeedback = _validateSpecific(pose, exercise);
    if (specificFeedback != null) {
      return ClassificationResult(
        exercise: exercise,
        isValid: false,
        confidence: 0.6,
        feedback: specificFeedback,
      );
    }

    // 4. OK
    return ClassificationResult(
      exercise: exercise,
      isValid: true,
      confidence: pose.coverageScore,
      feedback: _readyFeedback(exercise),
    );
  }

  // ── Validation spécifique par exercice ────────────────────────────────────

  /// Retourne un message de correction, ou null si la position est OK.
  static String? _validateSpecific(
    DetectedPose pose,
    SupportedExercise exercise,
  ) {
    switch (exercise) {
      case SupportedExercise.squat:
      case SupportedExercise.lunge:
        return _validateProfileView(pose);

      case SupportedExercise.pushUp:
      case SupportedExercise.plank:
        return _validateHorizontalProfile(pose);

      case SupportedExercise.jumpingJack:
        return _validateFrontalView(pose);

      case SupportedExercise.sitUp:
        return _validateSitUpPosition(pose);
    }
  }

  /// Vue de profil : épaule, hanche, cheville doivent être approximativement
  /// alignées verticalement (même x ± tolérance).
  static String? _validateProfileView(DetectedPose pose) {
    final shoulder = pose.leftShoulder ?? pose.rightShoulder;
    final hip = pose.leftHip ?? pose.rightHip;

    if (shoulder == null || hip == null) return null;

    // En vue profil, épaule et hanche ont un x similaire (±0.25 de largeur)
    final xDiff = (shoulder.x - hip.x).abs();
    if (xDiff > 0.3) {
      return 'Placez-vous de profil par rapport à la caméra.';
    }
    return null;
  }

  /// Vue de profil horizontal : corps allongé (épaule et cheville
  /// à hauteurs similaires en coordonnées normalisées).
  static String? _validateHorizontalProfile(DetectedPose pose) {
    final shoulder = pose.leftShoulder ?? pose.rightShoulder;
    final ankle = pose.leftAnkle ?? pose.rightAnkle;

    if (shoulder == null || ankle == null) return null;

    // En position horizontale, y de l'épaule ≈ y de la cheville (±0.2)
    final yDiff = (shoulder.y - ankle.y).abs();
    if (yDiff > 0.3) {
      return 'Positionnez-vous horizontalement, de profil.';
    }
    return null;
  }

  /// Vue frontale : les deux épaules doivent être visibles et symétriques.
  static String? _validateFrontalView(DetectedPose pose) {
    final leftShoulder = pose.leftShoulder;
    final rightShoulder = pose.rightShoulder;

    if (leftShoulder == null || rightShoulder == null) {
      return 'Faites face à la caméra, les deux épaules doivent être visibles.';
    }

    // En vue frontale, les deux épaules ont un y similaire (±0.1)
    final yDiff = (leftShoulder.y - rightShoulder.y).abs();
    if (yDiff > 0.15) {
      return 'Faites face à la caméra, épaules au même niveau.';
    }
    return null;
  }

  /// Sit-up : validation de la position allongée (y épaule ≈ y genou).
  static String? _validateSitUpPosition(DetectedPose pose) {
    final shoulder = pose.leftShoulder ?? pose.rightShoulder;
    final knee = pose.leftKnee ?? pose.rightKnee;

    if (shoulder == null || knee == null) return null;

    final yDiff = (shoulder.y - knee.y).abs();
    if (yDiff > 0.35) {
      return 'Allongez-vous sur le dos, caméra de côté.';
    }
    return null;
  }

  // ── Messages ───────────────────────────────────────────────────────────────

  static String _missingFeedback(
    SupportedExercise exercise,
    int missing,
    int total,
  ) {
    final pct = ((total - missing) / total * 100).round();
    return 'Détection partielle ($pct%). ${exercise.cameraGuide}';
  }

  static String _readyFeedback(SupportedExercise exercise) {
    return switch (exercise) {
      SupportedExercise.squat => 'Position OK. Commencez votre squat !',
      SupportedExercise.pushUp => 'Position OK. Commencez vos pompes !',
      SupportedExercise.plank => 'Position OK. Maintenez la planche !',
      SupportedExercise.jumpingJack => 'Position OK. Partez !',
      SupportedExercise.lunge => 'Position OK. Commencez vos fentes !',
      SupportedExercise.sitUp => 'Position OK. Commencez vos abdominaux !',
    };
  }
}
