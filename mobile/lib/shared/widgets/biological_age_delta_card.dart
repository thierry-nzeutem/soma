/// BiologicalAgeDeltaCard — Affichage grand format de l'âge biologique.
///
/// Montre l'âge chronologique, l'âge biologique et le delta en années.
library;

import 'package:flutter/material.dart';

class BiologicalAgeDeltaCard extends StatelessWidget {
  final int chronologicalAge;
  final double biologicalAge;
  final double delta; // bio - chrono (négatif = plus jeune)
  final String trendLabel;
  final double confidence;

  const BiologicalAgeDeltaCard({
    super.key,
    required this.chronologicalAge,
    required this.biologicalAge,
    required this.delta,
    required this.trendLabel,
    required this.confidence,
  });

  Color get _deltaColor {
    if (delta <= -3) return const Color(0xFF22C55E); // très bon
    if (delta <= 0) return const Color(0xFF84CC16); // bon
    if (delta <= 3) return const Color(0xFFF59E0B); // attention
    return const Color(0xFFEF4444); // mauvais
  }

  String get _deltaFormatted {
    if (delta == 0) return '= même âge';
    final sign = delta < 0 ? '−' : '+';
    return '$sign${delta.abs().toStringAsFixed(1)} ans';
  }

  String get _deltaDescription {
    if (delta <= -5) return 'Excellent ! Vous êtes biologiquement bien plus jeune.';
    if (delta <= -2) return 'Très bien. Votre hygiène de vie ralentit le vieillissement.';
    if (delta <= 0) return 'Bien. Vous êtes dans la moyenne de votre âge.';
    if (delta <= 3) return 'Attention. Quelques leviers à activer.';
    return 'À surveiller. Des améliorations sont possibles.';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                // Âge chronologique
                _AgeDisplay(
                  label: 'Âge réel',
                  age: chronologicalAge.toDouble(),
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                  isMain: false,
                ),
                // Delta
                Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: _deltaColor.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                        border:
                            Border.all(color: _deltaColor.withOpacity(0.4)),
                      ),
                      child: Text(
                        _deltaFormatted,
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: _deltaColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      trendLabel,
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.5),
                      ),
                    ),
                  ],
                ),
                // Âge biologique
                _AgeDisplay(
                  label: 'Âge biologique',
                  age: biologicalAge,
                  color: _deltaColor,
                  isMain: true,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _deltaDescription,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
            if (confidence < 0.6) ...[
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.info_outline,
                      size: 14,
                      color:
                          theme.colorScheme.onSurface.withOpacity(0.4)),
                  const SizedBox(width: 4),
                  Text(
                    'Confiance ${(confidence * 100).toStringAsFixed(0)}% — données incomplètes',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.4),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _AgeDisplay extends StatelessWidget {
  final String label;
  final double age;
  final Color color;
  final bool isMain;

  const _AgeDisplay({
    required this.label,
    required this.age,
    required this.color,
    required this.isMain,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Text(
          age.toStringAsFixed(isMain ? 1 : 0),
          style: (isMain
                  ? theme.textTheme.displaySmall
                  : theme.textTheme.headlineMedium)
              ?.copyWith(
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
      ],
    );
  }
}
