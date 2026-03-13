/// LongevityLeverCard — Levier d'amélioration de l'âge biologique.
///
/// Affiche un levier avec les années potentiellement gagnées,
/// la difficulté et le délai de mise en place.
library;

import 'package:flutter/material.dart';

import '../../core/models/biological_age.dart';

class LongevityLeverCard extends StatelessWidget {
  final BiologicalAgeLever lever;

  const LongevityLeverCard({super.key, required this.lever});

  Color get _difficultyColor {
    switch (lever.difficulty) {
      case 'easy':
        return const Color(0xFF22C55E);
      case 'moderate':
        return const Color(0xFFF59E0B);
      case 'hard':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF6B7280);
    }
  }

  IconData get _difficultyIcon {
    switch (lever.difficulty) {
      case 'easy':
        return Icons.sentiment_satisfied_alt;
      case 'moderate':
        return Icons.trending_up;
      case 'hard':
        return Icons.fitness_center;
      default:
        return Icons.help_outline;
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
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Badge années gagnées
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: const Color(0xFF22C55E).withOpacity(0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                    color: const Color(0xFF22C55E).withOpacity(0.3)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '−${lever.potentialYearsGained.toStringAsFixed(1)}',
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: const Color(0xFF22C55E),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'ans',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: const Color(0xFF22C55E),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    lever.title,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    lever.description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.7),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(_difficultyIcon,
                          size: 14, color: _difficultyColor),
                      const SizedBox(width: 4),
                      Text(
                        lever.difficultyLabel,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: _difficultyColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Icon(Icons.schedule,
                          size: 14,
                          color:
                              theme.colorScheme.onSurface.withOpacity(0.5)),
                      const SizedBox(width: 4),
                      Text(
                        lever.timeframeLabel,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color:
                              theme.colorScheme.onSurface.withOpacity(0.6),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
