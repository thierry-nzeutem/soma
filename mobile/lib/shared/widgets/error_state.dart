/// ErrorState — Widget générique pour les états d'erreur.
///
/// Gère les erreurs réseau, serveur et timeout.
/// Propose toujours un bouton "Réessayer".
library;

import 'package:flutter/material.dart';

import '../../core/theme/theme_extensions.dart';

class ErrorState extends StatelessWidget {
  const ErrorState({
    super.key,
    this.error,
    this.onRetry,
    this.title,
    this.subtitle,
  });

  /// Erreur capturée (optionnelle — affichée en mode debug).
  final Object? error;

  /// Callback du bouton "Réessayer".
  final VoidCallback? onRetry;

  /// Titre personnalisé (remplace le titre générique).
  final String? title;
  final String? subtitle;

  // ── Constructeurs nommés ───────────────────────────────────────────────────

  /// Erreur de chargement générique.
  factory ErrorState.loading({Object? error, VoidCallback? onRetry}) =>
      ErrorState(
        error: error,
        onRetry: onRetry,
        title: 'Impossible de charger les données',
        subtitle: 'Vérifiez votre connexion et réessayez.',
      );

  /// Erreur hors connexion avec données stale.
  factory ErrorState.offline({Object? error, VoidCallback? onRetry}) =>
      ErrorState(
        error: error,
        onRetry: onRetry,
        title: 'Hors connexion',
        subtitle: 'Les dernières données disponibles sont affichées.',
      );

  /// Erreur serveur (5xx).
  factory ErrorState.server({Object? error, VoidCallback? onRetry}) =>
      ErrorState(
        error: error,
        onRetry: onRetry,
        title: 'Erreur serveur',
        subtitle: 'SOMA rencontre un problème technique. Réessayez dans quelques instants.',
      );

  /// Timeout réseau.
  factory ErrorState.timeout({Object? onRetry, VoidCallback? onRetryCallback}) =>
      ErrorState(
        onRetry: onRetryCallback,
        title: 'Délai dépassé',
        subtitle: 'La requête a pris trop de temps. Vérifiez votre connexion.',
      );

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final errorText = _friendlyError(error);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline_rounded,
              size: 56,
              color: colors.danger,
            ),
            const SizedBox(height: 16),
            Text(
              title ?? 'Une erreur s\'est produite',
              style: TextStyle(
                color: colors.text.withOpacity(0.70),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 8),
              Text(
                subtitle!,
                style: TextStyle(
                  color: colors.text.withOpacity(0.38),
                  fontSize: 13,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            // Message d'erreur technique en mode debug uniquement.
            if (errorText != null && _isDebug) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  errorText,
                  style: TextStyle(
                    color: colors.danger,
                    fontSize: 11,
                    fontFamily: 'monospace',
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
            if (onRetry != null) ...[
              const SizedBox(height: 24),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Réessayer'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: colors.accent,
                  side: BorderSide(color: colors.accent),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  static bool get _isDebug {
    bool debug = false;
    assert(() {
      debug = true;
      return true;
    }());
    return debug;
  }

  static String? _friendlyError(Object? error) {
    if (error == null) return null;
    final msg = error.toString();
    if (msg.length > 120) return '${msg.substring(0, 120)}…';
    return msg;
  }
}

/// Widget inline compact pour les erreurs dans les cartes.
class InlineErrorWidget extends StatelessWidget {
  const InlineErrorWidget({
    super.key,
    this.message = 'Erreur de chargement',
    this.onRetry,
  });

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Icon(
            Icons.error_outline,
            size: 16,
            color: colors.danger,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: colors.danger,
                fontSize: 13,
              ),
            ),
          ),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              style: TextButton.styleFrom(
                foregroundColor: colors.accent,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                minimumSize: const Size(0, 32),
              ),
              child: const Text('Retry', style: TextStyle(fontSize: 12)),
            ),
        ],
      ),
    );
  }
}
