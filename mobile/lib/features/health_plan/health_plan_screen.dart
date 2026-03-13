/// Ecran Health Plan — morning briefing et plan du jour SOMA.
///
/// Consomme GET /api/v1/health/plan/today via [healthPlanProvider].
/// Affiche : seance recommandee, cibles nutritionnelles, conseils, alertes.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/health_plan.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'health_plan_notifier.dart';

class HealthPlanScreen extends ConsumerWidget {
  const HealthPlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(healthPlanProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Plan du Jour',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(healthPlanProvider.notifier).refresh(),
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => _PlanError(
          message: err.toString(),
          onRetry: () => ref.read(healthPlanProvider.notifier).refresh(),
        ),
        data: (plan) => RefreshIndicator(
          color: colors.accent,
          backgroundColor: colors.surface,
          onRefresh: () => ref.read(healthPlanProvider.notifier).refresh(),
          child: _PlanContent(plan: plan),
        ),
      ),
    );
  }
}

// -- Contenu du plan -----------------------------------------------------------

class _PlanContent extends StatelessWidget {
  final DailyHealthPlan plan;

  const _PlanContent({required this.plan});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Bandeau de recuperation
        _ReadinessBadge(
          level: plan.readinessLevel,
          score: plan.readinessScore,
          intensity: plan.recommendedIntensity,
        ),
        const SizedBox(height: 16),

        // Alertes (si presentes)
        if (plan.alerts.isNotEmpty) ...[
          _AlertsSection(alerts: plan.alerts),
          const SizedBox(height: 16),
        ],

        // Seance recommandee
        if (plan.workoutRecommendation != null) ...[
          _WorkoutCard(workout: plan.workoutRecommendation!),
          const SizedBox(height: 16),
        ],

        // Fenetre de jeune (si IF active)
        if (plan.intermittentFasting && plan.eatWindow != null) ...[
          _FastingCard(eatWindow: plan.eatWindow!, fastingWindow: plan.fastingWindow),
          const SizedBox(height: 16),
        ],

        // Cibles nutritionnelles
        if (plan.nutritionTargets != null) ...[
          _NutritionSection(
            targets: plan.nutritionTargets!,
            focus: plan.nutritionFocus,
          ),
          const SizedBox(height: 16),
        ],

        // Conseils du jour
        if (plan.dailyTips.isNotEmpty) ...[
          _TipsSection(tips: plan.dailyTips),
          const SizedBox(height: 24),
        ],
      ],
    );
  }
}

// -- Sous-widgets --------------------------------------------------------------

class _ReadinessBadge extends StatelessWidget {
  final String level;
  final double? score;
  final String intensity;

