/// Widget HealthScoreRing — anneau concentrique pour un score de santé.
///
/// Similaire à ScoreRing mais avec une couleur et un label personnalisables.
/// Utilisé dans le Morning Briefing pour les scores individuels (nutrition,
/// hydratation, entraînement, etc.).
library;

import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class HealthScoreRing extends StatelessWidget {
  /// Score entre 0 et 100.
  final double score;

  /// Couleur de l'arc (si null, couleur dynamique basée sur le score).
  final Color? color;

  /// Label principal sous le score.
  final String label;

  /// Label secondaire (ex: unité, sous-titre).
  final String? sublabel;

  /// Taille du widget.
  final double size;

  /// Épaisseur de l'anneau.
  final double strokeWidth;

  const HealthScoreRing({
    super.key,
    required this.score,
    required this.label,
    this.color,
    this.sublabel,
    this.size = 100,
    this.strokeWidth = 10,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final ringColor = color ?? _defaultColor(score, colors);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _RingPainter(
              score: score,
              color: ringColor,
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
                  fontSize: size * 0.22,
                  fontWeight: FontWeight.w700,
                  height: 1.0,
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  label,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: size * 0.085,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (sublabel != null)
                Text(
                  sublabel!,
                  style: TextStyle(
                    color: ringColor,
                    fontSize: size * 0.075,
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
            ],
          ),
        ],
      ),
    );
  }

  static Color _defaultColor(double score, SomaColors colors) {
    if (score >= 75) return colors.success;
    if (score >= 50) return colors.warning;
    return colors.danger;
  }
}

class _RingPainter extends CustomPainter {
  final double score;
  final Color color;
  final double strokeWidth;

  const _RingPainter({
    required this.score,
    required this.color,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (math.min(size.width, size.height) - strokeWidth) / 2;
    final rect = Rect.fromCircle(center: center, radius: radius);
    const startAngle = -math.pi / 2; // 12h

    // Fond
    canvas.drawArc(
      rect, startAngle, 2 * math.pi, false,
      Paint()
        ..color = const Color(0xFF2A2A2A)
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round,
    );

    // Progression
    final sweep = 2 * math.pi * (score.clamp(0, 100) / 100);
    if (sweep > 0) {
      canvas.drawArc(
        rect, startAngle, sweep, false,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = strokeWidth
          ..strokeCap = StrokeCap.round,
      );
    }
  }

  @override
  bool shouldRepaint(_RingPainter old) =>
      old.score != score || old.color != color;
}
