/// Tests ExerciseClassifier — validation de position pour un exercice (LOT 7).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/features/vision/models/exercise_frame.dart';
import 'package:soma_mobile/features/vision/models/pose_landmark.dart';
import 'package:soma_mobile/features/vision/services/exercise_classifier.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

/// Crée un landmark fiable à (x, y).
VisionLandmarkPoint lm(double x, double y) =>
    VisionLandmarkPoint(x: x, y: y, z: 0, likelihood: 0.9);

/// Pose minimale avec les landmarks donnés.
DetectedPose pose(Map<VisionLandmarkType, VisionLandmarkPoint> landmarks) =>
    DetectedPose(landmarks: landmarks);

/// Pose vide (aucun landmark).
DetectedPose emptyPose() => DetectedPose(landmarks: {});

/// Pose avec couverture suffisante mais landmarks requis absents.
DetectedPose insufficientPose() {
  return DetectedPose(landmarks: {
    VisionLandmarkType.nose: lm(0.5, 0.1),
    VisionLandmarkType.leftEye: lm(0.45, 0.1),
    VisionLandmarkType.rightEye: lm(0.55, 0.1),
    // pas de hanche, genou, cheville
  });
}

/// Crée une pose de vue de profil valide pour squat/lunge.
/// Épaule et hanche alignées verticalement.
DetectedPose validProfilePose() {
  return DetectedPose(landmarks: {
    VisionLandmarkType.leftShoulder: lm(0.5, 0.3),
    VisionLandmarkType.rightShoulder: lm(0.55, 0.3),
    VisionLandmarkType.leftHip: lm(0.5, 0.55),
    VisionLandmarkType.rightHip: lm(0.55, 0.55),
    VisionLandmarkType.leftKnee: lm(0.5, 0.72),
    VisionLandmarkType.rightKnee: lm(0.55, 0.72),
    VisionLandmarkType.leftAnkle: lm(0.5, 0.9),
    VisionLandmarkType.rightAnkle: lm(0.55, 0.9),
    // Ajout d'autres landmarks pour coverage > 40%
    VisionLandmarkType.nose: lm(0.5, 0.1),
    VisionLandmarkType.leftElbow: lm(0.4, 0.45),
    VisionLandmarkType.rightElbow: lm(0.6, 0.45),
    VisionLandmarkType.leftWrist: lm(0.38, 0.58),
    VisionLandmarkType.rightWrist: lm(0.62, 0.58),
    VisionLandmarkType.leftEye: lm(0.47, 0.08),
    VisionLandmarkType.rightEye: lm(0.53, 0.08),
  });
}

