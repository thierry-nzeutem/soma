/// GlycogenGauge — Gauge horizontale pour afficher le niveau de glycogène.
///
/// Visualise le glycogène estimé (0-400g) avec zones colorées.
library;

import 'package:flutter/material.dart';

class GlycogenGauge extends StatelessWidget {
  /// Valeur en grammes (0-400g).
  final double value;
  final double maxValue;
  final bool showLabel;

  const GlycogenGauge({
    super.key,
    required this.value,
    this.maxValue = 400,
    this.showLabel = true,
  });

  double get _progress => (value / maxValue).clamp(0.0, 1.0);

  Color get _color {
    if (_progress < 0.20) return const Color(0xFFEF4444); // rouge — épuisé
    if (_progress < 0.40) return const Color(0xFFF97316); // orange — faible
    if (_progress < 0.70) return const Color(0xFFF59E0B); // jaune — modéré
    return const Color(0xFF22C55E); // vert — bon/élevé
  }

  String get _label {
    if (_progress < 0.20) return 'Épuisé';
    if (_progress < 0.40) return 'Faible';
    if (_progress < 0.70) return 'Modéré';
    return 'Bon';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showLabel) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Glycogène',
                style: theme.textTheme.labelMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                '${value.toStringAsFixed(0)}g / ${maxValue.toStringAsFixed(0)}g — $_label',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: _color,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
        ],
        Stack(
          children: [
            // Fond de la barre
            Container(
              height: 12,
              decoration: BoxDecoration(
                color: theme.colorScheme.onSurface.withOpacity(0.08),
                borderRadius: BorderRadius.circular(6),
              ),
            ),
            // Barre remplie
            FractionallySizedBox(
              widthFactor: _progress,
              child: Container(
                height: 12,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [_color.withOpacity(0.7), _color],
                  ),
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
            ),
            // Marqueurs de zone (20%, 40%, 70%)
            for (final pct in [0.20, 0.40, 0.70])
              Positioned(
                left: 0,
                right: 0,
                top: 0,
                bottom: 0,
                child: FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: pct,
                  child: Align(
                    alignment: Alignment.centerRight,
                    child: Container(
                      width: 1,
                      height: 12,
                      color:
                          theme.colorScheme.onSurface.withOpacity(0.25),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}
