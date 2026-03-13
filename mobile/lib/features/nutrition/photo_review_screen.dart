/// Ecran Review Photo — confirmation analyse IA repas (LOT 6).
///
/// Consomme [photoAnalysisProvider]. Affiche les aliments detectes,
/// les macros estimees et le niveau de confiance.
/// Bouton "Enregistrer comme repas" -> POST nutritionEntries puis pop.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/nutrition.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'nutrition_notifier.dart';

class PhotoReviewScreen extends ConsumerWidget {
  const PhotoReviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(photoAnalysisProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Analyse photo'),
      body: () {
        if (state.isUploading) {
          return const _AnalyzingView();
        }
        if (state.error != null) {
          return _ErrorView(
            error: state.error!,
            onRetry: () => ref.read(photoAnalysisProvider.notifier).reset(),
          );
        }
        if (state.result == null) {
          return const _EmptyView();
        }
        final photo = state.result!;
        if (photo.isPending) {
          return const _AnalyzingView();
        }
        if (photo.isFailed) {
          return _ErrorView(
            error: 'Analyse echouee',
            onRetry: () => ref.read(photoAnalysisProvider.notifier).reset(),
          );
        }
        return _ReviewBody(photo: photo, ref: ref);
      }(),
    );
  }
}

class _AnalyzingView extends StatelessWidget {
  const _AnalyzingView();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: colors.info),
          const SizedBox(height: 20),
          Text(
            'Analyse en cours...',
            style: TextStyle(color: colors.text, fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            'L\'IA identifie votre repas',
            style: TextStyle(color: colors.textSecondary, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _ReviewBody extends StatelessWidget {
  final NutritionPhoto photo;
  final WidgetRef ref;

  const _ReviewBody({required this.photo, required this.ref});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        // Confiance globale
        if (photo.overallConfidence != null)
          _ConfidenceBar(confidence: photo.overallConfidence!),
        const SizedBox(height: 20),

        // Aliments detectes
        const _SectionTitle('Aliments identifies'),
        ...photo.identifiedFoods.map((f) => _DetectedFoodRow(food: f)),
        const SizedBox(height: 20),

        // Macros estimees
        const _SectionTitle('Estimation nutritionnelle'),
        _MacroRow('Calories', photo.estimatedCalories, 'kcal'),
        _MacroRow('Proteines', photo.estimatedProteinG, 'g'),
        _MacroRow('Glucides', photo.estimatedCarbsG, 'g'),
        _MacroRow('Lipides', photo.estimatedFatG, 'g'),
        const SizedBox(height: 32),

        // Bouton enregistrer
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => _saveAndPop(context, ref, photo),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF6B6B),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('Enregistrer comme repas',
                style: TextStyle(fontSize: 15)),
          ),
        ),
        const SizedBox(height: 12),
        TextButton(
          onPressed: () {
            ref.read(photoAnalysisProvider.notifier).reset();
            context.pop();
          },
          child: Text('Annuler',
              style: TextStyle(color: colors.textSecondary)),
        ),
      ],
    );
  }

  Future<void> _saveAndPop(
      BuildContext context, WidgetRef ref, NutritionPhoto photo) async {
    final mealType = photo.mealTypeGuess ?? 'lunch';
    final payload = {
      'meal_type': mealType,
      'meal_name': photo.identifiedFoods.isNotEmpty
          ? photo.identifiedFoods.first.name
          : 'Repas photo',
      if (photo.estimatedCalories != null)
        'calories': photo.estimatedCalories,
      if (photo.estimatedProteinG != null)
        'protein_g': photo.estimatedProteinG,
      if (photo.estimatedCarbsG != null) 'carbs_g': photo.estimatedCarbsG,
      if (photo.estimatedFatG != null) 'fat_g': photo.estimatedFatG,
      'data_quality': 'photo_ai',
      'logged_at': DateTime.now().toIso8601String(),
    };
    try {
      await ref.read(nutritionSummaryProvider.notifier).addEntry(payload);
      ref.read(photoAnalysisProvider.notifier).reset();
      if (context.mounted) {
        // Pop jusqu'a NutritionHome
        context
          ..pop()
          ..pop();
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: const Color(0xFFFF6B6B),
          ),
        );
      }
    }
  }
}

// -- Widgets -------------------------------------------------------------------

class _SectionTitle extends StatelessWidget {
  final String text;

  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          color: colors.textMuted,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double confidence;

  const _ConfidenceBar({required this.confidence});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final pct = (confidence * 100).toStringAsFixed(0);
    final color = confidence >= 0.7
        ? colors.accent
        : confidence >= 0.4
            ? const Color(0xFFFFB347)
            : colors.danger;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.auto_awesome_rounded, color: color, size: 18),
          const SizedBox(width: 10),
          Text(
            'Confiance IA',
            style: TextStyle(color: colors.text, fontSize: 13),
          ),
          const Spacer(),
          Text(
            '$pct%',
            style: TextStyle(
                color: color, fontSize: 15, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}

class _DetectedFoodRow extends StatelessWidget {
  final DetectedFood food;

  const _DetectedFoodRow({required this.food});

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
              food.name,
              style: TextStyle(color: colors.text, fontSize: 14),
            ),
          ),
          if (food.quantityG != null)
            Text(
              '${food.quantityG!.toStringAsFixed(0)}g',
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 12),
            ),
          const SizedBox(width: 8),
          if (food.caloriesEstimated != null)
            Text(
              '${food.caloriesEstimated!.toStringAsFixed(0)} kcal',
              style: const TextStyle(
                color: Color(0xFFFF6B6B),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
        ],
      ),
    );
  }
}

class _MacroRow extends StatelessWidget {
  final String label;
  final double? value;
  final String unit;

  const _MacroRow(this.label, this.value, this.unit);

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
          Text(label,
              style: TextStyle(
                  color: colors.textMuted, fontSize: 13)),
          const Spacer(),
          Text(
            value != null
                ? '${value!.toStringAsFixed(1)} $unit'
                : '— $unit',
            style: TextStyle(
              color: colors.text,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;

  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.broken_image_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(error,
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 14),
                textAlign: TextAlign.center),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: onRetry,
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.info,
                foregroundColor: Colors.white,
              ),
              child: const Text('Reessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.photo_camera_outlined,
              size: 48, color: colors.textMuted),
          const SizedBox(height: 12),
          Text(
            'Prenez une photo de votre repas',
            style: TextStyle(color: colors.textSecondary, fontSize: 14),
          ),
        ],
      ),
    );
  }
}
