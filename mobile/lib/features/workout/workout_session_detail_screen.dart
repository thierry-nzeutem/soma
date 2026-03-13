/// Écran Détail Session — exercices + séries + compléter (LOT 6).
///
/// Charge via [sessionDetailProvider.family].
/// Permet d'ajouter des exercices (ExercisePickerScreen) et des séries.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/workout.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'workout_notifier.dart';
import 'exercise_picker_screen.dart';

class WorkoutSessionDetailScreen extends ConsumerWidget {
  final String sessionId;

  const WorkoutSessionDetailScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final state = ref.watch(sessionDetailProvider(sessionId));

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Séance'),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: const Color(0xFFFFB347)),
        ),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.error_outline_rounded,
                    size: 48, color: colors.textMuted),
                const SizedBox(height: 12),
                Text(
                  'Erreur : $err',
                  style: TextStyle(
                      color: colors.textSecondary, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
        data: (session) => _SessionDetailBody(
          session: session,
          sessionId: sessionId,
        ),
      ),
    );
  }
}

class _SessionDetailBody extends ConsumerWidget {
  final WorkoutSession session;
  final String sessionId;

  const _SessionDetailBody({
    required this.session,
    required this.sessionId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        // Header session
        _SessionHeader(session: session),

        // Liste exercices
        Expanded(
          child: session.exercises.isEmpty
              ? _EmptyExercises(sessionId: sessionId)
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                  itemCount: session.exercises.length,
                  itemBuilder: (ctx, i) => _ExerciseCard(
                    entry: session.exercises[i],
                    sessionId: sessionId,
                  ),
                ),
        ),

        // Actions bottom
        _BottomActions(session: session, sessionId: sessionId),
      ],
    );
  }
}

class _SessionHeader extends StatelessWidget {
  final WorkoutSession session;

