/// BiologicalAgeHistoryScreen — Historique de l'âge biologique SOMA LOT 11.
///
/// Liste les snapshots d'âge biologique avec visualisation de l'évolution.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'biological_age_notifier.dart';

class BiologicalAgeHistoryScreen extends ConsumerWidget {
  const BiologicalAgeHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(biologicalAgeHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Historique Âge Biologique'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () =>
                ref.read(biologicalAgeHistoryProvider.notifier).refresh(),
          ),
        ],
      ),
      body: historyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              const Text('Impossible de charger l\'historique'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () =>
                    ref.read(biologicalAgeHistoryProvider.notifier).refresh(),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.history, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('Aucun historique disponible'),
                ],
              ),
            );
          }

          return Column(
            children: [
              // Mini chart text summary
              Padding(
                padding: const EdgeInsets.all(16),
                child: _DeltaEvolutionSummary(items: items),
              ),
              // Liste
              Expanded(
                child: ListView.builder(
                  itemCount: items.length,
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return _BiologicalAgeHistoryTile(
                      snapshotDate: item.snapshotDate,
                      chronologicalAge: (item.biologicalAge - item.biologicalAgeDelta).round(),
                      biologicalAge: item.biologicalAge,
                      delta: item.biologicalAgeDelta,
                      trendDirection: item.trendDirection,
                      confidence: item.confidence,
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ── Résumé évolution ──────────────────────────────────────────────────────────

class _DeltaEvolutionSummary extends StatelessWidget {
  final List items;
  const _DeltaEvolutionSummary({required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (items.isEmpty) return const SizedBox.shrink();

    final first = items.last;
    final last = items.first;
    final trend = (last.biologicalAgeDelta - first.biologicalAgeDelta);

    Color trendColor = const Color(0xFF6B7280);
    String trendText = 'Stable';
    if (trend < -0.5) {
      trendColor = const Color(0xFF22C55E);
      trendText = '↓ En amélioration (${trend.toStringAsFixed(1)} ans)';
    } else if (trend > 0.5) {
      trendColor = const Color(0xFFEF4444);
      trendText = '↑ En dégradation (+${trend.toStringAsFixed(1)} ans)';
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: trendColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: trendColor.withOpacity(0.2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _StatItem(
            label: 'Plus ancien',
            value: first.biologicalAgeDelta >= 0
                ? '+${first.biologicalAgeDelta.toStringAsFixed(1)} ans'
                : '${first.biologicalAgeDelta.toStringAsFixed(1)} ans',
            color: theme.colorScheme.onSurface.withOpacity(0.6),
          ),
          Text('→', style: theme.textTheme.titleLarge),
          _StatItem(
            label: 'Récent',
            value: last.biologicalAgeDelta >= 0
                ? '+${last.biologicalAgeDelta.toStringAsFixed(1)} ans'
                : '${last.biologicalAgeDelta.toStringAsFixed(1)} ans',
            color: trendColor,
          ),
          _StatItem(
            label: 'Tendance',
            value: trendText,
            color: trendColor,
          ),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _StatItem(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Text(value,
            style: theme.textTheme.titleSmall
                ?.copyWith(color: color, fontWeight: FontWeight.bold)),
        Text(label,
            style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.5))),
      ],
    );
  }
}

// ── Tile historique ───────────────────────────────────────────────────────────

class _BiologicalAgeHistoryTile extends StatelessWidget {
  final String snapshotDate;
  final int chronologicalAge;
  final double biologicalAge;
  final double delta;
  final String trendDirection;
  final double confidence;

  const _BiologicalAgeHistoryTile({
    required this.snapshotDate,
    required this.chronologicalAge,
    required this.biologicalAge,
    required this.delta,
    required this.trendDirection,
    required this.confidence,
  });

  Color get _deltaColor {
    if (delta <= -2) return const Color(0xFF22C55E);
    if (delta <= 0) return const Color(0xFF84CC16);
    if (delta <= 3) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  String get _trendIcon {
    switch (trendDirection) {
      case 'improving':
        return '↓';
      case 'declining':
        return '↑';
      default:
        return '→';
    }
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      const months = [
        '', 'jan', 'fév', 'mar', 'avr', 'mai', 'juin',
        'juil', 'août', 'sep', 'oct', 'nov', 'déc'
      ];
      return '${date.day} ${months[date.month]} ${date.year}';
    } catch (_) {
      return dateStr;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final deltaStr = delta >= 0
        ? '+${delta.toStringAsFixed(1)}'
        : delta.toStringAsFixed(1);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            // Date
            SizedBox(
              width: 80,
              child: Text(
                _formatDate(snapshotDate),
                style: theme.textTheme.labelMedium,
              ),
            ),
            const SizedBox(width: 8),
            // Âge biologique
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Biologique : ${biologicalAge.toStringAsFixed(1)} ans',
                    style: theme.textTheme.bodyMedium,
                  ),
                  Text(
                    'Chronologique : $chronologicalAge ans',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.5),
                    ),
                  ),
                ],
              ),
            ),
            // Delta
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '$deltaStr ans',
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: _deltaColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  _trendIcon,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: trendDirection == 'improving'
                        ? const Color(0xFF22C55E)
                        : trendDirection == 'declining'
                            ? const Color(0xFFEF4444)
                            : theme.colorScheme.onSurface.withOpacity(0.4),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
