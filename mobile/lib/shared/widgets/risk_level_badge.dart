/// SOMA LOT 17 — RiskLevelBadge widget.
///
/// Badge coloré pour afficher un niveau de risque coach platform.
/// Valeurs supportées : green | yellow | orange | red.
library;

import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class RiskLevelBadge extends StatelessWidget {
  final String riskLevel; // green | yellow | orange | red

  const RiskLevelBadge({super.key, required this.riskLevel});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final (label, color, icon) = _config(riskLevel, colors);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 12),
          const SizedBox(width: 4),
          Text(
            label,
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

  static (String, Color, IconData) _config(String level, SomaColors colors) => switch (level) {
        'green' => ('Vert', colors.success, Icons.circle),
        'yellow' => ('Jaune', const Color(0xFFFFCC00), Icons.circle),
        'orange' => ('Orange', colors.warning, Icons.warning_rounded),
        'red' => ('Rouge', colors.danger, Icons.error_rounded),
        _ => ('Inconnu', const Color(0xFF8E8E93), Icons.help_outline),
      };
}
