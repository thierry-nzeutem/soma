/// Widget AlertBanner — bannière d'alerte dismissible pleine largeur.
///
/// Affiche une alerte colorée selon sa sévérité :
///   - critical → rouge (danger)
///   - warning  → orange (warning)
///   - info     → bleu (info)
///
/// Dismissible via [onDismiss] (affiche bouton X si fourni).
library;

import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class AlertBanner extends StatelessWidget {
  /// Message de l'alerte.
  final String message;

  /// Sévérité : 'critical' | 'warning' | 'info'.
  final String severity;

  /// Callback pour fermer la bannière (null = non dismissible).
  final VoidCallback? onDismiss;

  /// Callback pour l'action principale (ex: "Voir").
  final String? actionLabel;
  final VoidCallback? onAction;

  const AlertBanner({
    super.key,
    required this.message,
    this.severity = 'info',
    this.onDismiss,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = _severityColor(severity, colors);
    final icon = _severityIcon(severity);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withAlpha(80), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Icône sévérité
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 8),

            // Message
            Expanded(
              child: Text(
                message,
                style: TextStyle(
                  color: color,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  height: 1.4,
                ),
              ),
            ),

            // Bouton action (optionnel)
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onAction,
                child: Text(
                  actionLabel!,
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ],

            // Bouton dismiss (optionnel)
            if (onDismiss != null) ...[
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onDismiss,
                child: Icon(
                  Icons.close_rounded,
                  color: color.withAlpha(180),
                  size: 16,
                ),
              ),
            ],
          ],
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
        return Icons.warning_amber_rounded;
      case 'info':
      default:
        return Icons.info_rounded;
    }
  }
}

/// Version animée avec animation de disparition.
class DismissibleAlertBanner extends StatefulWidget {
  final String message;
  final String severity;
  final String? actionLabel;
  final VoidCallback? onAction;

  const DismissibleAlertBanner({
    super.key,
    required this.message,
    this.severity = 'info',
    this.actionLabel,
    this.onAction,
  });

  @override
  State<DismissibleAlertBanner> createState() => _DismissibleAlertBannerState();
}

class _DismissibleAlertBannerState extends State<DismissibleAlertBanner>
    with SingleTickerProviderStateMixin {
  bool _dismissed = false;
  late final AnimationController _controller;
  late final Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 250),
    );
    _opacity = Tween<double>(begin: 1.0, end: 0.0).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _dismiss() {
    _controller.forward().then((_) {
      if (mounted) setState(() => _dismissed = true);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_dismissed) return const SizedBox.shrink();

    return FadeTransition(
      opacity: _opacity,
      child: AlertBanner(
        message: widget.message,
        severity: widget.severity,
        onDismiss: _dismiss,
        actionLabel: widget.actionLabel,
        onAction: widget.onAction,
      ),
    );
  }
}
