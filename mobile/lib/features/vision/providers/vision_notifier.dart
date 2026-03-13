/// VisionNotifier — orchestrateur de la session Computer Vision (LOT 7).
///
/// Gère le pipeline complet :
///   1. Initialisation caméra + PoseDetector
///   2. Flux frames → détection → classification → comptage → scoring
///   3. Timer de session
///   4. Finalisation et calcul qualité
///
/// Utilise [StateNotifier] (pas AsyncNotifier) car l'état évolue en continu.
library;

import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/exercise_frame.dart';
import '../models/movement_quality.dart';
import '../models/pose_landmark.dart';
import '../models/rep_counter_state.dart';
import '../models/vision_session.dart';
import '../services/angle_calculator.dart';
import '../services/exercise_classifier.dart';
import '../services/pose_detector_service.dart';
import '../services/quality_scorer.dart';
import '../services/rep_counter.dart';

// ── Statut de la session ──────────────────────────────────────────────────────

enum VisionStatus {
  /// Session non démarrée.
  idle,

  /// Initialisation caméra + détecteur.
  initializing,

  /// Prêt — caméra active, en attente du démarrage utilisateur.
  ready,

  /// En cours — détection + comptage actifs.
  running,

  /// Pause.
  paused,

  /// Session terminée — qualité calculée.
  finished,

  /// Erreur irrécupérable.
  error,
}

// ── État de la session Vision ─────────────────────────────────────────────────

class VisionSessionState {
  final VisionStatus status;
  final SupportedExercise? exercise;
  final RepCounterState repState;
  final ClassificationResult? classification;
  final MovementQuality quality;
  final int durationSeconds;
  final DetectedPose? lastPose;
  final String? errorMessage;
  final String? workoutSessionId; // rattachement à une WorkoutSession

  const VisionSessionState({
    this.status = VisionStatus.idle,
    this.exercise,
    this.repState = const RepCounterState(),
    this.classification,
    this.quality = const MovementQuality(),
    this.durationSeconds = 0,
    this.lastPose,
    this.errorMessage,
    this.workoutSessionId,
  });

  VisionSessionState copyWith({
    VisionStatus? status,
    SupportedExercise? exercise,
    RepCounterState? repState,
    ClassificationResult? classification,
    MovementQuality? quality,
    int? durationSeconds,
    DetectedPose? lastPose,
    String? errorMessage,
    String? workoutSessionId,
  }) =>
      VisionSessionState(
        status: status ?? this.status,
        exercise: exercise ?? this.exercise,
        repState: repState ?? this.repState,
        classification: classification ?? this.classification,
        quality: quality ?? this.quality,
        durationSeconds: durationSeconds ?? this.durationSeconds,
        lastPose: lastPose ?? this.lastPose,
        errorMessage: errorMessage ?? this.errorMessage,
        workoutSessionId: workoutSessionId ?? this.workoutSessionId,
      );

  /// Construit le résumé de session final pour envoi au backend.
  VisionSession toVisionSession() {
    final ex = exercise!;
    return VisionSession(
      exercise: ex,
      repCount: repState.count,
      durationSeconds: durationSeconds,
      quality: quality,
      startedAt: DateTime.now().subtract(Duration(seconds: durationSeconds)),
      workoutSessionId: workoutSessionId,
    );
  }

  bool get isRunning => status == VisionStatus.running;
  bool get isFinished => status == VisionStatus.finished;
  bool get hasError => status == VisionStatus.error;
}

// ── Provider ──────────────────────────────────────────────────────────────────

final visionProvider =
    StateNotifierProvider.autoDispose<VisionNotifier, VisionSessionState>(
  (ref) => VisionNotifier(),
);

// ── VisionNotifier ────────────────────────────────────────────────────────────

class VisionNotifier extends StateNotifier<VisionSessionState> {
  VisionNotifier() : super(const VisionSessionState());

  // Services internes
  final _detectorService = PoseDetectorService();
  CameraController? _camera;
  RepCounter? _counter;
  QualityScorer? _scorer;
  Timer? _timer;

  // Throttling : on traite 1 frame sur 2 (≈15fps depuis 30fps caméra)
  bool _isProcessing = false;
  int _frameCount = 0;
  static const int _kFrameSkip = 2;

  // ── Initialisation ────────────────────────────────────────────────────────

