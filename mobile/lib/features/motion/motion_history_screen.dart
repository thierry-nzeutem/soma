/// MotionHistoryScreen — Historique Motion Intelligence SOMA LOT 11.
///
/// Liste les snapshots d'analyse du mouvement.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/movement_health_ring.dart';
import 'motion_notifier.dart';

class MotionHistoryScreen extends ConsumerWidget {
  const MotionHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(motionHistoryProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: colors.background,
        title: Text('Historique Mouvement', style: TextStyle(color: colors.text)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.textSecondary),
            onPressed: () =>
                ref.read(motionHistoryProvider.notifier).refresh(),
          ),
        ],
      ),
      body: historyAsync.when(
        loading: () => Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 48, color: colors.danger),
              const SizedBox(height: 12),
              Text('Impossible de charger l\'historique',
                  style: TextStyle(color: colors.text)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () =>
                    ref.read(motionHistoryProvider.notifier).refresh(),
                child: const Text('Reessayer'),
              ),
            ],
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.history, size: 64, color: colors.textMuted),
                  const SizedBox(height: 16),
                  Text('Aucun historique de mouvement',
                      style: TextStyle(color: colors.text)),
                ],
              ),
            );
          }

          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              return _MotionHistoryTile(item: item);
            },
          );
        },
      ),
    );
  }
}

class _MotionHistoryTile extends StatelessWidget {
  final item;
  const _MotionHistoryTile({required this.item});

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      const months = [
        '', 'jan', 'fev', 'mar', 'avr', 'mai', 'juin',
        'juil', 'aout', 'sep', 'oct', 'nov', 'dec'
      ];
      return '${date.day} ${months[date.month]}';
    } catch (_) {
      return dateStr;
    }
  }

  String get _trendIcon {
    switch (item.overallQualityTrend as String) {
      case 'improving':
        return '↑';
      case 'declining':
        return '↓';
      default:
        return '→';
    }
  }

  Color _trendColor(BuildContext context) {
    final colors = context.somaColors;
    switch (item.overallQualityTrend as String) {
      case 'improving':
        return colors.success;
      case 'declining':
        return colors.danger;
      default:
        return colors.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final trendCol = _trendColor(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            // Mini ring
            MovementHealthRing(
              score: item.movementHealthScore as double,
              size: 60,
              strokeWidth: 7,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _formatDate(item.snapshotDate as String),
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text('Stabilite ${(item.stabilityScore as double).toStringAsFixed(0)}',
                          style: theme.textTheme.labelSmall?.copyWith(
                              color: const Color(0xFF3B82F6))),
                      const Text(' · '),
                      Text('Mobilite ${(item.mobilityScore as double).toStringAsFixed(0)}',
                          style: theme.textTheme.labelSmall?.copyWith(
                              color: const Color(0xFF8B5CF6))),
                    ],
                  ),
                ],
              ),
            ),
            // Trend
            Text(
              _trendIcon,
              style: theme.textTheme.headlineSmall?.copyWith(
                color: trendCol,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
