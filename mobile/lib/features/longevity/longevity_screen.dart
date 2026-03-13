/// Ecran Score Longevite — composantes et age biologique SOMA.
///
/// Consomme GET /api/v1/scores/longevity via [longevityProvider].
/// Affiche : score global (ScoreRing), 7 composantes, age biologique,
///           leviers d'amelioration.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/longevity.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/score_ring.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'longevity_notifier.dart';

class LongevityScreen extends ConsumerWidget {
  const LongevityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(longevityProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Score Longevite',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(longevityProvider.notifier).refresh(),
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => _LongevityError(
          message: err.toString(),
          onRetry: () => ref.read(longevityProvider.notifier).refresh(),
        ),
        data: (score) => RefreshIndicator(
          color: colors.accent,
          backgroundColor: colors.surface,
          onRefresh: () => ref.read(longevityProvider.notifier).refresh(),
          child: _LongevityContent(score: score),
        ),
      ),
    );
  }
}

// -- Contenu principal ---------------------------------------------------------

class _LongevityContent extends StatelessWidget {
  final LongevityScore score;

  const _LongevityContent({required this.score});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final bioAge = score.biologicalAgeEstimate;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Score global (anneau centre)
        Center(
          child: ScoreRing(
            score: score.longevityScore,
            size: 180,
            strokeWidth: 14,
            label: 'Longevite',
            sublabel:
                bioAge != null ? 'Age bio : ${bioAge.toStringAsFixed(0)} ans' : null,
          ),
        ),
        const SizedBox(height: 8),
        // Confiance
        Center(
          child: Text(
            'Confiance : ${(score.confidence * 100).toStringAsFixed(0)}%',
            style: TextStyle(color: colors.textMuted, fontSize: 12),
          ),
        ),
        const SizedBox(height: 24),

        // 7 composantes
        _ComponentsSection(score: score),
        const SizedBox(height: 24),

        // Leviers d'amelioration
        if (score.topImprovementLevers.isNotEmpty) ...[
          _LeversSection(levers: score.topImprovementLevers),
          const SizedBox(height: 24),
        ],

        // Date de calcul
        Center(
          child: Text(
            'Calcule le ${score.scoreDate}',
            style: TextStyle(color: colors.textMuted, fontSize: 11),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}

// -- Section composantes -------------------------------------------------------

class _ComponentsSection extends StatelessWidget {
  final LongevityScore score;

  const _ComponentsSection({required this.score});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Composantes',
          style: TextStyle(
            color: colors.text,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        ...score.components.map(
          (c) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _ComponentBar(
              label: c.label,
              score: c.score,
            ),
          ),
        ),
      ],
    );
  }
}

class _ComponentBar extends StatelessWidget {
  final String label;
  final double? score;

  const _ComponentBar({required this.label, this.score});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final s = score ?? 0;
    final color = _barColor(s, colors);
    final hasData = score != null;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(color: colors.textSecondary, fontSize: 13),
                ),
              ),
              Text(
                hasData ? s.toStringAsFixed(0) : '—',
                style: TextStyle(
                  color: hasData ? color : colors.textMuted,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                ' / 100',
                style: TextStyle(color: colors.textMuted, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: hasData ? (s / 100).clamp(0.0, 1.0) : 0,
              backgroundColor: const Color(0xFF2A2A2A),
              valueColor: AlwaysStoppedAnimation<Color>(
                hasData ? color : colors.textMuted,
              ),
              minHeight: 5,
            ),
          ),
        ],
      ),
    );
  }

  static Color _barColor(double score, dynamic colors) {
    if (score >= 75) return colors.accent;
    if (score >= 50) return const Color(0xFFFFB347);
    return colors.danger;
  }
}

// -- Section leviers d'amelioration -------------------------------------------

class _LeversSection extends StatelessWidget {
  final List<ImprovementLever> levers;

  const _LeversSection({required this.levers});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Leviers d\'Amelioration',
          style: TextStyle(
            color: colors.text,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Composantes avec score < 70, triees par priorite',
          style: TextStyle(color: colors.textMuted, fontSize: 12),
        ),
        const SizedBox(height: 12),
        ...levers.asMap().entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _LeverCard(
                  rank: entry.key + 1,
                  lever: entry.value,
                ),
              ),
            ),
      ],
    );
  }
}

class _LeverCard extends StatelessWidget {
  final int rank;
  final ImprovementLever lever;

  const _LeverCard({required this.rank, required this.lever});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final priorityColor = _priorityColor(lever.priority, colors);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Rang
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: priorityColor.withAlpha(38),
              border: Border.all(color: priorityColor.withAlpha(100)),
            ),
            child: Center(
              child: Text(
                '$rank',
                style: TextStyle(
                  color: priorityColor,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      lever.component,
                      style: TextStyle(
                        color: colors.text,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '${lever.score.toStringAsFixed(0)}/100',
                      style: TextStyle(
                        color: priorityColor,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  lever.suggestion,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 13,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 6),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: priorityColor.withAlpha(25),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    lever.priority.toUpperCase(),
                    style: TextStyle(
                      color: priorityColor,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static Color _priorityColor(String priority, dynamic colors) {
    switch (priority.toLowerCase()) {
      case 'high':
        return colors.danger;
      case 'medium':
        return const Color(0xFFFFB347);
      default:
        return colors.accent;
    }
  }
}

// -- Erreur --------------------------------------------------------------------

class _LongevityError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _LongevityError({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.timeline_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text('Score de longevite indisponible',
                style: TextStyle(color: colors.text, fontSize: 16),
                textAlign: TextAlign.center),
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
