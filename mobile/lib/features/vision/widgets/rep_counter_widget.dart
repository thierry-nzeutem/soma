/// RepCounterWidget — affichage du compteur de répétitions (LOT 7).
///
/// Affiche le nombre de répétitions courant et la phase active.
/// Pour les exercices timer-based (plank), affiche la durée à la place.
library;

import 'package:flutter/material.dart';

import '../../../core/theme/theme_extensions.dart';
import '../../../core/theme/soma_colors.dart';
import '../models/rep_counter_state.dart';

// ── Widget principal ──────────────────────────────────────────────────────────

class RepCounterWidget extends StatelessWidget {
  final int count;
  final ExercisePhase phase;
  final bool isTimerBased;
  final int durationSeconds;

  const RepCounterWidget({
    super.key,
    required this.count,
    required this.phase,
    required this.isTimerBased,
    required this.durationSeconds,
  });

  String get _durationLabel {
    final m = durationSeconds ~/ 60;
    final s = durationSeconds % 60;
    if (m == 0) return '${s}s';
    return '${m}m${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.75),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: phase.isActive
              ? colors.accent.withOpacity(0.6)
              : colors.textMuted,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Nombre / timer
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            transitionBuilder: (child, anim) => ScaleTransition(
              scale: anim,
              child: child,
            ),
            child: Text(
              isTimerBased ? _durationLabel : count.toString(),
              key: ValueKey(isTimerBased ? durationSeconds : count),
              style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w900,
                fontSize: 48,
                fontFeatures: const [FontFeature.tabularFigures()],
                shadows: const [Shadow(color: Colors.black54, blurRadius: 8)],
              ),
            ),
          ),

          const SizedBox(width: 16),

          // Phase label
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                isTimerBased ? 'Maintenu' : 'reps',
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 4),
              _PhaseBadge(phase: phase),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Badge de phase ────────────────────────────────────────────────────────────

class _PhaseBadge extends StatelessWidget {
  final ExercisePhase phase;

  const _PhaseBadge({required this.phase});

  Color _color(SomaColors colors) {
    return switch (phase) {
      ExercisePhase.peak => colors.accent,
      ExercisePhase.descending ||
      ExercisePhase.ascending =>
        colors.info,
      ExercisePhase.starting => colors.textMuted,
      ExercisePhase.unknown => colors.textMuted,
    };
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final c = _color(colors);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: c.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: c.withOpacity(0.4)),
      ),
      child: Text(
        phase.label,
        style: TextStyle(
          color: c,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
