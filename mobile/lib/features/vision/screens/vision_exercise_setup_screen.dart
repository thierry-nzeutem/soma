/// Écran de sélection d'exercice pour la session Computer Vision (LOT 7).
///
/// Présente les 6 exercices disponibles, le guide caméra et lance
/// la VisionWorkoutScreen avec l'exercice choisi.
library;

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/theme_extensions.dart';
import '../models/exercise_frame.dart';
import '../providers/vision_notifier.dart';

// ── Screen principale ─────────────────────────────────────────────────────────

class VisionExerciseSetupScreen extends ConsumerStatefulWidget {
  /// Session workout à laquelle rattacher la session CV (optionnel).
  final String? workoutSessionId;

  const VisionExerciseSetupScreen({super.key, this.workoutSessionId});

  @override
  ConsumerState<VisionExerciseSetupScreen> createState() =>
      _VisionExerciseSetupScreenState();
}

class _VisionExerciseSetupScreenState
    extends ConsumerState<VisionExerciseSetupScreen> {
  SupportedExercise? _selected;
  List<CameraDescription> _cameras = [];
  bool _loadingCameras = true;

  @override
  void initState() {
    super.initState();
    _loadCameras();
  }

  Future<void> _loadCameras() async {
    try {
      _cameras = await availableCameras();
    } catch (_) {
      _cameras = [];
    }
    if (mounted) setState(() => _loadingCameras = false);
  }

  void _onExerciseTap(SupportedExercise exercise) {
    setState(() => _selected = exercise);
    _showGuideDialog(exercise);
  }

  void _showGuideDialog(SupportedExercise exercise) {
    showDialog<bool>(
      context: context,
      builder: (ctx) => _CameraGuideDialog(
        exercise: exercise,
        onStart: () {
          Navigator.of(ctx).pop(true);
          _startSession(exercise);
        },
      ),
    );
  }

  Future<void> _startSession(SupportedExercise exercise) async {
    if (_cameras.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aucune caméra disponible.')),
      );
      return;
    }

    // Préfère la caméra arrière pour les exercices de profil
    final camera = _cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.back,
      orElse: () => _cameras.first,
    );

    // Initialise le notifier avant la navigation
    await ref.read(visionProvider.notifier).initialize(
          exercise: exercise,
          camera: camera,
          workoutSessionId: widget.workoutSessionId,
        );

    if (mounted) {
      context.push('/vision/workout');
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        title: const Text('Vision — Choisissez un exercice'),
        backgroundColor: colors.navBackground,
        foregroundColor: colors.text,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.bar_chart_rounded, color: colors.text),
            tooltip: 'Historique',
            onPressed: () => context.push('/vision/history'),
          ),
        ],
      ),
      body: _loadingCameras
          ? Center(
              child: CircularProgressIndicator(color: colors.accent),
            )
          : Column(
              children: [
                if (_cameras.isEmpty) _buildNoCameraWarning(),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
                  child: Text(
                    'Sélectionnez l\'exercice à analyser',
                    style: TextStyle(color: colors.textMuted, fontSize: 13),
                  ),
                ),
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 12,
                      crossAxisSpacing: 12,
                      childAspectRatio: 1.2,
                    ),
                    itemCount: SupportedExercise.values.length,
                    itemBuilder: (context, index) {
                      final ex = SupportedExercise.values[index];
                      return _ExerciseCard(
                        exercise: ex,
                        isSelected: _selected == ex,
                        onTap: () => _onExerciseTap(ex),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildNoCameraWarning() {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.danger.withOpacity(0.4)),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded,
              color: colors.danger, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Aucune caméra détectée. Vérifiez les permissions.',
              style: TextStyle(color: colors.danger, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Card exercice ─────────────────────────────────────────────────────────────

class _ExerciseCard extends StatelessWidget {
  final SupportedExercise exercise;
  final bool isSelected;
  final VoidCallback onTap;

  const _ExerciseCard({
    required this.exercise,
    required this.isSelected,
    required this.onTap,
  });

  IconData get _icon {
    return switch (exercise) {
      SupportedExercise.squat => Icons.accessibility_new_rounded,
      SupportedExercise.pushUp => Icons.fitness_center_rounded,
      SupportedExercise.plank => Icons.horizontal_rule_rounded,
      SupportedExercise.jumpingJack => Icons.sports_gymnastics_rounded,
      SupportedExercise.lunge => Icons.directions_walk_rounded,
      SupportedExercise.sitUp => Icons.self_improvement_rounded,
    };
  }

  String get _subtitle {
    if (exercise.isTimerBased) return 'Timer · gainage';
    return '${exercise.targetReps} répétitions';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          color: isSelected
              ? colors.accent.withOpacity(0.15)
              : colors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected
                ? colors.accent
                : colors.border,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                _icon,
                color: isSelected
                    ? colors.accent
                    : colors.textSecondary,
                size: 32,
              ),
              const SizedBox(height: 8),
              Text(
                exercise.nameFr,
                style: TextStyle(
                  color: colors.text,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                _subtitle,
                style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 11,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Dialog guide caméra ───────────────────────────────────────────────────────

class _CameraGuideDialog extends StatelessWidget {
  final SupportedExercise exercise;
  final VoidCallback onStart;

  const _CameraGuideDialog({
    required this.exercise,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return AlertDialog(
      backgroundColor: colors.surfaceVariant,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: Row(
        children: [
          Icon(Icons.camera_alt_rounded,
              color: colors.accent, size: 22),
          const SizedBox(width: 8),
          Text(
            exercise.nameFr,
            style: TextStyle(
              color: colors.text,
              fontWeight: FontWeight.w700,
              fontSize: 18,
            ),
          ),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Positionnement caméra',
            style: TextStyle(
              color: colors.accent,
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            exercise.cameraGuide,
            style: TextStyle(color: colors.textSecondary, fontSize: 14),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: colors.navBackground,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                const Icon(Icons.lightbulb_outline_rounded,
                    color: Color(0xFFFFD700), size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Assurez-vous d\'avoir un éclairage suffisant et un fond contrasté.',
                    style:
                        TextStyle(color: colors.textMuted, fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text('Annuler',
              style: TextStyle(color: colors.textMuted)),
        ),
        ElevatedButton(
          onPressed: onStart,
          style: ElevatedButton.styleFrom(
            backgroundColor: colors.accent,
            foregroundColor: Colors.black,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8)),
          ),
          child: const Text('Démarrer',
              style: TextStyle(fontWeight: FontWeight.w700)),
        ),
      ],
    );
  }
}
