/// AdaptiveMacroCard — Card pour une cible macro-nutritionnelle adaptative.
///
/// Affiche la valeur, l'unité, le rationnel et la priorité avec code couleur.
library;

import 'package:flutter/material.dart';

import '../../core/models/adaptive_nutrition.dart';

class AdaptiveMacroCard extends StatelessWidget {
  final String macroName;
  final String emoji;
  final NutritionTarget target;

  const AdaptiveMacroCard({
    super.key,
    required this.macroName,
    required this.emoji,
    required this.target,
  });

  Color get _priorityColor {
    switch (target.priority) {
      case 'critical':
        return const Color(0xFFEF4444);
      case 'high':
        return const Color(0xFFF97316);
      case 'normal':
        return const Color(0xFF3B82F6);
      case 'low':
        return const Color(0xFF6B7280);
      default:
        return const Color(0xFF6B7280);
    }
  }

  String get _priorityLabel {
    switch (target.priority) {
      case 'critical':
        return 'Critique';
      case 'high':
        return 'Priorité haute';
      case 'normal':
        return 'Normal';
      case 'low':
        return 'Secondaire';
      default:
        return target.priority;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(emoji, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    macroName,
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: _priorityColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _priorityLabel,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: _priorityColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            RichText(
              text: TextSpan(
                children: [
                  TextSpan(
                    text: target.value.toStringAsFixed(
                        target.value >= 100 ? 0 : 1),
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  TextSpan(
                    text: ' ${target.unit}',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
            if (target.rationale.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                target.rationale,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
