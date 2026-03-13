/// PoseOverlayPainter — overlay squelette sur le preview caméra (LOT 7).
///
/// Dessine les landmarks (points articulaires) et les connexions (os)
/// par-dessus le flux caméra en utilisant un [CustomPainter].
///
/// Les coordonnées normalisées [0,1] sont converties aux dimensions du canvas.
///
/// Les couleurs sont injectées via le constructeur (rule 7 : pas de
/// BuildContext dans un CustomPainter).
library;

import 'package:flutter/material.dart';

import '../models/pose_landmark.dart';

// ── Connexions squelette ──────────────────────────────────────────────────────

/// Paires de landmarks à relier par des lignes (os).
const _kConnections = <(VisionLandmarkType, VisionLandmarkType)>[
  // Torse
  (VisionLandmarkType.leftShoulder, VisionLandmarkType.rightShoulder),
  (VisionLandmarkType.leftShoulder, VisionLandmarkType.leftHip),
  (VisionLandmarkType.rightShoulder, VisionLandmarkType.rightHip),
  (VisionLandmarkType.leftHip, VisionLandmarkType.rightHip),

  // Bras gauche
  (VisionLandmarkType.leftShoulder, VisionLandmarkType.leftElbow),
  (VisionLandmarkType.leftElbow, VisionLandmarkType.leftWrist),

  // Bras droit
  (VisionLandmarkType.rightShoulder, VisionLandmarkType.rightElbow),
  (VisionLandmarkType.rightElbow, VisionLandmarkType.rightWrist),

  // Jambe gauche
  (VisionLandmarkType.leftHip, VisionLandmarkType.leftKnee),
  (VisionLandmarkType.leftKnee, VisionLandmarkType.leftAnkle),

  // Jambe droite
  (VisionLandmarkType.rightHip, VisionLandmarkType.rightKnee),
  (VisionLandmarkType.rightKnee, VisionLandmarkType.rightAnkle),
];

/// Landmarks clés à afficher comme points (cercles).
const _kKeyLandmarks = <VisionLandmarkType>[
  VisionLandmarkType.leftShoulder,
  VisionLandmarkType.rightShoulder,
  VisionLandmarkType.leftElbow,
  VisionLandmarkType.rightElbow,
  VisionLandmarkType.leftWrist,
  VisionLandmarkType.rightWrist,
  VisionLandmarkType.leftHip,
  VisionLandmarkType.rightHip,
  VisionLandmarkType.leftKnee,
  VisionLandmarkType.rightKnee,
  VisionLandmarkType.leftAnkle,
  VisionLandmarkType.rightAnkle,
];

// ── PoseOverlayPainter ────────────────────────────────────────────────────────

class PoseOverlayPainter extends CustomPainter {
  final DetectedPose pose;

  /// Vrai si la pose est validée par le classificateur (couleur verte).
  final bool isValid;

  /// Couleur des os quand la pose est valide.
  final Color validBoneColor;

  /// Couleur des os quand la pose n'est pas encore validée.
  final Color invalidBoneColor;

  /// Couleur des points articulaires.
  final Color jointColor;

  PoseOverlayPainter({
    required this.pose,
    this.isValid = false,
    required this.validBoneColor,
    required this.invalidBoneColor,
    required this.jointColor,
  });

  Color get _boneColor => isValid ? validBoneColor : invalidBoneColor;

  @override
  void paint(Canvas canvas, Size size) {
    final bonePaint = Paint()
      ..color = _boneColor.withOpacity(0.8)
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final jointPaint = Paint()
      ..color = jointColor
      ..style = PaintingStyle.fill;

    final jointBorderPaint = Paint()
      ..color = _boneColor
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    // ── Connexions (os) ──────────────────────────────────────────────────
    for (final (typeA, typeB) in _kConnections) {
      final a = pose.landmarks[typeA];
      final b = pose.landmarks[typeB];
      if (a == null || b == null) continue;
      if (!a.isReliable || !b.isReliable) continue;

      final pa = Offset(a.x * size.width, a.y * size.height);
      final pb = Offset(b.x * size.width, b.y * size.height);

      canvas.drawLine(pa, pb, bonePaint);
    }

    // ── Points articulaires ───────────────────────────────────────────────
    for (final type in _kKeyLandmarks) {
      final lm = pose.landmarks[type];
      if (lm == null || !lm.isReliable) continue;

      final center = Offset(lm.x * size.width, lm.y * size.height);
      const radius = 5.0;

      canvas.drawCircle(center, radius, jointPaint);
      canvas.drawCircle(center, radius, jointBorderPaint);
    }
  }

  @override
  bool shouldRepaint(PoseOverlayPainter oldDelegate) {
    return oldDelegate.pose != pose || oldDelegate.isValid != isValid;
  }
}
