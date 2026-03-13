/// Ecran Nutrition Home — resume journalier + liste repas + FAB (LOT 6).
///
/// Affiche les macros du jour via [nutritionSummaryProvider].
/// FAB -> NutritionEntryFormScreen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/nutrition.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'nutrition_notifier.dart';

class NutritionHomeScreen extends ConsumerWidget {
  const NutritionHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(nutritionSummaryProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Nutrition',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () =>
                ref.read(nutritionSummaryProvider.notifier).refresh(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFFFF6B6B),
        child: const Icon(Icons.add, color: Colors.white),
        onPressed: () => context.push('/journal/nutrition/add'),
      ),
      body: state.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: Color(0xFFFF6B6B)),
        ),
        error: (err, _) => _ErrorView(
          message: err.toString(),
          onRetry: () =>
              ref.read(nutritionSummaryProvider.notifier).refresh(),
        ),
        data: (summary) => RefreshIndicator(
          color: const Color(0xFFFF6B6B),
          backgroundColor: colors.surface,
          onRefresh: () =>
              ref.read(nutritionSummaryProvider.notifier).refresh(),
          child: _NutritionBody(summary: summary, ref: ref),
        ),
      ),
    );
  }
}

class _NutritionBody extends StatelessWidget {
  final DailyNutritionSummary summary;
  final WidgetRef ref;

  const _NutritionBody({required this.summary, required this.ref});

  @override
  Widget build(BuildContext context) {
    final byMeal = <String, List<NutritionEntry>>{};
    for (final e in summary.meals) {
      byMeal.putIfAbsent(e.mealType, () => []).add(e);
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
      children: [
        // -- Resume macros --
        _MacroSummaryCard(summary: summary),
        const SizedBox(height: 20),

        // -- Repas par type --
        if (summary.meals.isEmpty)
          const _EmptyMeals()
        else
          ...byMeal.entries.map((entry) => _MealGroup(
                mealType: entry.key,
                entries: entry.value,
                ref: ref,
              )),
      ],
    );
  }
}

// -- Card macros ---------------------------------------------------------------

class _MacroSummaryCard extends StatelessWidget {
  final DailyNutritionSummary summary;

  const _MacroSummaryCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.local_fire_department_rounded,
                  color: Color(0xFFFF6B6B), size: 18),
              const SizedBox(width: 8),
              Text(
                '${summary.totals.calories.toStringAsFixed(0)} kcal',
                style: TextStyle(
                  color: colors.text,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (summary.goals.caloriesTarget != null) ...[
                const SizedBox(width: 8),
                Text(
                  '/ ${summary.goals.caloriesTarget!.toStringAsFixed(0)}',
                  style: TextStyle(
                    color: colors.textSecondary,
                    fontSize: 14,
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 12),
          // Barre progression calories
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: summary.caloriePct / 100,
              backgroundColor: const Color(0xFF2A2A2A),
              valueColor: AlwaysStoppedAnimation<Color>(
                summary.caloriePct >= 100
                    ? const Color(0xFFFF6B6B)
                    : colors.accent,
              ),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 16),
          // Macros row
          Row(
            children: [
              _MacroChip(
                label: 'Proteines',
                value: '${summary.totals.proteinG.toStringAsFixed(0)}g',
                color: const Color(0xFFFFB347),
                pct: summary.proteinPct,
              ),
              const SizedBox(width: 10),
              _MacroChip(
                label: 'Glucides',
                value: '${summary.totals.carbsG.toStringAsFixed(0)}g',
                color: colors.info,
              ),
              const SizedBox(width: 10),
              _MacroChip(
                label: 'Lipides',
                value: '${summary.totals.fatG.toStringAsFixed(0)}g',
                color: const Color(0xFF9B72CF),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MacroChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final double? pct;

  const _MacroChip({
    required this.label,
    required this.value,
    required this.color,
    this.pct,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(color: color.withOpacity(0.8), fontSize: 11),
            ),
            const SizedBox(height: 2),
            Text(
              value,
              style: TextStyle(
                  color: color, fontSize: 14, fontWeight: FontWeight.bold),
            ),
            if (pct != null)
              Text(
                '${pct!.toStringAsFixed(0)}%',
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 10),
              ),
          ],
        ),
      ),
    );
  }
}

// -- Groupe repas --------------------------------------------------------------

class _MealGroup extends StatelessWidget {
  final String mealType;
  final List<NutritionEntry> entries;
  final WidgetRef ref;

  const _MealGroup({
    required this.mealType,
    required this.entries,
    required this.ref,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final total = entries.fold<double>(0, (s, e) => s + (e.calories ?? 0));
    final label = entries.first.mealTypeLabel;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              Text(
                label,
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.5,
                ),
              ),
              const Spacer(),
              Text(
                '${total.toStringAsFixed(0)} kcal',
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        ...entries.map((e) => _EntryRow(entry: e, ref: ref)),
        const SizedBox(height: 16),
      ],
    );
  }
}

class _EntryRow extends StatelessWidget {
  final NutritionEntry entry;
  final WidgetRef ref;

  const _EntryRow({required this.entry, required this.ref});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              entry.mealName ?? entry.foodItemName ?? 'Repas',
              style: TextStyle(color: colors.text, fontSize: 14),
            ),
          ),
          if (entry.calories != null)
            Text(
              '${entry.calories!.toStringAsFixed(0)} kcal',
              style: const TextStyle(
                color: Color(0xFFFF6B6B),
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => _confirmDelete(context, ref, entry.id),
            child: Icon(Icons.close_rounded,
                color: colors.textMuted, size: 18),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmDelete(
      BuildContext context, WidgetRef ref, String id) async {
    final colors = context.somaColors;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: colors.surface,
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text('Supprimer ?',
            style: TextStyle(color: colors.text, fontSize: 16)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text('Annuler',
                style: TextStyle(color: colors.textSecondary)),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text('Supprimer',
                style: TextStyle(color: colors.danger)),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await ref.read(nutritionSummaryProvider.notifier).deleteEntry(id);
    }
  }
}

class _EmptyMeals extends StatelessWidget {
  const _EmptyMeals();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 48),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.restaurant_outlined,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Aucun repas enregistre',
              style: TextStyle(color: colors.textSecondary, fontSize: 14),
            ),
            const SizedBox(height: 6),
            Text(
              'Utilisez le + pour ajouter un repas',
              style: TextStyle(color: colors.textMuted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.cloud_off_rounded,
              size: 48, color: colors.textMuted),
          const SizedBox(height: 16),
          Text('Erreur de chargement',
              style: TextStyle(color: colors.text, fontSize: 16)),
          const SizedBox(height: 8),
          Text(message,
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
              maxLines: 3),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Reessayer'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF6B6B),
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}
