/// Ecran Hydratation — saisie rapide + historique du jour (LOT 6).
///
/// Boutons rapides +250 ml / +500 ml / +750 ml / +1000 ml.
/// Anneau de progression vers l'objectif journalier.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/hydration.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'hydration_notifier.dart';

class HydrationScreen extends ConsumerWidget {
  const HydrationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(hydrationProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Hydratation',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(hydrationProvider.notifier).refresh(),
            tooltip: 'Actualiser',
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.info),
        ),
        error: (err, _) => _ErrorView(
          message: err.toString(),
          onRetry: () => ref.read(hydrationProvider.notifier).refresh(),
        ),
        data: (summary) => RefreshIndicator(
          color: colors.info,
          backgroundColor: colors.surface,
          onRefresh: () => ref.read(hydrationProvider.notifier).refresh(),
          child: _HydrationBody(summary: summary, ref: ref),
        ),
      ),
    );
  }
}

class _HydrationBody extends StatelessWidget {
  final HydrationSummary summary;
  final WidgetRef ref;

  const _HydrationBody({required this.summary, required this.ref});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        // Anneau de progression
        Center(child: _ProgressRing(summary: summary)),
        const SizedBox(height: 32),

        // Boutons rapides
        Text(
          'Ajouter rapidement',
          style: TextStyle(
            color: colors.textMuted,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: 2.4,
          children: [
            _QuickAddButton(ml: 250, ref: ref),
            _QuickAddButton(ml: 500, ref: ref),
            _QuickAddButton(ml: 750, ref: ref),
            _QuickAddButton(ml: 1000, ref: ref),
          ],
        ),
        const SizedBox(height: 28),

        // Entrees du jour
        if (summary.entries.isNotEmpty) ...[
          Text(
            'Entrees du jour',
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          ...summary.entries.map((e) => _EntryRow(entry: e)),
        ],
      ],
    );
  }
}

class _ProgressRing extends StatelessWidget {
  final HydrationSummary summary;

  const _ProgressRing({required this.summary});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final progress = summary.progress.clamp(0.0, 1.0);
    final liters = (summary.totalMl / 1000).toStringAsFixed(1);
    final targetL = (summary.targetMl / 1000).toStringAsFixed(1);
    final color = progress >= 1.0
        ? colors.accent
        : colors.info;

    return SizedBox(
      width: 180,
      height: 180,
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 180,
            height: 180,
            child: CircularProgressIndicator(
              value: progress,
              strokeWidth: 12,
              backgroundColor: colors.border,
              valueColor: AlwaysStoppedAnimation<Color>(color),
              strokeCap: StrokeCap.round,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '$liters L',
                style: TextStyle(
                  color: colors.text,
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'objectif $targetL L',
                style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 13,
                ),
              ),
              if (summary.remainingMl > 0)
                Text(
                  '${(summary.remainingMl / 1000).toStringAsFixed(1)} L restants',
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _QuickAddButton extends StatelessWidget {
  final int ml;
  final WidgetRef ref;

  const _QuickAddButton({required this.ml, required this.ref});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Material(
      color: colors.info.withOpacity(0.12),
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: () => ref.read(hydrationProvider.notifier).addEntry(
              volumeMl: ml,
            ),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: colors.info.withOpacity(0.3)),
          ),
          child: Center(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.add, color: colors.info, size: 18),
                const SizedBox(width: 4),
                Text(
                  ml >= 1000 ? '${ml ~/ 1000} L' : '$ml ml',
                  style: TextStyle(
                    color: colors.info,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EntryRow extends StatelessWidget {
  final dynamic entry; // HydrationLog

  const _EntryRow({required this.entry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Text(
            entry.beverageEmoji,
            style: const TextStyle(fontSize: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              entry.beverageLabel,
              style: TextStyle(color: colors.text, fontSize: 14),
            ),
          ),
          Text(
            '${entry.volumeMl} ml',
            style: TextStyle(
              color: colors.info,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
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
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.water_drop_outlined,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Impossible de charger l\'hydratation',
              style: TextStyle(color: colors.text, fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.info,
                foregroundColor: Colors.black,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
