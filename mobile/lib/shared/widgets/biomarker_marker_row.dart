/// SOMA LOT 17 — BiomarkerMarkerRow widget.
///
/// Ligne biomarqueur : nom affiché + valeur + unité + statut + barre de score.
library;

import 'package:flutter/material.dart';

import '../../core/models/biomarker.dart';
import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class BiomarkerMarkerRow extends StatelessWidget {
  final BiomarkerMarker marker;

  const BiomarkerMarkerRow({super.key, required this.marker});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final statusColor = _statusColor(marker.status, colors);

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      marker.displayName,
                      style: TextStyle(
                          color: colors.text,
                          fontWeight: FontWeight.w500,
                          fontSize: 14),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${marker.value.toStringAsFixed(1)} ${marker.unit}',
                      style: TextStyle(
                          color: colors.textMuted, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              // Score numérique
              Text(
                '${marker.score.toStringAsFixed(0)}/100',
                style: TextStyle(
                    color: statusColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 14),
              ),
              const SizedBox(width: 8),
              // Badge statut
              _StatusBadge(status: marker.status, color: statusColor),
            ],
          ),
          const SizedBox(height: 8),
          // Barre de progression
          LinearProgressIndicator(
            value: marker.score / 100,
            backgroundColor: colors.textMuted,
            valueColor: AlwaysStoppedAnimation<Color>(statusColor),
            minHeight: 4,
            borderRadius: BorderRadius.circular(2),
          ),
          if (marker.interpretation.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              marker.interpretation,
              style: TextStyle(
                  color: colors.textMuted, fontSize: 11),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }

  static Color _statusColor(String status, SomaColors colors) => switch (status) {
        'optimal' => colors.success,
        'adequate' => const Color(0xFF30D158),
        'suboptimal' => const Color(0xFFFFCC00),
        'deficient' => colors.danger,
        'elevated' => colors.warning,
        'toxic' => const Color(0xFFFF2D55),
        _ => const Color(0xFF8E8E93),
      };
}

class _StatusBadge extends StatelessWidget {
  final String status;
  final Color color;
  const _StatusBadge({required this.status, required this.color});

  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      'optimal' => 'Optimal',
      'adequate' => 'Correct',
      'suboptimal' => 'Suboptimal',
      'deficient' => 'Carence',
      'elevated' => 'Élevé',
      'toxic' => 'Toxique',
      _ => status,
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
            color: color, fontSize: 10, fontWeight: FontWeight.w600),
      ),
    );
  }
}
