/// SOMA LOT 17 — LongevityImpactCard widget.
///
/// Affiche l'impact du profil biomarqueurs sur l'âge biologique.
/// longevityModifier positif = années gagnées, négatif = années perdues.
library;

import 'package:flutter/material.dart';

import '../../core/theme/theme_extensions.dart';

class LongevityImpactCard extends StatelessWidget {
  /// Modificateur en années (plage attendue : -10 à +10).
  final double longevityModifier;

  /// Nombre de marqueurs analysés.
  final int markersAnalyzed;

  /// Nombre de marqueurs optimaux.
  final int optimalMarkers;

  const LongevityImpactCard({
    super.key,
    required this.longevityModifier,
    required this.markersAnalyzed,
    required this.optimalMarkers,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final isPositive = longevityModifier >= 0;
    final color = isPositive ? colors.success : colors.danger;
    final sign = isPositive ? '+' : '';
    final formatted = '$sign${longevityModifier.toStringAsFixed(1)} ans';

    final optimalPercent = markersAnalyzed > 0
        ? (optimalMarkers / markersAnalyzed * 100).toStringAsFixed(0)
        : '0';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(
                isPositive
                    ? Icons.trending_up_rounded
                    : Icons.trending_down_rounded,
                color: color,
                size: 32,
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    formatted,
                    style: TextStyle(
                      color: color,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    isPositive
                        ? 'sur votre âge biologique'
                        : 'sur votre âge biologique',
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 12),
                  ),
                ],
              ),
              const Spacer(),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '$optimalPercent%',
                    style: TextStyle(
                        color: colors.accent,
                        fontSize: 18,
                        fontWeight: FontWeight.bold),
                  ),
                  Text(
                    'marqueurs optimaux',
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 10),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          Divider(color: colors.border),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.science_rounded,
                  color: colors.textMuted, size: 14),
              const SizedBox(width: 4),
              Text(
                '$markersAnalyzed marqueur(s) analysé(s) · $optimalMarkers optimal(aux)',
                style: TextStyle(
                    color: colors.textMuted, fontSize: 11),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
