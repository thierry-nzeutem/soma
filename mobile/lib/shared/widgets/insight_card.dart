/// Widget InsightCard — carte d'insight avec sévérité et catégorie.
///
/// Affiche un message d'insight avec :
///   - Icône de sévérité (info, warning, critical)
///   - Message principal
///   - Chip de catégorie
///   - Bordure gauche colorée par sévérité
/// Optionnellement tappable via [onTap].
library;

import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

/// Sévérité d'un insight.
enum InsightSeverity { info, warning, critical }

class InsightCard extends StatelessWidget {
  /// Message de l'insight.
  final String message;

  /// Sévérité : 'info' | 'warning' | 'critical'.
  final String severity;

  /// Catégorie (ex: 'nutrition', 'recovery', 'training').
  final String? category;

  /// Callback optionnel lors du tap.
  final VoidCallback? onTap;

  const InsightCard({
    super.key,
    required this.message,
    this.severity = 'info',
    this.category,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = _severityColor(severity, colors);
    final icon = _severityIcon(severity);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: colors.surfaceVariant,
          borderRadius: BorderRadius.circular(12),
          border: Border(
            left: BorderSide(color: color, width: 3),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Icône sévérité
              Padding(
                padding: const EdgeInsets.only(top: 1, right: 10),
                child: Icon(icon, color: color, size: 18),
              ),

              // Contenu principal
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      message,
                      style: TextStyle(
                        color: colors.text,
                        fontSize: 13,
                        fontWeight: FontWeight.w400,
                        height: 1.4,
                      ),
                    ),
                    if (category != null) ...[
                      const SizedBox(height: 6),
                      _CategoryChip(label: category!, color: color),
                    ],
                  ],
                ),
              ),

              // Flèche si tappable
              if (onTap != null)
                Padding(
                  padding: const EdgeInsets.only(left: 6, top: 1),
                  child: Icon(Icons.chevron_right, color: colors.textMuted, size: 18),
                ),
            ],
          ),
        ),
      ),
    );
  }

  static Color _severityColor(String severity, SomaColors colors) {
    switch (severity) {
      case 'critical':
        return colors.danger;
      case 'warning':
        return colors.warning;
      case 'info':
      default:
        return const Color(0xFF0A84FF);
    }
  }

  static IconData _severityIcon(String severity) {
    switch (severity) {
      case 'critical':
        return Icons.error_rounded;
      case 'warning':
        return Icons.warning_rounded;
      case 'info':
      default:
        return Icons.info_rounded;
    }
  }
}

class _CategoryChip extends StatelessWidget {
  final String label;
  final Color color;

  const _CategoryChip({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(80), width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
