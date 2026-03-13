/// EmptyState — Widget générique pour les états vides.
///
/// Utilisé quand les données existent mais sont vides (liste vide,
/// pas encore de données saisies, etc.).
///
/// Différent de [ErrorState] qui gère les erreurs réseau/serveur.
library;

import 'package:flutter/material.dart';

import '../../core/theme/theme_extensions.dart';

class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.action,
    this.actionLabel,
  });

  final IconData icon;
  final String title;
  final String? subtitle;

  /// Callback du bouton d'action (optionnel).
  final VoidCallback? action;
  final String? actionLabel;

  // ── Constructeurs nommés (états courants SOMA) ─────────────────────────────

  /// Aucune donnée de nutrition pour aujourd'hui.
  factory EmptyState.noNutritionData({VoidCallback? onAdd}) => EmptyState(
        icon: Icons.restaurant_outlined,
        title: 'Aucun repas enregistré',
        subtitle: 'Ajoutez votre premier repas pour commencer le suivi nutritionnel.',
        action: onAdd,
        actionLabel: 'Ajouter un repas',
      );

  /// Aucun entraînement enregistré.
  factory EmptyState.noWorkouts({VoidCallback? onAdd}) => EmptyState(
        icon: Icons.fitness_center_outlined,
        title: 'Aucune séance enregistrée',
        subtitle: 'Créez votre première séance d\'entraînement.',
        action: onAdd,
        actionLabel: 'Nouvelle séance',
      );

  /// Aucune donnée de vision / analyse mouvement.
  factory EmptyState.noVisionData({VoidCallback? onStart}) => EmptyState(
        icon: Icons.videocam_outlined,
        title: 'Aucune analyse mouvement',
        subtitle: 'Commencez une session d\'analyse pour obtenir des insights sur votre forme.',
        action: onStart,
        actionLabel: 'Commencer une analyse',
      );

  /// Historique vide (graphiques, listes).
  factory EmptyState.noHistory() => const EmptyState(
        icon: Icons.history_outlined,
        title: 'Pas encore d\'historique',
        subtitle: 'Continuez à utiliser SOMA pour voir votre progression dans le temps.',
      );

  /// Aucun insight disponible.
  factory EmptyState.noInsights() => const EmptyState(
        icon: Icons.lightbulb_outline,
        title: 'Aucun insight pour le moment',
        subtitle: 'Les insights apparaîtront après quelques jours de suivi.',
      );

  /// Données insuffisantes pour l'analyse (moteurs IA).
  factory EmptyState.insufficientData() => const EmptyState(
        icon: Icons.analytics_outlined,
        title: 'Données insuffisantes',
        subtitle:
            'Continuez à enregistrer vos repas, entraînements et métriques '
            'pour débloquer les analyses avancées.',
      );

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 64,
              color: colors.text.withOpacity(0.24),
            ),
            const SizedBox(height: 16),
            Text(
              title,
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
            if (action != null && actionLabel != null) ...[
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: action,
                icon: const Icon(Icons.add),
                label: Text(actionLabel!),
                style: FilledButton.styleFrom(
                  backgroundColor: colors.accent,
                  foregroundColor: Colors.black,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
