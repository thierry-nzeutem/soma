/// Service AngleCalculator — calcul d'angles articulaires à partir d'une pose (LOT 7).
///
/// Calcule les angles en 2D (projection x, y normalisée).
/// Service pur sans dépendance Flutter, entièrement testable.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/exercise_frame.dart';
import '../models/pose_landmark.dart';

// ── Calculateur ───────────────────────────────────────────────────────────────

class AngleCalculator {
  AngleCalculator._();

  // ── API publique ──────────────────────────────────────────────────────────

  /// Calcule tous les angles pertinents pour l'exercice donné depuis la pose.
  static ExerciseAngles computeForExercise(
    DetectedPose pose,
    SupportedExercise exercise,
  ) {
    switch (exercise) {
      case SupportedExercise.squat:
        return ExerciseAngles(
          leftKneeAngle: _kneeAngle(pose, left: true),
          rightKneeAngle: _kneeAngle(pose, left: false),
          bodyAlignmentAngle: _bodyAlignmentAngle(pose),
        );
      case SupportedExercise.pushUp:
        return ExerciseAngles(
          leftElbowAngle: _elbowAngle(pose, left: true),
          rightElbowAngle: _elbowAngle(pose, left: false),
          bodyAlignmentAngle: _bodyAlignmentAngle(pose),
        );
      case SupportedExercise.plank:
        return ExerciseAngles(
          bodyAlignmentAngle: _bodyAlignmentAngle(pose),
        );
      case SupportedExercise.jumpingJack:
        return ExerciseAngles(
          armSpreadRatio: _armSpreadRatio(pose),
          legSpreadRatio: _legSpreadRatio(pose),
        );
      case SupportedExercise.lunge:
        return ExerciseAngles(
          leftKneeAngle: _kneeAngle(pose, left: true),
          rightKneeAngle: _kneeAngle(pose, left: false),
        );
      case SupportedExercise.sitUp:
        return ExerciseAngles(
          leftHipAngle: _trunkAngleAtHip(pose, left: true),
          rightHipAngle: _trunkAngleAtHip(pose, left: false),
        );
    }
  }

  // ── Calcul angle genou (hanche-genou-cheville) ────────────────────────────

  static double? _kneeAngle(DetectedPose pose, {required bool left}) {
    final hip = left ? pose.leftHip : pose.rightHip;
    final knee = left ? pose.leftKnee : pose.rightKnee;
    final ankle = left ? pose.leftAnkle : pose.rightAnkle;
    if (!_allReliable([hip, knee, ankle])) return null;
    return _angleBetween(
      hip!.toOffset(),
      knee!.toOffset(),
      ankle!.toOffset(),
    );
  }

  // ── Calcul angle coude (épaule-coude-poignet) ─────────────────────────────

  static double? _elbowAngle(DetectedPose pose, {required bool left}) {
    final shoulder = left ? pose.leftShoulder : pose.rightShoulder;
    final elbow = left ? pose.leftElbow : pose.rightElbow;
    final wrist = left ? pose.leftWrist : pose.rightWrist;
    if (!_allReliable([shoulder, elbow, wrist])) return null;
    return _angleBetween(
      shoulder!.toOffset(),
      elbow!.toOffset(),
      wrist!.toOffset(),
    );
  }

  // ── Calcul angle tronc-hanche (épaule-hanche-genou) — sit-up ─────────────

  static double? _trunkAngleAtHip(DetectedPose pose, {required bool left}) {
    final shoulder = left ? pose.leftShoulder : pose.rightShoulder;
    final hip = left ? pose.leftHip : pose.rightHip;
    final knee = left ? pose.leftKnee : pose.rightKnee;
    if (!_allReliable([shoulder, hip, knee])) return null;
    return _angleBetween(
      shoulder!.toOffset(),
      hip!.toOffset(),
      knee!.toOffset(),
    );
  }

  // ── Calcul alignement corps (épaule-hanche-cheville) ─────────────────────