  /// Initialise la caméra et le détecteur de pose.
  ///
  /// [exercise] : exercice sélectionné par l'utilisateur
  /// [camera] : caméra à utiliser (typiquement caméra frontale ou arrière)
  /// [workoutSessionId] : id de la WorkoutSession à laquelle rattacher la session
  Future<void> initialize({
    required SupportedExercise exercise,
    required CameraDescription camera,
    String? workoutSessionId,
  }) async {
    state = state.copyWith(
      status: VisionStatus.initializing,
      exercise: exercise,
      workoutSessionId: workoutSessionId,
    );

    try {
      // Initialise ML Kit
      await _detectorService.initialize();

      // Initialise la caméra
      _camera = CameraController(
        camera,
        ResolutionPreset.medium, // équilibre qualité / performance
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.nv21,
      );
      await _camera!.initialize();

      // Prépare les services d'analyse
      _counter = RepCounterFactory.create(exercise);
      _scorer = QualityScorer(exercise: exercise);

      state = state.copyWith(status: VisionStatus.ready);
    } catch (e) {
      state = state.copyWith(
        status: VisionStatus.error,
        errorMessage: "Impossible d'initialiser la caméra : $e",
      );
    }
  }

  /// Accès au controller caméra pour le preview dans l'UI.
  CameraController? get cameraController => _camera;

  // ── Contrôles de session ──────────────────────────────────────────────────

  /// Démarre le flux de détection + timer.
  void start() {
    if (state.status != VisionStatus.ready &&
        state.status != VisionStatus.paused) return;

    _camera!.startImageStream(_onCameraFrame);
    _startTimer();
    state = state.copyWith(status: VisionStatus.running);
  }

  /// Met la session en pause.
  void pause() {
    if (state.status != VisionStatus.running) return;
    _camera?.stopImageStream();
    _timer?.cancel();
    state = state.copyWith(status: VisionStatus.paused);
  }

  /// Reprend après une pause.
  void resume() {
    if (state.status != VisionStatus.paused) return;
    _camera!.startImageStream(_onCameraFrame);
    _startTimer();
    state = state.copyWith(status: VisionStatus.running);
  }

  /// Termine la session et calcule la qualité finale.
  Future<void> finish() async {
    _camera?.stopImageStream();
    _timer?.cancel();

    final quality = _scorer?.compute() ?? const MovementQuality();

    state = state.copyWith(
      status: VisionStatus.finished,
      quality: quality,
    );
  }

  // ── Pipeline de traitement des frames ────────────────────────────────────

  Future<void> _onCameraFrame(CameraImage image) async {
    if (_isProcessing) return;
    if (state.status != VisionStatus.running) return;

    _frameCount++;
    if (_frameCount % _kFrameSkip != 0) return; // throttle

    _isProcessing = true;

    try {
      final camera = _camera?.description;
      if (camera == null) return;

      // 1. Détection de pose
      final pose = await _detectorService.processFrame(image, camera);

      if (pose == null) {
        // Pas de pose détectée
        state = state.copyWith(
          lastPose: null,
          classification: ClassificationResult.noPose(state.exercise!),
        );
        return;
      }

      // 2. Classification / validation de position
      final classification = ExerciseClassifier.validate(
        pose,
        state.exercise!,
      );

      // 3. Calcul des angles
      final angles = AngleCalculator.computeForExercise(
        pose,
        state.exercise!,
      );

      // 4. Alimentation du scorer
      _scorer?.addFrame(angles, pose.coverageScore);

      // 5. Mise à jour du compteur de reps (si position valide)
      RepCounterState newRepState = state.repState;
      if (classification.isValid) {
        newRepState = _counter!.update(angles);
        // Synchronisation scorer ↔ rep counter
        _scorer?.syncFromRepState(
          peakAngles: newRepState.peakAngles,
          repTimestamps: newRepState.repTimestamps,
        );
      }

      // 6. Mise à jour état
      state = state.copyWith(
        lastPose: pose,
        classification: classification,
        repState: newRepState,
      );
    } catch (e) {
      if (kDebugMode) debugPrint('[VisionNotifier] Frame error: $e');
    } finally {
      _isProcessing = false;
    }
  }

  // ── Timer ─────────────────────────────────────────────────────────────────

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      state = state.copyWith(durationSeconds: state.durationSeconds + 1);
    });
  }

  // ── Dispose ───────────────────────────────────────────────────────────────

  @override
  void dispose() {
    _timer?.cancel();
    _camera?.dispose();
    _detectorService.close();
    super.dispose();
  }
}
