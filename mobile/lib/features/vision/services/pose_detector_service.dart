/// Service PoseDetectorService — pont entre ML Kit et nos modèles internes (LOT 7).
///
/// Gère le cycle de vie du [PoseDetector] ML Kit :
///   - Conversion [CameraImage] → [InputImage] (formats YUV420/BGRA8888)
///   - Inférence ML Kit → [DetectedPose] interne
///   - Mapping des 33 landmarks ML Kit ↔ [VisionLandmarkType]
///
/// Utiliser [initialize()] avant usage, [close()] en fin de session.
library;

import 'dart:io' show Platform;
import 'dart:ui' show Size;

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../models/pose_landmark.dart';

// ── PoseDetectorService ───────────────────────────────────────────────────────

class PoseDetectorService {
  late PoseDetector _detector;
  bool _isInitialized = false;

  // ── Cycle de vie ──────────────────────────────────────────────────────────

  Future<void> initialize() async {
    final options = PoseDetectorOptions(
      mode: PoseDetectionMode.stream, // optimisé pour flux vidéo
      model: PoseDetectionModel.accurate, // précision > vitesse pour V1
    );
    _detector = PoseDetector(options: options);
    _isInitialized = true;
  }

  Future<void> close() async {
    if (_isInitialized) {
      await _detector.close();
      _isInitialized = false;
    }
  }

  // ── Traitement frame ──────────────────────────────────────────────────────

  /// Convertit un frame caméra en [DetectedPose].
  ///
  /// Retourne null si :
  ///   - Le service n'est pas initialisé
  ///   - Aucune pose détectée dans le frame
  ///   - La conversion de format échoue
  Future<DetectedPose?> processFrame(
    CameraImage image,
    CameraDescription camera,
  ) async {
    if (!_isInitialized) return null;

    try {
      final inputImage = _convertCameraImage(image, camera);
      if (inputImage == null) return null;

      final poses = await _detector.processImage(inputImage);
      if (poses.isEmpty) return null;

      // En exercice solo, on prend la première pose détectée
      return _convertPose(poses.first, image.width, image.height);
    } catch (e) {
      if (kDebugMode) debugPrint('[PoseDetector] Error: $e');
      return null;
    }
  }

  // ── Conversion CameraImage → InputImage ───────────────────────────────────

  InputImage? _convertCameraImage(CameraImage image, CameraDescription camera) {
    final rotation = _rotationFromSensorOrientation(camera.sensorOrientation);

    if (Platform.isAndroid) {
      return _convertAndroid(image, rotation);
    } else if (Platform.isIOS) {
      return _convertIOS(image, rotation);
    }
    return null;
  }