/// Pose pour jumping jack (vue frontale, épaules symétriques).
DetectedPose validFrontalPose() {
  return DetectedPose(landmarks: {
    VisionLandmarkType.leftShoulder: lm(0.35, 0.3),
    VisionLandmarkType.rightShoulder: lm(0.65, 0.3), // même y → frontal
    VisionLandmarkType.leftWrist: lm(0.1, 0.2),
    VisionLandmarkType.rightWrist: lm(0.9, 0.2),
    VisionLandmarkType.leftAnkle: lm(0.25, 0.9),
    VisionLandmarkType.rightAnkle: lm(0.75, 0.9),
    VisionLandmarkType.leftHip: lm(0.4, 0.6),
    VisionLandmarkType.rightHip: lm(0.6, 0.6),
    VisionLandmarkType.nose: lm(0.5, 0.1),
    VisionLandmarkType.leftEye: lm(0.47, 0.08),
    VisionLandmarkType.rightEye: lm(0.53, 0.08),
    VisionLandmarkType.leftElbow: lm(0.2, 0.25),
    VisionLandmarkType.rightElbow: lm(0.8, 0.25),
    VisionLandmarkType.leftKnee: lm(0.3, 0.72),
    VisionLandmarkType.rightKnee: lm(0.7, 0.72),
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  group('ExerciseClassifier — pose non détectée', () {
    test('pose vide → isValid = false, confidence = 0', () {
      final result = ExerciseClassifier.validate(
        emptyPose(),
        SupportedExercise.squat,
      );
      expect(result.isValid, isFalse);
      expect(result.confidence, 0.0);
    });

    test('feedback explicite quand pose non détectée', () {
      final result = ExerciseClassifier.validate(
        emptyPose(),
        SupportedExercise.squat,
      );
      expect(result.feedback, isNotEmpty);
    });
  });

  group('ExerciseClassifier — landmarks insuffisants', () {
    test('pose sans landmarks requis → isValid = false', () {
      final result = ExerciseClassifier.validate(
        insufficientPose(),
        SupportedExercise.squat,
      );
      // insufficientPose n'a pas les 15 landmarks requis pour coverage > 40%
      // Donc isUsable = false → noPose
      expect(result.isValid, isFalse);
    });
  });

  group('ExerciseClassifier — squat', () {
    test('pose profil valide → isValid = true', () {
      final result = ExerciseClassifier.validate(
        validProfilePose(),
        SupportedExercise.squat,
      );
      expect(result.isValid, isTrue);
    });

    test('exercise retourné correspond à celui passé', () {
      final result = ExerciseClassifier.validate(
        validProfilePose(),
        SupportedExercise.squat,
      );
      expect(result.exercise, SupportedExercise.squat);
    });

    test('confidence > 0 pour une pose valide', () {
      final result = ExerciseClassifier.validate(
        validProfilePose(),
        SupportedExercise.squat,
      );
      expect(result.confidence, greaterThan(0.0));
    });

    test('feedback positif quand pose valide', () {
      final result = ExerciseClassifier.validate(
        validProfilePose(),
        SupportedExercise.squat,
      );
      expect(result.feedback, contains('OK'));
    });
  });

  group('ExerciseClassifier — jumping jack', () {
    test('pose frontale valide → isValid = true', () {
      final result = ExerciseClassifier.validate(
        validFrontalPose(),
        SupportedExercise.jumpingJack,
      );
      expect(result.isValid, isTrue);
    });

    test('pose de profil pour jumping jack → isValid = false', () {
      // Vue de profil : épaules à des y très différents (simule vue côté)
      final badPose = DetectedPose(landmarks: {
        VisionLandmarkType.leftShoulder: lm(0.5, 0.3),
        VisionLandmarkType.rightShoulder: lm(0.5, 0.55), // y très différent
        VisionLandmarkType.leftWrist: lm(0.4, 0.2),
        VisionLandmarkType.rightWrist: lm(0.6, 0.2),
        VisionLandmarkType.leftAnkle: lm(0.45, 0.9),
        VisionLandmarkType.rightAnkle: lm(0.55, 0.9),
        VisionLandmarkType.leftHip: lm(0.5, 0.6),
        VisionLandmarkType.rightHip: lm(0.5, 0.6),
        VisionLandmarkType.nose: lm(0.5, 0.1),
        VisionLandmarkType.leftEye: lm(0.47, 0.08),
        VisionLandmarkType.rightEye: lm(0.53, 0.08),
        VisionLandmarkType.leftElbow: lm(0.42, 0.25),
        VisionLandmarkType.rightElbow: lm(0.58, 0.25),
        VisionLandmarkType.leftKnee: lm(0.47, 0.72),
        VisionLandmarkType.rightKnee: lm(0.53, 0.72),
      });
      final result = ExerciseClassifier.validate(
        badPose,
        SupportedExercise.jumpingJack,
      );
      // Les deux épaules ont un y très différent → feedback de correction
      expect(result.isValid, isFalse);
    });
  });

  group('ExerciseClassifier — ClassificationResult.noPose', () {
    test('noPose : isValid = false, confidence = 0', () {
      const result = ClassificationResult.noPose(SupportedExercise.squat);
      expect(result.isValid, isFalse);
      expect(result.confidence, 0.0);
      expect(result.exercise, SupportedExercise.squat);
    });

    test('noPose : feedback non vide', () {
      const result = ClassificationResult.noPose(SupportedExercise.pushUp);
      expect(result.feedback, isNotEmpty);
    });
  });
}
