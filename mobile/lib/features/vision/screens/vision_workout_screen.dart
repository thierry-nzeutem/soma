/// Écran principal de la session Computer Vision en temps réel (LOT 7).
///
/// Affiche :
///   - Preview caméra plein écran
///   - Overlay squelette pose (PoseOverlayPainter)
///   - Compteur de répétitions
///   - Timer de session
///   - Feedback de classification (positionnement)
///   - Contrôles Start / Pause / Stop
library;

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/theme_extensions.dart';
import '../models/exercise_frame.dart';
import '../models/rep_counter_state.dart';
import '../providers/vision_notifier.dart';
import '../widgets/pose_overlay_painter.dart';
import '../widgets/rep_counter_widget.dart';

// ── Screen ────────────────────────────────────────────────────────────────────

class VisionWorkoutScreen extends ConsumerWidget {
  const VisionWorkoutScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final session = ref.watch(visionProvider);
    final notifier = ref.read(visionProvider.notifier);

    // Erreur d'initialisation
    if (session.status == VisionStatus.error) {
      return _ErrorView(
        message: session.errorMessage ?? 'Erreur inconnue',
        onBack: () => context.pop(),
      );
    }

    // Session terminée → navigation vers résumé
    if (session.status == VisionStatus.finished) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.pushReplacement('/vision/summary');
      });
    }

    final controller = notifier.cameraController;
    final isReady = controller != null && controller.value.isInitialized;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Preview caméra ─────────────────────────────────────────────
          if (isReady) _CameraPreviewFilled(controller: controller),

          // ── Overlay squelette ──────────────────────────────────────────
          if (isReady && session.lastPose != null)
            CustomPaint(
              painter: PoseOverlayPainter(
                pose: session.lastPose!,
                isValid: session.classification?.isValid ?? false,
                validBoneColor: colors.accent,
                invalidBoneColor: const Color(0xFFFFB347),
                jointColor: colors.text,
              ),
            ),

          // ── Spinner initialisation ─────────────────────────────────────
          if (!isReady ||
              session.status == VisionStatus.initializing)
            Center(
              child: CircularProgressIndicator(color: colors.accent),
            ),

          // ── UI overlay ─────────────────────────────────────────────────
          SafeArea(
            child: Column(
              children: [
                _TopBar(session: session),
                const Spacer(),
                _ClassificationFeedback(session: session),
                const SizedBox(height: 12),
                _BottomControls(session: session, notifier: notifier),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Preview caméra centré + rempli ───────────────────────────────────────────

class _CameraPreviewFilled extends StatelessWidget {
  final CameraController controller;

  const _CameraPreviewFilled({required this.controller});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final previewSize = controller.value.previewSize;
        if (previewSize == null) return const SizedBox.shrink();

        // Aspect ratio natif de la caméra
        final nativeRatio = previewSize.height / previewSize.width;
        final screenRatio =
            constraints.maxHeight / constraints.maxWidth;

        double scale;
        if (screenRatio > nativeRatio) {
          // Screen plus haut → on scale la largeur
          scale = constraints.maxHeight / (constraints.maxWidth * nativeRatio);
        } else {
          scale = constraints.maxWidth / (constraints.maxHeight / nativeRatio);
        }

        return Transform.scale(
          scale: scale,
          child: Center(child: CameraPreview(controller)),
        );
      },
    );
  }
}

// ── Barre supérieure ──────────────────────────────────────────────────────────

class _TopBar extends StatelessWidget {
  final VisionSessionState session;

  const _TopBar({required this.session});

  String _formatDuration(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          // Bouton retour
          GestureDetector(
            onTap: () => context.pop(),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.5),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.close_rounded,
                  color: colors.text, size: 20),
            ),
          ),
          const SizedBox(width: 12),
          // Exercice
          Expanded(
            child: Text(
              session.exercise?.nameFr ?? '',
              style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w700,
                fontSize: 18,
                shadows: const [Shadow(color: Colors.black54, blurRadius: 4)],
              ),
            ),
          ),
          // Timer
          if (session.status == VisionStatus.running ||
              session.status == VisionStatus.paused)
            _TimerBadge(
              time: _formatDuration(session.durationSeconds),
              isPaused: session.status == VisionStatus.paused,
            ),
        ],
      ),
    );
  }
}

