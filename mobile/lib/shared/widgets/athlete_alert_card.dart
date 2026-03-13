/// SOMA LOT 17 — AthleteAlertCard widget.
///
/// Carte alerte athlète avec sévérité visuelle (couleur + icône).
library;

import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class AthleteAlertCard extends StatelessWidget {
  /// Nom de l'athlète ou type d'alerte affiché en en-tête.
  final String athleteName;

  /// Niveau de sévérité : critical | warning | info.
  final String severity;

  /// Message descriptif de l'alerte.
  final String message;

  /// Callback optionnel lors d'un tap sur la carte.
  final VoidCallback? onTap;

  const AthleteAlertCard({
    super.key,
    required this.athleteName,
    required this.severity,
    required this.message,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final (color, icon, label) = _severityConfig(severity, colors);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border(left: BorderSide(color: color, width: 3)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          athleteName,
                          style: TextStyle(
                              color: colors.text,
                              fontWeight: FontWeight.w600,
                              fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(label,
                            style: TextStyle(
                                color: color,
                                fontSize: 10,
                                fontWeight: FontWeight.w600)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    message,
                    style: TextStyle(
                        color: colors.textSecondary, fontSize: 12),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            if (onTap != null)
              Icon(Icons.chevron_right_rounded,
                  color: colors.textMuted, size: 20),
          ],
        ),
      ),
    );
  }

  static (Color, IconData, String) _severityConfig(String severity, SomaColors colors) =>
      switch (severity) {
        'critical' => (
            colors.danger,
            Icons.error_rounded,
            'Critique',
          ),
        'warning' => (
            colors.warning,
            Icons.warning_amber_rounded,
            'Avert.',
          ),
        'info' => (
            colors.success,
            Icons.info_outline_rounded,
            'Info',
          ),
        _ => (
            const Color(0xFF8E8E93),
            Icons.circle_outlined,
            severity,
          ),
      };
}