  const _SessionHeader({required this.session});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final statusColor = session.isCompleted
        ? colors.accent
        : session.isInProgress
            ? const Color(0xFFFFB347)
            : colors.textMuted;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(bottom: BorderSide(color: colors.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  session.typeLabel,
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${session.locationLabel} · ${session.exercises.length} exercice${session.exercises.length != 1 ? 's' : ''}',
                  style: TextStyle(
                      color: colors.textSecondary, fontSize: 13),
                ),
              ],
            ),
          ),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                  color: statusColor.withOpacity(0.3)),
            ),
            child: Text(
              session.statusLabel,
              style: TextStyle(
                  color: statusColor,
                  fontSize: 12,
                  fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _ExerciseCard extends ConsumerWidget {
  final ExerciseEntry entry;
  final String sessionId;

  const _ExerciseCard(
      {required this.entry, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Titre exercice
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
            child: Row(
              children: [
                const Icon(Icons.fitness_center_rounded,
                    color: Color(0xFFFFB347), size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    entry.exerciseName,
                    style: TextStyle(
                      color: colors.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Text(
                  '${entry.totalSets}×${entry.totalReps} reps',
                  style: TextStyle(
                      color: colors.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
          // Séries
          ...entry.sets.asMap().entries.map((e) => _SetRow(
                set: e.value,
                index: e.key + 1,
              )),
          // Bouton +série
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 4, 14, 12),
            child: GestureDetector(
              onTap: () => _addSet(context, ref, entry.id),
              child: const Row(
                children: [
                  Icon(Icons.add_rounded,
                      color: Color(0xFFFFB347), size: 16),
                  SizedBox(width: 6),
                  Text(
                    'Ajouter une série',
                    style: TextStyle(
                      color: Color(0xFFFFB347),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _addSet(
      BuildContext context, WidgetRef ref, String exerciseEntryId) async {
    final result = await _showAddSetDialog(context);
    if (result != null) {
      await addSetToExercise(ref, sessionId, exerciseEntryId, result);
    }
  }

  Future<Map<String, dynamic>?> _showAddSetDialog(
      BuildContext context) async {
    final colors = context.somaColors;
    final repsCtrl = TextEditingController();
    final weightCtrl = TextEditingController();
    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: colors.surface,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16)),
        title: Text('Ajouter une série',
            style: TextStyle(color: colors.text, fontSize: 16)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _DialogField(ctrl: repsCtrl, label: 'Répétitions'),
            const SizedBox(height: 10),
            _DialogField(
                ctrl: weightCtrl, label: 'Charge (kg)', optional: true),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('Annuler',
                style: TextStyle(color: colors.textSecondary)),
          ),
          ElevatedButton(
            onPressed: () {
              final reps = int.tryParse(repsCtrl.text);
              if (reps == null) return;
              Navigator.of(ctx).pop({
                'reps': reps,
                if (weightCtrl.text.isNotEmpty)
                  'weight_kg': double.tryParse(weightCtrl.text),
                'set_type': 'normal',
              });
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFFB347),
              foregroundColor: Colors.black,
            ),
            child: const Text('Ajouter'),
          ),
        ],
      ),
    );
  }
}

class _SetRow extends StatelessWidget {
  final WorkoutSet set;
  final int index;

  const _SetRow({required this.set, required this.index});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 2, 14, 2),
      child: Row(
        children: [
          SizedBox(
            width: 24,
            child: Text(
              '$index',
              style: TextStyle(
                  color: colors.textMuted, fontSize: 12),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(
                horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: colors.border,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              set.setType,
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 10),
            ),
          ),
          const SizedBox(width: 10),
          Text(
            set.display,
            style: TextStyle(color: colors.text, fontSize: 13),
          ),
          if (set.isPr) ...[
            const SizedBox(width: 8),
            const Text('\u{1F3C6}',
                style: TextStyle(fontSize: 12)),
          ],
        ],
      ),
    );
  }
}

class _EmptyExercises extends StatelessWidget {
  final String sessionId;

  const _EmptyExercises({required this.sessionId});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.add_circle_outline_rounded,
                size: 56, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Aucun exercice',
              style: TextStyle(color: colors.text, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              'Ajoutez des exercices via le bouton ci-dessous',
              style: TextStyle(color: colors.textMuted, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _BottomActions extends ConsumerWidget {
  final WorkoutSession session;
  final String sessionId;

  const _BottomActions(
      {required this.session, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.background,
        border: Border(top: BorderSide(color: colors.border)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── Ligne 1 : Exercice | Terminer ──────────────────────────
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Exercice'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFFFB347),
                    side: const BorderSide(color: Color(0xFFFFB347)),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () => _pickExercise(context, ref),
                ),
              ),
              if (session.isInProgress) ...[
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.check_rounded),
                    label: const Text('Terminer'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colors.accent,
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: () => _complete(context, ref),
                  ),
                ),
              ],
            ],
          ),

          // ── Ligne 2 : Analyser avec Computer Vision ─────────────────
          if (session.isInProgress) ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.camera_alt_rounded, size: 18),
                label: const Text('Analyser avec Computer Vision'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: colors.accent,
                  side: BorderSide(color: colors.accent),
                  padding: const EdgeInsets.symmetric(vertical: 11),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: () =>
                    context.push('/vision/setup?sessionId=$sessionId'),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _pickExercise(BuildContext context, WidgetRef ref) async {
    final exercise = await Navigator.of(context).push<dynamic>(
      MaterialPageRoute(
        builder: (_) => ExercisePickerScreen(),
      ),
    );
    if (exercise != null) {
      await addExerciseToSession(ref, sessionId, {
        'exercise_id': exercise.id,
        'exercise_name': exercise.displayName,
      });
    }
  }

  Future<void> _complete(BuildContext context, WidgetRef ref) async {
    await ref
        .read(workoutSessionsProvider.notifier)
        .completeSession(sessionId);
    ref.invalidate(sessionDetailProvider(sessionId));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Séance complétée !'),
          backgroundColor: context.somaColors.accent,
        ),
      );
    }
  }
}

class _DialogField extends StatelessWidget {
  final TextEditingController ctrl;
  final String label;
  final bool optional;

  const _DialogField({
    required this.ctrl,
    required this.label,
    this.optional = false,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return TextField(
      controller: ctrl,
      keyboardType:
          const TextInputType.numberWithOptions(decimal: true),
      style: TextStyle(color: colors.text),
      decoration: InputDecoration(
        labelText: optional ? '$label (optionnel)' : label,
        labelStyle: TextStyle(color: colors.textMuted),
        filled: true,
        fillColor: colors.border,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}
