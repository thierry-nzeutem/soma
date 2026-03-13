/// TwinHistoryScreen — Historique du jumeau numérique SOMA LOT 11.
///
/// Liste les snapshots du jumeau avec date et statut global.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/theme_extensions.dart';
import 'twin_notifier.dart';

class TwinHistoryScreen extends ConsumerWidget {
  const TwinHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(twinHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Historique Jumeau'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(twinHistoryProvider.notifier).refresh(),
          ),
        ],
      ),
      body: historyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 48, color: context.somaColors.danger),
              const SizedBox(height: 12),
              const Text('Impossible de charger l\'historique'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () =>
                    ref.read(twinHistoryProvider.notifier).refresh(),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (history) {
          final items = history.snapshots;
          if (items.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.history, size: 64, color: context.somaColors.textMuted),
                  SizedBox(height: 16),
                  Text('Aucun historique disponible'),
                ],
              ),
            );
          }

          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              return _TwinHistoryTile(
                snapshotDate: item.snapshotDate,
                overallStatus: item.overallStatus,
                globalConfidence: item.globalConfidence,
                trainingReadiness: item.trainingReadiness,
                fatigue: item.fatigue,
                
              );
            },
          );
        },
      ),
    );
  }
}

class _TwinHistoryTile extends StatelessWidget {
  final String snapshotDate;
  final String overallStatus;
  final double globalConfidence;
  final double trainingReadiness;
  final double fatigue;

  const _TwinHistoryTile({
    required this.snapshotDate,
    required this.overallStatus,
    required this.globalConfidence,
    required this.trainingReadiness,
    required this.fatigue,
  });

  Color get _statusColor {
    switch (overallStatus) {
      case 'fresh':
        return const Color(0xFF22C55E);
      case 'good':
        return const Color(0xFF84CC16);
      case 'moderate':
        return const Color(0xFFF59E0B);
      case 'tired':
        return const Color(0xFFF97316);
      case 'critical':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF6B7280);
    }
  }

  String get _statusLabel {
    switch (overallStatus) {
      case 'fresh':
        return 'Frais';
      case 'good':
        return 'Bon';
      case 'moderate':
        return 'Modéré';
      case 'tired':
        return 'Fatigué';
      case 'critical':
        return 'Critique';
      default:
        return overallStatus;
    }
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      const months = [
        '', 'jan', 'fév', 'mar', 'avr', 'mai', 'juin',
        'juil', 'août', 'sep', 'oct', 'nov', 'déc'
      ];
      return '${date.day} ${months[date.month]}';
    } catch (_) {
      return dateStr;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            // Indicateur statut
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _statusColor,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 12),
            // Date
            SizedBox(
              width: 50,
              child: Text(
                _formatDate(snapshotDate),
                style: theme.textTheme.labelMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 8),
            // Statut
            Expanded(
              child: Text(
                _statusLabel,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: _statusColor,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            // Readiness
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  'Readiness ${trainingReadiness.toStringAsFixed(0)}',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
                Text(
                  'Fatigue ${fatigue.toStringAsFixed(0)}',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
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
