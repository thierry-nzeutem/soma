/// SOMA — Cardio Fitness Screen.
///
/// Affiche le VO2max, la categorie, le percentile, le groupe d'age,
/// les barres de reference et la suggestion d'amelioration.
/// Consomme cardioFitnessProvider.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/cardio_fitness.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'fitness_notifier.dart';

// ── Screen ────────────────────────────────────────────────────────────────────

class FitnessScreen extends ConsumerWidget {
  const FitnessScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(cardioFitnessProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Cardio Fitness',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.invalidate(cardioFitnessProvider),
          ),
        ],
      ),
      body: state.when(
        loading: () =>
            Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (err, _) => _FitnessError(
          message: err.toString(),
          onRetry: () => ref.invalidate(cardioFitnessProvider),
        ),
        data: (fitness) => _FitnessContent(fitness: fitness),
      ),
    );
  }
}

// ── Content ───────────────────────────────────────────────────────────────────

class _FitnessContent extends StatelessWidget {
  final CardioFitnessResponse? fitness;

  const _FitnessContent({required this.fitness});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    if (fitness == null) {
      return Center(
        child: Text(
          'Donn\u00e9es cardio non disponibles',
          style: TextStyle(color: colors.textMuted, fontSize: 16),
        ),
      );
    }

    final f = fitness!;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // VO2max hero card
        _Vo2maxHero(fitness: f),
        const SizedBox(height: 20),

        // Percentile + age group row
        Row(
          children: [
            Expanded(child: _InfoCard(
              label: 'Percentile',
              value: f.percentile != null
                  ? 'Meilleur que ${f.percentile!.toStringAsFixed(0)}%'
                  : '--',
              icon: Icons.leaderboard_outlined,
              color: colors.accent,
            )),
            const SizedBox(width: 10),
            Expanded(child: _InfoCard(
              label: 'Groupe d\u00e2ge',
              value: f.ageGroup ?? '--',
              icon: Icons.people_outline,
              color: colors.info,
            )),
          ],
        ),
        const SizedBox(height: 20),

        // Reference bars
        if (f.referenceBars.isNotEmpty) ...[
          _ReferenceBarsSection(bars: f.referenceBars, fitness: f),
          const SizedBox(height: 20),
        ],

        // Improvement suggestion
        if (f.improvementSuggestion != null &&
            f.improvementSuggestion!.isNotEmpty) ...[
          _SuggestionCard(suggestion: f.improvementSuggestion!),
          const SizedBox(height: 16),
        ],
      ],
    );
  }
}

// ── VO2max Hero ───────────────────────────────────────────────────────────────

class _Vo2maxHero extends StatelessWidget {
  final CardioFitnessResponse fitness;

  const _Vo2maxHero({required this.fitness});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final categoryColor = _categoryColor(fitness.categoryKey, colors);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        children: [
          // VO2max value
          Text(
            fitness.vo2max != null
                ? fitness.vo2max!.toStringAsFixed(1)
                : '--',
            style: TextStyle(
              color: colors.text,
              fontSize: 64,
              fontWeight: FontWeight.w800,
              height: 1,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'VO2max (mL/kg/min)',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
          const SizedBox(height: 16),
          // Category badge
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            decoration: BoxDecoration(
              color: categoryColor.withAlpha(30),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: categoryColor.withAlpha(100)),
            ),
            child: Text(
              fitness.category ?? 'Unknown',
              style: TextStyle(
                color: categoryColor,
                fontSize: 16,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.5,
              ),
            ),
          ),
          // Percentile bar
          if (fitness.percentile != null) ...[
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: (fitness.percentile! / 100).clamp(0.0, 1.0),
                backgroundColor: colors.border,
                valueColor:
                    AlwaysStoppedAnimation<Color>(categoryColor),
                minHeight: 8,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Meilleur que ${fitness.percentile!.toStringAsFixed(0)}% de votre groupe',
              style: TextStyle(
                color: colors.textMuted,
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }

  static Color _categoryColor(String key, dynamic colors) {
    switch (key) {
      case 'poor':
        return colors.danger as Color;
      case 'fair':
        return const Color(0xFFFFB347);
      case 'good':
        return const Color(0xFF34C759);
      case 'excellent':
        return const Color(0xFF9B72CF);
      default:
        return colors.textMuted as Color;
    }
  }
}

// ── Info Card ─────────────────────────────────────────────────────────────────

class _InfoCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _InfoCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withAlpha(30),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 11,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Reference Bars ────────────────────────────────────────────────────────────

class _ReferenceBarsSection extends StatelessWidget {
  final List<Map<String, dynamic>> bars;
  final CardioFitnessResponse fitness;

  const _ReferenceBarsSection({
    required this.bars,
    required this.fitness,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    // Find max value for normalization
    double maxVal = 1;
    for (final b in bars) {
      final v = (b['value'] as num?)?.toDouble() ?? 0;
      if (v > maxVal) maxVal = v;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'R\u00e9f\u00e9rence d\u00e9mographique',
          style: TextStyle(
            color: colors.text,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Plages VO2max par niveau de forme',
          style: TextStyle(color: colors.textMuted, fontSize: 12),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: colors.border),
          ),
          child: Column(
            children: bars.map((bar) {
              final label = bar['label'] as String? ??
                  bar['category'] as String? ??
                  '';
              final value =
                  (bar['value'] as num?)?.toDouble() ??
                  (bar['vo2max'] as num?)?.toDouble() ??
                  0.0;
              final ratio = (value / maxVal).clamp(0.0, 1.0);
              final isCurrentCategory =
                  label.toLowerCase().contains(
                        (fitness.category ?? '').toLowerCase(),
                      ) ||
                  (fitness.category ?? '')
                      .toLowerCase()
                      .contains(label.toLowerCase());

              final barColor = isCurrentCategory
                  ? colors.accent
                  : colors.textMuted;

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        SizedBox(
                          width: 90,
                          child: Text(
                            label,
                            style: TextStyle(
                              color: isCurrentCategory
                                  ? colors.text
                                  : colors.textSecondary,
                              fontSize: 13,
                              fontWeight: isCurrentCategory
                                  ? FontWeight.w600
                                  : FontWeight.w400,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Expanded(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: ratio,
                              backgroundColor:
                                  colors.border,
                              valueColor:
                                  AlwaysStoppedAnimation<Color>(
                                barColor,
                              ),
                              minHeight: 6,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          value.toStringAsFixed(0),
                          style: TextStyle(
                            color: isCurrentCategory
                                ? colors.accent
                                : colors.textMuted,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}

// ── Suggestion Card ───────────────────────────────────────────────────────────

class _SuggestionCard extends StatelessWidget {
  final String suggestion;

  const _SuggestionCard({required this.suggestion});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.accent.withAlpha(15),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.accent.withAlpha(60)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.lightbulb_outline,
            color: colors.accent,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Conseil d\u2019am\u00e9lioration',
                  style: TextStyle(
                    color: colors.accent,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  suggestion,
                  style: TextStyle(
                    color: colors.textSecondary,
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Error ─────────────────────────────────────────────────────────────────────

class _FitnessError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _FitnessError({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.directions_run, size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Donn\u00e9es cardio non disponibles',
              style: TextStyle(color: colors.text, fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('R\u00e9essayer'),
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
