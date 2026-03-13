/// BiologicalAgeScreen — Âge biologique SOMA LOT 11.
///
/// Affiche le score d'âge biologique, le delta, les composantes et les leviers.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/biological_age.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/biological_age_delta_card.dart';
import '../../shared/widgets/longevity_lever_card.dart';
import 'biological_age_notifier.dart';

class BiologicalAgeScreen extends ConsumerWidget {
  const BiologicalAgeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bioAgeAsync = ref.watch(biologicalAgeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Âge Biologique'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () =>
                Navigator.pushNamed(context, '/biological-age/history'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(biologicalAgeProvider.notifier).refresh(),
          ),
        ],
      ),
      body: bioAgeAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              const Text('Impossible de calculer l\'âge biologique'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () =>
                    ref.read(biologicalAgeProvider.notifier).refresh(),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (result) {
          if (result == null) {
            return const _EmptyView();
          }
          return _BiologicalAgeBody(result: result);
        },
      ),
    );
  }
}

// ── Corps principal ───────────────────────────────────────────────────────────

class _BiologicalAgeBody extends StatelessWidget {
  final BiologicalAgeResult result;
  const _BiologicalAgeBody({required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    // Top 3 leviers (ceux avec le plus de gain potentiel)
    final topLevers = [...result.levers]
      ..sort((a, b) =>
          b.potentialYearsGained.compareTo(a.potentialYearsGained));
    final displayLevers = topLevers.take(3).toList();

    return ListView(
      children: [
        // Card delta principal
        BiologicalAgeDeltaCard(
          chronologicalAge: result.chronologicalAge,
          biologicalAge: result.biologicalAge,
          delta: result.biologicalAgeDelta,
          trendLabel: result.trendLabel,
          confidence: result.confidence,
        ),

        // Explication
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Text(
            result.explanation,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ),

        const SizedBox(height: 8),
        _SectionHeader(title: '🔬 Composantes biologiques'),

        // Composantes expandables
        ...result.components.map((c) => _ComponentTile(component: c)),

        if (displayLevers.isNotEmpty) ...[
          const SizedBox(height: 4),
          _SectionHeader(title: '🎯 Leviers d\'amélioration'),
          ...displayLevers.map((l) => LongevityLeverCard(lever: l)),
          if (result.levers.length > 3)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: OutlinedButton(
                onPressed: () =>
                    Navigator.pushNamed(context, '/biological-age/levers'),
                child: Text(
                    'Voir tous les leviers (${result.levers.length})'),
              ),
            ),
        ],
        const SizedBox(height: 8),

        // CTA Biomarqueurs — lien entre âge bio et biomarqueurs
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Builder(builder: (context) {
            final colors = context.somaColors;
            return GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/biomarkers'),
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: colors.info.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                      color: colors.info.withOpacity(0.25)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.biotech_rounded,
                        color: colors.info, size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Biomarqueurs',
                              style: TextStyle(
                                  color: colors.info,
                                  fontWeight: FontWeight.w600)),
                          Text('Améliorez votre âge biologique via vos analyses sanguines',
                              style: TextStyle(
                                  color: colors.textMuted, fontSize: 12)),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded,
                        color: colors.textMuted, size: 20),
                  ],
                ),
              ),
            );
          }),
        ),
        const SizedBox(height: 24),
      ],
    );
  }
}

// ── Composante tile ───────────────────────────────────────────────────────────

class _ComponentTile extends StatefulWidget {
  final BiologicalAgeComponent component;
  const _ComponentTile({required this.component});

  @override
  State<_ComponentTile> createState() => _ComponentTileState();
}

class _ComponentTileState extends State<_ComponentTile> {
  bool _expanded = false;

  Color get _scoreColor {
    final s = widget.component.score;
    if (s >= 80) return const Color(0xFF22C55E);
    if (s >= 65) return const Color(0xFF84CC16);
    if (s >= 45) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final comp = widget.component;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      comp.displayName,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  if (!comp.isAvailable)
                    Icon(Icons.lock_outline,
                        size: 16,
                        color: theme.colorScheme.onSurface.withOpacity(0.3))
                  else ...[
                    Text(
                      '${comp.score.toStringAsFixed(0)}/100',
                      style: theme.textTheme.labelMedium?.copyWith(
                        color: _scoreColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      comp.ageDeltaYears >= 0
                          ? '+${comp.ageDeltaYears.toStringAsFixed(1)} ans'
                          : '${comp.ageDeltaYears.toStringAsFixed(1)} ans',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: comp.ageDeltaYears <= 0
                            ? const Color(0xFF22C55E)
                            : const Color(0xFFEF4444),
                      ),
                    ),
                  ],
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    size: 20,
                    color: theme.colorScheme.onSurface.withOpacity(0.4),
                  ),
                ],
              ),
              if (comp.isAvailable) ...[
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: (comp.score / 100).clamp(0.0, 1.0),
                    backgroundColor:
                        theme.colorScheme.onSurface.withOpacity(0.08),
                    valueColor:
                        AlwaysStoppedAnimation<Color>(_scoreColor),
                    minHeight: 5,
                  ),
                ),
              ],
              if (_expanded && comp.explanation.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  comp.explanation,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
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
          Icon(Icons.cake_outlined, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('Données insuffisantes pour calculer l\'âge biologique'),
          SizedBox(height: 8),
          Text(
            'Complétez votre profil et vos données de santé.',
            style: TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }
}