  const _ReadinessBadge({
    required this.level,
    this.score,
    required this.intensity,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = _levelColor(level, colors);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withAlpha(76)),
      ),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withAlpha(38),
              border: Border.all(color: color, width: 2),
            ),
            child: Center(
              child: Text(
                score != null ? score!.toStringAsFixed(0) : '—',
                style: TextStyle(
                  color: color,
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  level.toUpperCase(),
                  style: TextStyle(
                    color: color,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Intensite recommandee : $intensity',
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static Color _levelColor(String level, dynamic colors) {
    switch (level.toLowerCase()) {
      case 'high':
      case 'excellent':
        return colors.accent;
      case 'moderate':
      case 'good':
        return const Color(0xFFFFB347);
      default:
        return colors.danger;
    }
  }
}

class _WorkoutCard extends StatelessWidget {
  final WorkoutRecommendation workout;

  const _WorkoutCard({required this.workout});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // En-tete
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
            child: Row(
              children: [
                const Icon(Icons.fitness_center_rounded,
                    color: Color(0xFFFFB347), size: 20),
                const SizedBox(width: 8),
                Text(
                  'Seance Recommandee',
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                if (workout.durationMinutes != null)
                  _Chip(
                    label: '${workout.durationMinutes} min',
                    color: colors.border,
                  ),
              ],
            ),
          ),
          Divider(color: colors.border, height: 1),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Type + intensite
                Row(
                  children: [
                    _Chip(
                      label: workout.type.toUpperCase(),
                      color: const Color(0xFFFFB347).withAlpha(38),
                      textColor: const Color(0xFFFFB347),
                    ),
                    if (workout.intensity != null) ...[
                      const SizedBox(width: 8),
                      _Chip(
                        label: workout.intensity!,
                        color: colors.border,
                      ),
                    ],
                  ],
                ),
                if (workout.description != null) ...[
                  const SizedBox(height: 10),
                  Text(
                    workout.description!,
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 13,
                      height: 1.5,
                    ),
                  ),
                ],
                if (workout.exercises.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Exercices suggeres',
                    style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...workout.exercises.map(
                    (ex) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        children: [
                          const Text('• ',
                              style: TextStyle(
                                  color: Color(0xFFFFB347), fontSize: 14)),
                          Text(
                            ex,
                            style: const TextStyle(
                              color: Color(0xFFAAAAAA),
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _NutritionSection extends StatelessWidget {
  final NutritionTargetsSummary targets;
  final String? focus;

  const _NutritionSection({required this.targets, this.focus});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.restaurant_rounded,
                  color: colors.accent, size: 20),
              const SizedBox(width: 8),
              Text(
                'Cibles Nutritionnelles',
                style: TextStyle(
                  color: colors.text,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          if (focus != null) ...[
            const SizedBox(height: 8),
            Text(
              focus!,
              style: TextStyle(
                  color: colors.accent, fontSize: 13),
            ),
          ],
          const SizedBox(height: 16),
          // Grille macros
          Row(
            children: [
              if (targets.caloriesKcal != null)
                Expanded(
                  child: _MacroTile(
                    label: 'Calories',
                    value: '${targets.caloriesKcal!.toStringAsFixed(0)} kcal',
                    color: const Color(0xFFFF6B6B),
                  ),
                ),
              if (targets.proteinG != null) ...[
                const SizedBox(width: 8),
                Expanded(
                  child: _MacroTile(
                    label: 'Proteines',
                    value: '${targets.proteinG!.toStringAsFixed(0)} g',
                    color: const Color(0xFFFFB347),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              if (targets.carbsG != null)
                Expanded(
                  child: _MacroTile(
                    label: 'Glucides',
                    value: '${targets.carbsG!.toStringAsFixed(0)} g',
                    color: colors.info,
                  ),
                ),
              if (targets.fatG != null) ...[
                const SizedBox(width: 8),
                Expanded(
                  child: _MacroTile(
                    label: 'Lipides',
                    value: '${targets.fatG!.toStringAsFixed(0)} g',
                    color: const Color(0xFF9B72CF),
                  ),
                ),
              ],
            ],
          ),
          if (targets.waterMl != null) ...[
            const SizedBox(height: 8),
            _MacroTile(
              label: 'Eau',
              value: '${(targets.waterMl! / 1000).toStringAsFixed(1)} L',
              color: colors.info,
            ),
          ],
        ],
      ),
    );
  }
}

class _MacroTile extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _MacroTile({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(50)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: TextStyle(
                  color: color, fontSize: 11, fontWeight: FontWeight.w600)),
          const SizedBox(height: 2),
          Text(value,
              style: TextStyle(
                  color: colors.text,
                  fontSize: 14,
                  fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _FastingCard extends StatelessWidget {
  final String eatWindow;
  final String? fastingWindow;

  const _FastingCard({required this.eatWindow, this.fastingWindow});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF9B72CF).withAlpha(20),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF9B72CF).withAlpha(60)),
      ),
      child: Row(
        children: [
          const Icon(Icons.access_time_rounded,
              color: Color(0xFF9B72CF), size: 20),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Fenetre alimentaire',
                  style: TextStyle(
                      color: Color(0xFF9B72CF),
                      fontSize: 12,
                      fontWeight: FontWeight.w600)),
              Text(eatWindow,
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w700)),
              if (fastingWindow != null)
                Text('Jeune : $fastingWindow',
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }
}

class _AlertsSection extends StatelessWidget {
  final List<String> alerts;

  const _AlertsSection({required this.alerts});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.danger.withAlpha(15),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.danger.withAlpha(60)),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        children: alerts
            .map(
              (alert) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.warning_rounded,
                        color: colors.danger, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        alert,
                        style: TextStyle(
                            color: colors.textSecondary, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}

class _TipsSection extends StatelessWidget {
  final List<String> tips;

  const _TipsSection({required this.tips});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Text(
            'Conseils du Jour',
            style: TextStyle(
              color: colors.text,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        ...tips.asMap().entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: _TipTile(index: entry.key + 1, tip: entry.value),
              ),
            ),
      ],
    );
  }
}

class _TipTile extends StatelessWidget {
  final int index;
  final String tip;

  const _TipTile({required this.index, required this.tip});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: colors.accent,
            ),
            child: Center(
              child: Text(
                '$index',
                style: const TextStyle(
                  color: Colors.black,
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              tip,
              style: TextStyle(
                color: colors.textSecondary,
                fontSize: 13,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final Color color;
  final Color? textColor;

  const _Chip({
    required this.label,
    required this.color,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: textColor ?? colors.textMuted,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _PlanError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _PlanError({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.event_busy_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Plan du jour indisponible',
              style: TextStyle(color: colors.text, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(message,
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 12),
                textAlign: TextAlign.center),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