  /// Conversion Android (YUV_420_888).
  InputImage? _convertAndroid(CameraImage image, InputImageRotation rotation) {
    if (image.planes.isEmpty) return null;

    // Concatène les planes NV21 / YUV420
    final WriteBuffer buffer = WriteBuffer();
    for (final Plane plane in image.planes) {
      buffer.putUint8List(plane.bytes);
    }
    final bytes = buffer.done().buffer.asUint8List();

    return InputImage.fromBytes(
      bytes: bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: InputImageFormat.nv21,
        bytesPerRow: image.planes[0].bytesPerRow,
      ),
    );
  }

  /// Conversion iOS (BGRA8888).
  InputImage? _convertIOS(CameraImage image, InputImageRotation rotation) {
    if (image.planes.isEmpty) return null;

    return InputImage.fromBytes(
      bytes: image.planes[0].bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: InputImageFormat.bgra8888,
        bytesPerRow: image.planes[0].bytesPerRow,
      ),
    );
  }

  InputImageRotation _rotationFromSensorOrientation(int sensorOrientation) {
    switch (sensorOrientation) {
      case 0:
        return InputImageRotation.rotation0deg;
      case 90:
        return InputImageRotation.rotation90deg;
      case 180:
        return InputImageRotation.rotation180deg;
      case 270:
        return InputImageRotation.rotation270deg;
      default:
        return InputImageRotation.rotation0deg;
    }
  }

  // ── Conversion Pose ML Kit → DetectedPose ─────────────────────────────────

  DetectedPose _convertPose(Pose mlPose, int width, int height) {
    final landmarks = <VisionLandmarkType, VisionLandmarkPoint>{};

    for (final entry in mlPose.landmarks.entries) {
      final type = _mapLandmarkType(entry.key);
      if (type == null) continue;

      final lm = entry.value;
      landmarks[type] = VisionLandmarkPoint(
        type: type,
        x: lm.x / width, // normalisation [0, 1]
        y: lm.y / height,
        z: lm.z, // déjà normalisé par ML Kit
        likelihood: lm.likelihood,
      );
    }

    return DetectedPose(landmarks: landmarks, capturedAt: DateTime.now());
  }

  /// Mapping ML Kit PoseLandmarkType → VisionLandmarkType.
  VisionLandmarkType? _mapLandmarkType(PoseLandmarkType type) {
    return switch (type) {
      PoseLandmarkType.nose => VisionLandmarkType.nose,
      PoseLandmarkType.leftEyeInner => VisionLandmarkType.leftEyeInner,
      PoseLandmarkType.leftEye => VisionLandmarkType.leftEye,
      PoseLandmarkType.leftEyeOuter => VisionLandmarkType.leftEyeOuter,
      PoseLandmarkType.rightEyeInner => VisionLandmarkType.rightEyeInner,
      PoseLandmarkType.rightEye => VisionLandmarkType.rightEye,
      PoseLandmarkType.rightEyeOuter => VisionLandmarkType.rightEyeOuter,
      PoseLandmarkType.leftEar => VisionLandmarkType.leftEar,
      PoseLandmarkType.rightEar => VisionLandmarkType.rightEar,
      PoseLandmarkType.leftMouth => VisionLandmarkType.mouthLeft,
      PoseLandmarkType.rightMouth => VisionLandmarkType.mouthRight,
      PoseLandmarkType.leftShoulder => VisionLandmarkType.leftShoulder,
      PoseLandmarkType.rightShoulder => VisionLandmarkType.rightShoulder,
      PoseLandmarkType.leftElbow => VisionLandmarkType.leftElbow,
      PoseLandmarkType.rightElbow => VisionLandmarkType.rightElbow,
      PoseLandmarkType.leftWrist => VisionLandmarkType.leftWrist,
      PoseLandmarkType.rightWrist => VisionLandmarkType.rightWrist,
      PoseLandmarkType.leftPinky => VisionLandmarkType.leftPinky,
      PoseLandmarkType.rightPinky => VisionLandmarkType.rightPinky,
      PoseLandmarkType.leftIndex => VisionLandmarkType.leftIndex,
      PoseLandmarkType.rightIndex => VisionLandmarkType.rightIndex,
      PoseLandmarkType.leftThumb => VisionLandmarkType.leftThumb,
      PoseLandmarkType.rightThumb => VisionLandmarkType.rightThumb,
      PoseLandmarkType.leftHip => VisionLandmarkType.leftHip,
      PoseLandmarkType.rightHip => VisionLandmarkType.rightHip,
      PoseLandmarkType.leftKnee => VisionLandmarkType.leftKnee,
      PoseLandmarkType.rightKnee => VisionLandmarkType.rightKnee,
      PoseLandmarkType.leftAnkle => VisionLandmarkType.leftAnkle,
      PoseLandmarkType.rightAnkle => VisionLandmarkType.rightAnkle,
      PoseLandmarkType.leftHeel => VisionLandmarkType.leftHeel,
      PoseLandmarkType.rightHeel => VisionLandmarkType.rightHeel,
      PoseLandmarkType.leftFootIndex => VisionLandmarkType.leftFootIndex,
      PoseLandmarkType.rightFootIndex => VisionLandmarkType.rightFootIndex,
    };
  }
}
