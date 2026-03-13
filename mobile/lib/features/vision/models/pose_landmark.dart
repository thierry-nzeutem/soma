/// Modèle PoseLandmark — abstraction de Google ML Kit Pose Detection (LOT 7).
///
/// Représente un squelette 33 points détecté dans un frame vidéo.
/// Coordonnées normalisées [0, 1] depuis le coin supérieur gauche.
library;

import 'package:flutter/material.dart';

// ── Types de landmarks ────────────────────────────────────────────────────────

/// 33 landmarks MediaPipe / ML Kit (miroir de PoseLandmarkType ML Kit).
enum VisionLandmarkType {
  nose,
  leftEyeInner,
  leftEye,
  leftEyeOuter,
  rightEyeInner,
  rightEye,
  rightEyeOuter,
  leftEar,
  rightEar,
  mouthLeft,
  mouthRight,
  leftShoulder,
  rightShoulder,
  leftElbow,
  rightElbow,
  leftWrist,
  rightWrist,
  leftPinky,
  rightPinky,
  leftIndex,
  rightIndex,
  leftThumb,
  rightThumb,
  leftHip,
  rightHip,
  leftKnee,
  rightKnee,
  leftAnkle,
  rightAnkle,
  leftHeel,
  rightHeel,
  leftFootIndex,
  rightFootIndex,
}

// ── Landmark point ────────────────────────────────────────────────────────────

/// Un point de squelette avec sa position et sa fiabilité.
class VisionLandmarkPoint {
  final VisionLandmarkType type;

  /// Position normalisée [0, 1] dans le frame.
  final double x;
  final double y;

  /// Profondeur relative (Z).
  final double z;

  /// Degré de confiance ML Kit [0, 1].
  final double likelihood;

  const VisionLandmarkPoint({
    required this.type,
    required this.x,
    required this.y,
    this.z = 0,
    this.likelihood = 0,
  });

  /// Considéré fiable si likelihood > 50%.
  bool get isReliable => likelihood > 0.5;

  /// Convertit en Offset pour les calculs géométriques.
  Offset toOffset() => Offset(x, y);

  /// Retourne une position en pixels selon les dimensions de l'image.
  Offset toPixelOffset(Size imageSize) =>
      Offset(x * imageSize.width, y * imageSize.height);

  @override
  String toString() =>
      'VisionLandmarkPoint(${type.name}, x=$x, y=$y, p=${likelihood.toStringAsFixed(2)})';
}

// ── Pose détectée ─────────────────────────────────────────────────────────────

/// Ensemble des 33 landmarks d'une pose détectée dans un frame.
class DetectedPose {
  final Map<VisionLandmarkType, VisionLandmarkPoint> landmarks;
  final DateTime capturedAt;

  const DetectedPose({
    required this.landmarks,
    required this.capturedAt,
  });

  /// Récupère un landmark par type (null si absent).
  VisionLandmarkPoint? get(VisionLandmarkType type) => landmarks[type];

  /// Vérifie que tous les landmarks donnés sont présents et fiables.
  bool hasReliableLandmarks(List<VisionLandmarkType> types) =>
      types.every((t) => landmarks[t]?.isReliable ?? false);

  /// Nombre de landmarks fiables (utilisé pour la qualité globale).
  int get reliableCount => landmarks.values.where((l) => l.isReliable).length;

  /// Score de couverture globale du squelette [0, 1].
  double get coverageScore => reliableCount / 33.0;

  /// Vrai si une pose est détectée de façon exploitable.
  bool get isUsable => coverageScore > 0.4;

  // ── Helpers raccourcis ────────────────────────────────────────────────────

  VisionLandmarkPoint? get leftShoulder =>
      get(VisionLandmarkType.leftShoulder);
  VisionLandmarkPoint? get rightShoulder =>
      get(VisionLandmarkType.rightShoulder);
  VisionLandmarkPoint? get leftElbow => get(VisionLandmarkType.leftElbow);
  VisionLandmarkPoint? get rightElbow => get(VisionLandmarkType.rightElbow);
  VisionLandmarkPoint? get leftWrist => get(VisionLandmarkType.leftWrist);
  VisionLandmarkPoint? get rightWrist => get(VisionLandmarkType.rightWrist);
  VisionLandmarkPoint? get leftHip => get(VisionLandmarkType.leftHip);
  VisionLandmarkPoint? get rightHip => get(VisionLandmarkType.rightHip);
  VisionLandmarkPoint? get leftKnee => get(VisionLandmarkType.leftKnee);
  VisionLandmarkPoint? get rightKnee => get(VisionLandmarkType.rightKnee);
  VisionLandmarkPoint? get leftAnkle => get(VisionLandmarkType.leftAnkle);
  VisionLandmarkPoint? get rightAnkle => get(VisionLandmarkType.rightAnkle);
}