  static double? _bodyAlignmentAngle(DetectedPose pose) {
    // Utilise le côté gauche en priorité, droite en fallback
    final shoulder =
        pose.leftShoulder?.isReliable == true ? pose.leftShoulder : pose.rightShoulder;
    final hip =
        pose.leftHip?.isReliable == true ? pose.leftHip : pose.rightHip;
    final ankle =
        pose.leftAnkle?.isReliable == true ? pose.leftAnkle : pose.rightAnkle;
    if (!_allReliable([shoulder, hip, ankle])) return null;
    return _angleBetween(
      shoulder!.toOffset(),
      hip!.toOffset(),
      ankle!.toOffset(),
    );
  }

  // ── Calcul ratio ouverture bras — jumping jack ────────────────────────────

  /// 0 = bras le long du corps, 1 = bras totalement levés
  static double? _armSpreadRatio(DetectedPose pose) {
    final leftWrist = pose.leftWrist;
    final rightWrist = pose.rightWrist;
    final leftShoulder = pose.leftShoulder;
    final rightShoulder = pose.rightShoulder;

    if (!_allReliable([leftWrist, rightWrist, leftShoulder, rightShoulder])) {
      return null;
    }

    // Spread des poignets vs spread des épaules
    final wristWidth =
        (leftWrist!.x - rightWrist!.x).abs();
    final shoulderWidth =
        (leftShoulder!.x - rightShoulder!.x).abs();

    if (shoulderWidth < 0.001) return null;

    // En plus, vérifier que les poignets montent (y < épaule)
    final avgWristY = (leftWrist.y + rightWrist.y) / 2;
    final avgShoulderY = (leftShoulder.y + rightShoulder.y) / 2;
    final heightBonus = avgShoulderY > avgWristY ? 0.3 : 0.0;

    return ((wristWidth / shoulderWidth - 1.0).clamp(0.0, 1.0) * 0.7 +
            heightBonus)
        .clamp(0.0, 1.0);
  }

  // ── Calcul ratio ouverture jambes — jumping jack ──────────────────────────

  /// 0 = pieds joints, 1 = pieds largement écartés
  static double? _legSpreadRatio(DetectedPose pose) {
    final leftAnkle = pose.leftAnkle;
    final rightAnkle = pose.rightAnkle;
    final leftHip = pose.leftHip;
    final rightHip = pose.rightHip;

    if (!_allReliable([leftAnkle, rightAnkle, leftHip, rightHip])) {
      return null;
    }

    final ankleWidth = (leftAnkle!.x - rightAnkle!.x).abs();
    final hipWidth = (leftHip!.x - rightHip!.x).abs();

    if (hipWidth < 0.001) return null;
    return (ankleWidth / hipWidth - 1.0).clamp(0.0, 1.5) / 1.5;
  }

  // ── Utilitaire : angle au vertex B entre les rayons BA et BC ─────────────

  /// Retourne l'angle en DEGRÉS au point [b] entre les rayons [a]→[b] et [b]→[c].
  static double _angleBetween(Offset a, Offset b, Offset c) {
    final ba = Offset(a.dx - b.dx, a.dy - b.dy);
    final bc = Offset(c.dx - b.dx, c.dy - b.dy);

    final dot = ba.dx * bc.dx + ba.dy * bc.dy;
    final magBA =
        math.sqrt(ba.dx * ba.dx + ba.dy * ba.dy);
    final magBC =
        math.sqrt(bc.dx * bc.dx + bc.dy * bc.dy);

    if (magBA < 1e-6 || magBC < 1e-6) return 0;

    final cosAngle = (dot / (magBA * magBC)).clamp(-1.0, 1.0);
    return math.acos(cosAngle) * 180.0 / math.pi;
  }

  // ── Vérification fiabilité ────────────────────────────────────────────────

  static bool _allReliable(List<VisionLandmarkPoint?> points) =>
      points.every((p) => p != null && p.isReliable);

  // ── Helpers publics ───────────────────────────────────────────────────────

  /// Calcule l'angle entre 3 Offsets normalisés (API publique pour les tests).
  static double angleBetween(Offset a, Offset b, Offset c) =>
      _angleBetween(a, b, c);
}
