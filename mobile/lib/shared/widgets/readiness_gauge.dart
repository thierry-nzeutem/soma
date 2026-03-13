/// Widget ReadinessGauge — jauge arc 240° pour le score de récupération.
///
/// Affiche un score 0-100 sous forme d'arc coloré (240° de sweep max).
/// Couleur dynamique : vert (>=75), orange (>=50), rouge (<50).
/// Utilisé dans le Morning Briefing comme widget principal.
library;

import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class ReadinessGauge extends StatelessWidget {
  /// Score de récupération entre 0 et 100.
  final double score;

  /// Taille du widget (hauteur = largeur).
  final double size;

  /// Épaisseur de l'arc.
  final double strokeWidth;

  /// Label affiché sous le score (ex: "Récupération").
  final String label;

  const ReadinessGauge({
    super.key,
    required this.score,
    this.size = 120,
    this.strokeWidth = 14,
    this.label = 'Récupération',
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = _gaugeColor(score, colors);
    final levelLabel = _levelLabel(score);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _GaugePainter(
              score: score,
              color: color,
              strokeWidth: strokeWidth,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                score.toStringAsFixed(0),
                style: TextStyle(
                  color: colors.text,
                  fontSize: size * 0.24,
                  fontWeight: FontWeight.w800,
                  height: 1.0,
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  levelLabel,
                  style: TextStyle(
                    color: color,
                    fontSize: size * 0.09,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  label,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: size * 0.08,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Couleur basée sur les seuils SOMA.
  static Color _gaugeColor(double score, SomaColors colors) {
    if (score >= 75) return colors.success;
    if (score >= 50) return colors.warning;
    return colors.danger;
  }

  /// Libellé textuel du niveau de récupération.
  static String _levelLabel(double score) {
    if (score >= 80) return 'Excellent';
    if (score >= 65) return 'Bon';
    if (score >= 45) return 'Moyen';
    return 'Faible';
  }
}

/// Painter pour l'arc de 240°.
class _GaugePainter extends CustomPainter {
  final double score;
  final Color color;
  final double strokeWidth;

  // L'arc commence à -210° (7h30 sur une horloge) et balaie 240°.
  static const _startAngle = -210.0 * math.pi / 180.0;
  static const _totalSweep = 240.0 * math.pi / 180.0;

  const _GaugePainter({
    required this.score,
    required this.color,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (math.min(size.width, size.height) - strokeWidth) / 2;
    final rect = Rect.fromCircle(center: center, radius: radius);

    // Fond gris (arc complet 240°)
    canvas.drawArc(
      rect,
      _startAngle,
      _totalSweep,
      false,
      Paint()
        ..color = const Color(0xFF2A2A2A)
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round,
    );

    // Arc de progression
    final sweepAngle = _totalSweep * (score.clamp(0, 100) / 100);
    if (sweepAngle > 0) {
      canvas.drawArc(
        rect,
        _startAngle,
        sweepAngle,
        false,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = strokeWidth
          ..strokeCap = StrokeCap.round,
      );
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) =>
      old.score != score || old.color != color || old.strokeWidth != strokeWidth;
}
