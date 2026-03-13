/// SOMA LOT 17 — ConfidenceBadge widget.
///
/// Badge compact affichant le niveau de confiance d'une analyse.
/// Tiers : >= 0.7 → élevée (vert), >= 0.4 → moyenne (jaune), < 0.4 → faible (gris).
library;

import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class ConfidenceBadge extends StatelessWidget {
  /// Score de confiance entre 0.0 et 1.0.
  final double confidence;

  const ConfidenceBadge({super.key, required this.confidence});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final (label, color) = _config(confidence, colors);
    final pct = '${(confidence * 100).toStringAsFixed(0)}%';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.verified_rounded, color: color, size: 12),
          const SizedBox(width: 4),
          Text(
            '$pct · $label',
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  static (String, Color) _config(double score, SomaColors colors) {
    if (score >= 0.7) {
      return ('Confiance élevée', colors.success);
    } else if (score >= 0.4) {
      return ('Confiance moyenne', const Color(0xFFFFCC00));
    } else {
      return ('Confiance faible', const Color(0xFF8E8E93));
    }
  }
}
