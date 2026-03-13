/// Écran Sessions Entraînement — liste + FAB créer session (LOT 6).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/workout.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'workout_notifier.dart';

class WorkoutSessionsScreen extends ConsumerWidget {
  const WorkoutSessionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final state = ref.watch(workoutSessionsProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Entraînements',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () =>
                ref.read(workoutSessionsProvider.notifier).refresh(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFFFFB347),
        child: Icon(Icons.add, color: colors.text),
        onPressed: () => context.push('/journal/workout/create'),
      ),
      body: state.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: Color(0xFFFFB347)),
        ),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.cloud_off_rounded,
                    size: 48, color: colors.textMuted),
                const SizedBox(height: 16),
                Text('Erreur de chargement',
                    style: TextStyle(color: colors.text, fontSize: 16)),
                const SizedBox(height: 8),
                Text(err.toString(),
                    style: TextStyle(
                        color: colors.textSecondary, fontSize: 12),
                    textAlign: TextAlign.center,
                    maxLines: 3),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: () =>
                      ref.read(workoutSessionsProvider.notifier).refresh(),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Réessayer'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFFB347),
                    foregroundColor: Colors.black,
                  ),
                ),
              ],
            ),
          ),
        ),
        data: (sessions) => RefreshIndicator(
          color: const Color(0xFFFFB347),
          backgroundColor: colors.surface,
          onRefresh: () =>
              ref.read(workoutSessionsProvider.notifier).refresh(),
          child: sessions.isEmpty
              ? const _EmptySessions()
              : ListView.separated(
                  padding:
                      const EdgeInsets.fromLTRB(16, 16, 16, 100),
                  itemCount: sessions.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (ctx, i) => _SessionCard(
                    session: sessions[i],
                    onTap: () => context
                        .push('/journal/workout/${sessions[i].id}'),
                  ),
                ),
        ),
      ),
    );
  }
}

class _SessionCard extends StatelessWidget {
  final WorkoutSession session;
  final VoidCallback onTap;

  const _SessionCard({required this.session, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = session.isCompleted
        ? colors.accent
        : session.isInProgress
            ? const Color(0xFFFFB347)
            : colors.textMuted;

    return Material(
      color: colors.surface,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: colors.border),
          ),
          child: Row(
            children: [
              // Badge type
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.fitness_center_rounded,
                    color: color, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      session.typeLabel,
                      style: TextStyle(
                        color: colors.text,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        Text(
                          session.locationLabel,
                          style: TextStyle(
                              color: colors.textSecondary, fontSize: 12),
                        ),
                        if (session.exercises.isNotEmpty) ...[
                          Text(' \u00b7 ',
                              style: TextStyle(
                                  color: colors.textMuted)),
                          Text(
                            '${session.exercises.length} exercice${session.exercises.length > 1 ? 's' : ''}',
                            style: TextStyle(
                                color: colors.textSecondary, fontSize: 12),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      session.statusLabel,
                      style: TextStyle(
                          color: color,
                          fontSize: 11,
                          fontWeight: FontWeight.w600),
                    ),
                  ),
                  const SizedBox(height: 4),
                  if (session.startedAt != null)
                    Text(
                      session.startedAt!.substring(0, 10),
                      style: TextStyle(
                          color: colors.textMuted, fontSize: 11),
                    ),
                ],
              ),
              const SizedBox(width: 4),
              Icon(Icons.chevron_right_rounded,
                  color: colors.textMuted, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptySessions extends StatelessWidget {
  const _EmptySessions();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.sports_gymnastics_rounded,
                size: 56, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Aucune séance',
              style: TextStyle(color: colors.text, fontSize: 18),
            ),
            const SizedBox(height: 8),
            Text(
              'Créez votre première séance avec le +',
              style: TextStyle(color: colors.textMuted, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}
