/// Journal Hub — ecran d'accueil du journal sante (LOT 6).
///
/// 4 cartes d'entree : Nutrition, Entrainement, Hydratation, Sommeil.
/// Chaque carte affiche un resume du jour et ouvre son sous-ecran.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/hydration.dart';
import '../../core/theme/theme_extensions.dart';
import '../hydration/hydration_notifier.dart';
import '../nutrition/nutrition_notifier.dart';
import '../sleep/sleep_notifier.dart';
import '../workout/workout_notifier.dart';
import '../../shared/widgets/soma_app_bar.dart';

class JournalHubScreen extends ConsumerWidget {
  const JournalHubScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Journal'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _SectionTitle(
            icon: Icons.today_rounded,
            label: "Aujourd'hui",
          ),
          const SizedBox(height: 12),
          _NutritionCard(ref: ref),
          const SizedBox(height: 12),
          _WorkoutCard(ref: ref),
          const SizedBox(height: 12),
          _HydrationCard(ref: ref),
          const SizedBox(height: 12),
          _SleepCard(ref: ref),
          const SizedBox(height: 24),
          _SectionTitle(
            icon: Icons.science_rounded,
            label: 'Sante avancee',
          ),
          const SizedBox(height: 12),
          _JournalCard(
            icon: Icons.biotech_rounded,
            title: 'Biomarqueurs',
            accentColor: const Color(0xFF00B4D8),
            subtitle: 'Analyses biologiques · impact longevite',
            onTap: () => context.push('/biomarkers'),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

// -- Cartes --------------------------------------------------------------------

class _NutritionCard extends ConsumerWidget {
  const _NutritionCard({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef wRef) {
    final state = wRef.watch(nutritionSummaryProvider);
    return _JournalCard(
      icon: Icons.restaurant_rounded,
      title: 'Nutrition',
      accentColor: const Color(0xFFFF6B6B),
      subtitle: state.when(
        loading: () => 'Chargement...',
        error: (_, __) => 'Erreur de chargement',
        data: (s) =>
            '${s.totals.calories.toStringAsFixed(0)} kcal · '
            '${s.mealCount} repas · '
            'proteines ${s.totals.proteinG.toStringAsFixed(0)}g',
      ),
      onTap: () => context.push('/journal/nutrition'),
    );
  }
}

class _WorkoutCard extends ConsumerWidget {
  const _WorkoutCard({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef wRef) {
    final state = wRef.watch(workoutSessionsProvider);
    return _JournalCard(
      icon: Icons.fitness_center_rounded,
      title: 'Entrainement',
      accentColor: const Color(0xFFFFB347),
      subtitle: state.when(
        loading: () => 'Chargement...',
        error: (_, __) => 'Erreur de chargement',
        data: (sessions) {
          final today = sessions
              .where((s) => s.startedAt?.startsWith(
                    DateTime.now().toIso8601String().substring(0, 10),
                  ) ??
                  false)
              .toList();
          if (today.isEmpty) return 'Aucune seance aujourd\'hui';
          return '${today.length} seance${today.length > 1 ? 's' : ''} aujourd\'hui';
        },
      ),
      onTap: () => context.push('/journal/workout'),
    );
  }
}

class _HydrationCard extends ConsumerWidget {
  const _HydrationCard({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef wRef) {
    final state = wRef.watch(hydrationProvider);
    return _JournalCard(
      icon: Icons.water_drop_rounded,
      title: 'Hydratation',
      accentColor: const Color(0xFF00B4D8),
      subtitle: state.when(
        loading: () => 'Chargement...',
        error: (_, __) => 'Erreur de chargement',
        data: (s) {
          final liters = (s.totalMl / 1000).toStringAsFixed(1);
          final target = (s.targetMl / 1000).toStringAsFixed(1);
          final pct = s.pct.toStringAsFixed(0);
          return '$liters L / $target L · $pct%';
        },
      ),
      onTap: () => context.push('/journal/hydration'),
    );
  }
}

class _SleepCard extends ConsumerWidget {
  const _SleepCard({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef wRef) {
    final state = wRef.watch(sleepProvider);
    return _JournalCard(
      icon: Icons.bedtime_rounded,
      title: 'Sommeil',
      accentColor: const Color(0xFF9B72CF),
      subtitle: state.when(
        loading: () => 'Chargement...',
        error: (_, __) => 'Erreur de chargement',
        data: (sessions) {
          if (sessions.isEmpty) return 'Aucune donnee recente';
          final last = sessions.first;
          return '${last.durationLabel} · ${last.qualityLabel}';
        },
      ),
      onTap: () => context.push('/journal/sleep'),
    );
  }
}

// -- Widgets communs -----------------------------------------------------------

class _SectionTitle extends StatelessWidget {
  final IconData icon;
  final String label;

  const _SectionTitle({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Row(
      children: [
        Icon(icon, size: 16, color: colors.accent),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            color: colors.textMuted,
            fontSize: 13,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }
}

class _JournalCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final Color accentColor;
  final String subtitle;
  final VoidCallback onTap;

  const _JournalCard({
    required this.icon,
    required this.title,
    required this.accentColor,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Material(
      color: colors.surface,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: colors.border),
          ),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: accentColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: accentColor, size: 22),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: colors.text,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded,
                  color: colors.textMuted, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
