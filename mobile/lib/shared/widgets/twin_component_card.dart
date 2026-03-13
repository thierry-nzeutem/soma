/// TwinComponentCard — Widget pour afficher une composante du jumeau numérique.
///
/// Affiche la valeur, le statut, la barre de confiance et l'explication.
library;

import 'package:flutter/material.dart';

import '../../core/models/digital_twin.dart';

class TwinComponentCard extends StatelessWidget {
  final String title;
  final TwinComponent component;
  final bool expanded;

  const TwinComponentCard({
    super.key,
    required this.title,
    required this.component,
    this.expanded = false,
  });

  Color get _statusColor {
    switch (component.status) {
      case 'excellent':
      case 'high':
      case 'fresh':
        return const Color(0xFF22C55E); // vert
      case 'good':
      case 'normal':
        return const Color(0xFF84CC16); // vert clair
      case 'moderate':
      case 'low':
        return const Color(0xFFF59E0B); // orange
      case 'depleted':
      case 'tired':
      case 'high_risk':
        return const Color(0xFFF97316); // orange foncé
      case 'critical':
      case 'overloaded':
        return const Color(0xFFEF4444); // rouge
      default:
        return const Color(0xFF6B7280); // gris
    }
  }

  String get _statusLabel {
    switch (component.status) {
      case 'excellent':
        return 'Excellent';
      case 'high':
        return 'Élevé';
      case 'fresh':
        return 'Frais';
      case 'good':
        return 'Bon';
      case 'normal':
        return 'Normal';
      case 'moderate':
        return 'Modéré';
      case 'low':
        return 'Faible';
      case 'depleted':
        return 'Épuisé';
      case 'tired':
        return 'Fatigué';
      case 'high_risk':
        return 'Risque élevé';
      case 'critical':
        return 'Critique';
      case 'overloaded':
        return 'Surchargé';
      default:
        return component.status;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: _statusColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: _statusColor.withOpacity(0.4)),
                  ),
                  child: Text(
                    _statusLabel,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: _statusColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(
                  component.value.toStringAsFixed(
                      component.value.abs() < 10 ? 1 : 0),
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _statusColor,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Confiance',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurface.withOpacity(0.5),
                        ),
                      ),
                      const SizedBox(height: 2),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: component.confidence.clamp(0.0, 1.0),
                          backgroundColor:
                              theme.colorScheme.onSurface.withOpacity(0.1),
                          valueColor:
                              AlwaysStoppedAnimation<Color>(_statusColor),
                          minHeight: 6,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (component.explanation.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                component.explanation,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
            if (expanded && component.variablesUsed.isNotEmpty) ...[
              const SizedBox(height: 6),
              Wrap(
                spacing: 4,
                runSpacing: 4,
                children: component.variablesUsed
                    .map((v) => Chip(
                          label: Text(v),
                          labelStyle: theme.textTheme.labelSmall,
                          padding: EdgeInsets.zero,
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