class _TimerBadge extends StatelessWidget {
  final String time;
  final bool isPaused;

  const _TimerBadge({required this.time, required this.isPaused});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isPaused
              ? const Color(0xFFFFB347)
              : colors.accent,
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isPaused ? Icons.pause_rounded : Icons.radio_button_on_rounded,
            size: 10,
            color: isPaused ? const Color(0xFFFFB347) : colors.accent,
          ),
          const SizedBox(width: 6),
          Text(
            time,
            style: TextStyle(
              color: isPaused ? const Color(0xFFFFB347) : colors.text,
              fontWeight: FontWeight.w700,
              fontSize: 15,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Feedback classification ───────────────────────────────────────────────────

class _ClassificationFeedback extends StatelessWidget {
  final VisionSessionState session;

  const _ClassificationFeedback({required this.session});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final cl = session.classification;
    if (cl == null) return const SizedBox.shrink();

    // ── Feedback V2 : tips par phase quand position valide + running ──
    if (cl.isValid && session.status == VisionStatus.running) {
      return _PhaseTip(
        exercise: session.exercise,
        phase: session.repState.phase,
      );
    }

    // ── Feedback standard : positionnement ────────────────────────────
    final isValid = cl.isValid;
    final color = isValid ? colors.accent : const Color(0xFFFFB347);
    final icon =
        isValid ? Icons.check_circle_rounded : Icons.info_outline_rounded;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: color.withOpacity(0.5)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                cl.feedback,
                style: TextStyle(color: color, fontSize: 13),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Tips par phase (Feedback V2) ──────────────────────────────────────────────

class _PhaseTip extends StatelessWidget {
  final SupportedExercise? exercise;
  final ExercisePhase phase;

  const _PhaseTip({required this.exercise, required this.phase});

  /// Carte (exercice, phase) → message coaching.
  static const Map<(SupportedExercise, ExercisePhase), String> _tips = {
    // Squat
    (SupportedExercise.squat, ExercisePhase.starting): 'Prêt(e) — pieds à largeur d\'épaules',
    (SupportedExercise.squat, ExercisePhase.descending): 'Descends lentement, dos droit',
    (SupportedExercise.squat, ExercisePhase.peak): 'Super profondeur ! Genou dans l\'axe',
    (SupportedExercise.squat, ExercisePhase.ascending): 'Pousse sur les talons !',
    // Push-up
    (SupportedExercise.pushUp, ExercisePhase.starting): 'Gainage serré, corps aligné',
    (SupportedExercise.pushUp, ExercisePhase.descending): 'Coudes à 45° du corps',
    (SupportedExercise.pushUp, ExercisePhase.peak): 'Au plus bas — maintiens !',
    (SupportedExercise.pushUp, ExercisePhase.ascending): 'Pousse fort, expire !',
    // Plank
    (SupportedExercise.plank, ExercisePhase.starting): 'Corps aligné — ventre rentré',
    (SupportedExercise.plank, ExercisePhase.peak): 'Tiens ! Respire régulièrement',
    // Jumping Jack
    (SupportedExercise.jumpingJack, ExercisePhase.starting): 'Position départ — prêt(e) !',
    (SupportedExercise.jumpingJack, ExercisePhase.ascending): 'Ouvre les bras et les jambes !',
    (SupportedExercise.jumpingJack, ExercisePhase.peak): 'Bien ouvert — maintiens !',
    (SupportedExercise.jumpingJack, ExercisePhase.descending): 'Referme en douceur',
    // Lunge
    (SupportedExercise.lunge, ExercisePhase.starting): 'Prêt(e) — hanches de face',
    (SupportedExercise.lunge, ExercisePhase.descending): 'Genou arrière vers le sol',
    (SupportedExercise.lunge, ExercisePhase.peak): 'Genou avant à 90° !',
    (SupportedExercise.lunge, ExercisePhase.ascending): 'Remonte sur la jambe avant',
    // Sit-up
    (SupportedExercise.sitUp, ExercisePhase.starting): 'Allongé(e), mains derrière la nuque',
    (SupportedExercise.sitUp, ExercisePhase.ascending): 'Monte ! Contracte les abdos',
    (SupportedExercise.sitUp, ExercisePhase.peak): 'Contracte fort !',
    (SupportedExercise.sitUp, ExercisePhase.descending): 'Redescends lentement',
  };

  String get _tipText {
    if (exercise == null) return '✓ Bonne position';
    final tip = _tips[(exercise!, phase)];
    return tip ?? '✓ Bonne position';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
              color: colors.accent.withOpacity(0.5)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.tips_and_updates_rounded,
              color: colors.accent,
              size: 16,
            ),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                _tipText,
                style: TextStyle(
                  color: colors.accent,
                  fontSize: 13,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Contrôles bas d'écran ─────────────────────────────────────────────────────

class _BottomControls extends StatelessWidget {
  final VisionSessionState session;
  final VisionNotifier notifier;

  const _BottomControls({
    required this.session,
    required this.notifier,
  });

  @override
  Widget build(BuildContext context) {
    final status = session.status;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          // ── Compteur de répétitions ──────────────────────────────────
          if (status == VisionStatus.running ||
              status == VisionStatus.paused)
            RepCounterWidget(
              count: session.repState.count,
              phase: session.repState.phase,
              isTimerBased: session.exercise?.isTimerBased ?? false,
              durationSeconds: session.durationSeconds,
            ),

          const SizedBox(height: 16),

          // ── Boutons ──────────────────────────────────────────────────
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (status == VisionStatus.ready) ...[
                _PrimaryButton(
                  label: 'Démarrer',
                  icon: Icons.play_arrow_rounded,
                  onTap: notifier.start,
                ),
              ] else if (status == VisionStatus.running) ...[
                _SecondaryButton(
                  label: 'Pause',
                  icon: Icons.pause_rounded,
                  onTap: notifier.pause,
                ),
                const SizedBox(width: 16),
                _StopButton(
                  onTap: () async => await notifier.finish(),
                ),
              ] else if (status == VisionStatus.paused) ...[
                _PrimaryButton(
                  label: 'Reprendre',
                  icon: Icons.play_arrow_rounded,
                  onTap: notifier.resume,
                ),
                const SizedBox(width: 16),
                _StopButton(
                  onTap: () async => await notifier.finish(),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

// ── Boutons ───────────────────────────────────────────────────────────────────

class _PrimaryButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  const _PrimaryButton({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return ElevatedButton.icon(
      onPressed: onTap,
      icon: Icon(icon),
      label: Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
      style: ElevatedButton.styleFrom(
        backgroundColor: colors.accent,
        foregroundColor: Colors.black,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
      ),
    );
  }
}

class _SecondaryButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  const _SecondaryButton({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: colors.text,
        side: BorderSide(color: colors.textMuted),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
      ),
    );
  }
}

class _StopButton extends StatelessWidget {
  final Future<void> Function() onTap;

  const _StopButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return OutlinedButton.icon(
      onPressed: () async {
        final confirm = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: colors.surfaceVariant,
            title: Text('Terminer la session',
                style: TextStyle(color: colors.text)),
            content: Text(
              'Voulez-vous terminer et enregistrer votre session ?',
              style: TextStyle(color: colors.textSecondary),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: Text('Continuer',
                    style: TextStyle(color: colors.textMuted)),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(ctx, true),
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.accent,
                  foregroundColor: Colors.black,
                ),
                child: const Text('Terminer'),
              ),
            ],
          ),
        );
        if (confirm == true) await onTap();
      },
      icon: const Icon(Icons.stop_rounded),
      label: const Text('Terminer'),
      style: OutlinedButton.styleFrom(
        foregroundColor: colors.danger,
        side: BorderSide(color: colors.danger),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
      ),
    );
  }
}

// ── Vue erreur ────────────────────────────────────────────────────────────────

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onBack;

  const _ErrorView({required this.message, required this.onBack});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Scaffold(
      backgroundColor: colors.background,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline_rounded,
                  color: colors.danger, size: 48),
              const SizedBox(height: 16),
              Text(
                message,
                style: TextStyle(color: colors.textSecondary),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: onBack,
                child: const Text('Retour'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
