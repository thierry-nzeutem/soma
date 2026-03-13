/// AdaptiveNutritionScreen — Nutrition Adaptative SOMA LOT 11.
///
/// Affiche le plan nutritionnel du jour : type de journée, macros, stratégie.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/adaptive_nutrition.dart';
import '../../shared/widgets/adaptive_macro_card.dart';
import '../../shared/widgets/day_type_badge.dart';
import 'adaptive_nutrition_notifier.dart';

class AdaptiveNutritionScreen extends ConsumerWidget {
  const AdaptiveNutritionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final planAsync = ref.watch(adaptiveNutritionProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Nutrition Adaptative'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () =>
                ref.read(adaptiveNutritionProvider.notifier).refresh(),
          ),
        ],
      ),
      body: planAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              const Text('Impossible de charger le plan nutritionnel'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () =>
                    ref.read(adaptiveNutritionProvider.notifier).refresh(),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (plan) {
          if (plan == null) {
            return const _EmptyView();
          }
          return _AdaptiveNutritionBody(plan: plan);
        },
      ),
    );
  }
}

// ── Corps principal ───────────────────────────────────────────────────────────

class _AdaptiveNutritionBody extends StatelessWidget {
  final AdaptiveNutritionPlan plan;
  const _AdaptiveNutritionBody({required this.plan});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return RefreshIndicator(
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.symmetric(vertical: 12),
        children: [
          // Type de journée + date
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                DayTypeBadge(dayType: plan.dayType, large: true),
                Text(
                  plan.targetDate,
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.5),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Cible calorique principale
          _CalorieTargetCard(plan: plan),
          const SizedBox(height: 8),

          // Macros (grid 2 colonnes)
          _SectionHeader(title: '🥗 Macronutriments'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: GridView.count(
              crossAxisCount: 2,
              childAspectRatio: 1.4,
              crossAxisSpacing: 0,
              mainAxisSpacing: 0,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                AdaptiveMacroCard(
                  macroName: 'Protéines',
                  emoji: '🥩',
                  target: plan.proteinTarget,
                ),
                AdaptiveMacroCard(
                  macroName: 'Glucides',
                  emoji: '🍚',
                  target: plan.carbTarget,
                ),
                AdaptiveMacroCard(
                  macroName: 'Lipides',
                  emoji: '🥑',
                  target: plan.fatTarget,
                ),
                AdaptiveMacroCard(
                  macroName: 'Fibres',
                  emoji: '🥦',
                  target: plan.fiberTarget,
                ),
              ],
            ),
          ),

          // Hydratation
          _SectionHeader(title: '💧 Hydratation'),
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  const Text('💧', style: TextStyle(fontSize: 24)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${plan.hydrationTarget.value.toStringAsFixed(0)} ${plan.hydrationTarget.unit}',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: const Color(0xFF3B82F6),
                          ),
                        ),
                        Text(
                          plan.hydrationTarget.rationale,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color:
                                theme.colorScheme.onSurface.withOpacity(0.6),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Stratégie
          _SectionHeader(title: '⏰ Stratégie alimentaire'),
          _StrategyCard(plan: plan),

          // Alertes
          if (plan.alerts.isNotEmpty) ...[
            _SectionHeader(title: '⚠️ Alertes'),
            ...plan.alerts.map(
              (a) => Card(
                margin:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
                color: const Color(0xFFF59E0B).withOpacity(0.08),
                child: ListTile(
                  leading: const Icon(Icons.warning_amber_outlined,
                      color: Color(0xFFF59E0B)),
                  title: Text(a, style: theme.textTheme.bodySmall),
                  dense: true,
                ),
              ),
            ),
          ],

          // Bouton recalculer
          Padding(
            padding: const EdgeInsets.all(16),
            child: OutlinedButton.icon(
              onPressed: null, // naviguer vers recompute ou direct call
              icon: const Icon(Icons.calculate_outlined),
              label: const Text('Recalculer le plan'),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

// ── Card calorique ────────────────────────────────────────────────────────────

class _CalorieTargetCard extends StatelessWidget {
  final AdaptiveNutritionPlan plan;
  const _CalorieTargetCard({required this.plan});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('🔥', style: TextStyle(fontSize: 28)),
                const SizedBox(width: 8),
                Text(
                  '${plan.calorieTarget.value.toStringAsFixed(0)} kcal',
                  style: theme.textTheme.displaySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFFF97316),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              plan.calorieTarget.rationale,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

// ── Card stratégie ────────────────────────────────────────────────────────────

class _StrategyCard extends StatelessWidget {
  final AdaptiveNutritionPlan plan;
  const _StrategyCard({required this.plan});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              plan.mealTimingStrategy,
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            if (plan.fastingCompatible) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.access_time,
                      size: 16, color: Color(0xFF8B5CF6)),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      plan.fastingRationale,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: const Color(0xFF8B5CF6),
                      ),
                    ),
                  ),
                ],
              ),
            ],
            if (plan.preWorkoutGuidance != null) ...[
              const SizedBox(height: 8),
              _GuidanceTile(
                icon: Icons.fitness_center,
                label: 'Avant entraînement',
                text: plan.preWorkoutGuidance!,
                color: const Color(0xFF3B82F6),
              ),
            ],
            if (plan.postWorkoutGuidance != null) ...[
              const SizedBox(height: 6),
              _GuidanceTile(
                icon: Icons.sports_score,
                label: 'Après entraînement',
                text: plan.postWorkoutGuidance!,
                color: const Color(0xFF22C55E),
              ),
            ],
            if (plan.recoveryNutritionFocus.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                '🔄 Récupération : ${plan.recoveryNutritionFocus}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
            if (plan.supplementationFocus.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                '💊 Suppléments : ${plan.supplementationFocus.join(', ')}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _GuidanceTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String text;
  final Color color;
  const _GuidanceTile(
      {required this.icon,
      required this.label,
      required this.text,
      required this.color});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: theme.textTheme.labelSmall
                      ?.copyWith(color: color, fontWeight: FontWeight.w600)),
              Text(text, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context)
                  .colorScheme
                  .onSurface
                  .withOpacity(0.7),
            ),
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.restaurant_menu_outlined, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('Plan nutritionnel non disponible'),
          SizedBox(height: 8),
          Text(
            'Complétez votre profil pour obtenir des recommandations.',
            style: TextStyle(color: Colors.grey),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
