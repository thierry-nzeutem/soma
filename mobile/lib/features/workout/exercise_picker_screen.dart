/// Écran Sélection Exercice — bibliothèque searchable (LOT 6).
///
/// Charge tous les exercices via [exercisesProvider].
/// Filtre local côté client (cache).
/// Retourne un ExerciseLibrary via Navigator.pop.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/workout.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'workout_notifier.dart';

class ExercisePickerScreen extends ConsumerStatefulWidget {
  const ExercisePickerScreen({super.key});

  @override
  ConsumerState<ExercisePickerScreen> createState() =>
      _ExercisePickerScreenState();
}

class _ExercisePickerScreenState
    extends ConsumerState<ExercisePickerScreen> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final state = ref.watch(exercisesProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Choisir un exercice'),
      body: Column(
        children: [
          // Barre de recherche
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchCtrl,
              autofocus: true,
              style: TextStyle(color: colors.text, fontSize: 14),
              onChanged: (q) =>
                  ref.read(exercisesProvider.notifier).setFilter(q),
              decoration: InputDecoration(
                hintText: 'Rechercher un exercice\u2026',
                hintStyle:
                    TextStyle(color: colors.textMuted),
                prefixIcon: Icon(Icons.search_rounded,
                    color: colors.textMuted),
                suffixIcon: state.filter.isNotEmpty
                    ? GestureDetector(
                        onTap: () {
                          _searchCtrl.clear();
                          ref
                              .read(exercisesProvider.notifier)
                              .setFilter('');
                        },
                        child: Icon(Icons.close_rounded,
                            color: colors.textMuted),
                      )
                    : null,
                filled: true,
                fillColor: colors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide:
                      BorderSide(color: colors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide:
                      BorderSide(color: colors.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide:
                      const BorderSide(color: Color(0xFFFFB347)),
                ),
                contentPadding:
                    const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          // Liste
          Expanded(child: _ExerciseList(state: state)),
        ],
      ),
    );
  }
}

class _ExerciseList extends StatelessWidget {
  final ExercisesState state;

  const _ExerciseList({required this.state});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    if (state.isLoading) {
      return const Center(
        child:
            CircularProgressIndicator(color: Color(0xFFFFB347)),
      );
    }
    if (state.error != null) {
      return Center(
        child: Text(
          'Erreur : ${state.error}',
          style: TextStyle(
              color: colors.danger, fontSize: 13),
        ),
      );
    }
    final items = state.filtered;
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.sports_gymnastics_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Aucun exercice trouvé',
              style: TextStyle(color: colors.textMuted, fontSize: 14),
            ),
          ],
        ),
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      itemCount: items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 6),
      itemBuilder: (ctx, i) => _ExerciseRow(
        exercise: items[i],
        onTap: () => Navigator.of(ctx).pop(items[i]),
      ),
    );
  }
}

class _ExerciseRow extends StatelessWidget {
  final ExerciseLibrary exercise;
  final VoidCallback onTap;

  const _ExerciseRow({required this.exercise, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Material(
      color: colors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: colors.border),
          ),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFFFB347).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.fitness_center_rounded,
                    color: Color(0xFFFFB347), size: 18),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      exercise.displayName,
                      style: TextStyle(
                        color: colors.text,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (exercise.categoryLabel != null ||
                        exercise.muscleGroups.isNotEmpty)
                      Text(
                        [
                          if (exercise.categoryLabel != null)
                            exercise.categoryLabel!,
                          ...exercise.muscleGroups.take(2),
                        ].join(' \u00b7 '),
                        style: TextStyle(
                          color: colors.textSecondary,
                          fontSize: 11,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
              if (exercise.difficultyLevel != null)
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: colors.border,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    exercise.difficultyLevel!,
                    style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 10,
                    ),
                  ),
                ),
              const SizedBox(width: 8),
              const Icon(Icons.add_circle_outline_rounded,
                  color: Color(0xFFFFB347), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
