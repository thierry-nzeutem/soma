/// Widget CoachTipCard — carte conseil du coach SOMA.
///
/// Affiche un conseil du coach IA avec :
///   - Avatar SOMA (icône robot)
///   - Label "SOMA Coach"
///   - Texte du conseil
///   - Bouton CTA optionnel (ex: "Voir le détail")
/// Design iOS-style sombre, compatible avec la palette SOMA.
library;

import 'package:flutter/material.dart';

import '../../core/theme/theme_extensions.dart';

class CoachTipCard extends StatelessWidget {
  /// Conseil du coach à afficher.
  final String tip;

  /// Label du bouton CTA (null = pas de bouton).
  final String? ctaLabel;

  /// Callback lors du tap sur le CTA.
  final VoidCallback? onCta;

  const CoachTipCard({
    super.key,
    required this.tip,
    this.ctaLabel,
    this.onCta,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF30D158).withAlpha(80),
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // En-tête : avatar + label
            Row(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: const Color(0xFF30D158).withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.smart_toy_outlined,
                    color: Color(0xFF30D158),
                    size: 18,
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  'SOMA Coach',
                  style: TextStyle(
                    color: Color(0xFF30D158),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 10),

            // Texte du conseil
            Text(
              tip,
              style: TextStyle(
                color: colors.text,
                fontSize: 14,
                fontWeight: FontWeight.w400,
                height: 1.5,
              ),
            ),

            // Bouton CTA (optionnel)
            if (ctaLabel != null && onCta != null) ...[
              const SizedBox(height: 12),
              GestureDetector(
                onTap: onCta,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF30D158).withAlpha(25),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: const Color(0xFF30D158).withAlpha(100),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        ctaLabel!,
                        style: const TextStyle(
                          color: Color(0xFF30D158),
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(width: 4),
                      const Icon(
                        Icons.arrow_forward_rounded,
                        color: Color(0xFF30D158),
                        size: 14,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
