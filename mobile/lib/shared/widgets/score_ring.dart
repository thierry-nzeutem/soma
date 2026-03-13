/// Widget ScoreRing — anneau circulaire affichant un score 0–100.
///
/// Utilise CustomPainter pour dessiner l'arc de progression.
/// Couleur dynamique selon le score : rouge → orange → vert.
library;

import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';

class ScoreRing extends StatelessWidget {
  /// Score entre 0 et 100.
  final double score;

  /// Rayon total du widget.
  final double size;

  /// Épaisseur de l'anneau.
  final double strokeWidth;

  /// Texte sous le score (ex: "Longévité").
  final String? label;

  /// Texte secondaire (ex: "Âge bio : 34 ans").
  final String? sublabel;

  const ScoreRing({
    super.key,
    required this.score,
    this.size = 160,
    this.strokeWidth = 12,
    this.label,
    this.sublabel,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = _scoreColor(score, colors);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Arc dessiné via CustomPainter
          CustomPaint(
            size: Size(size, size),
            painter: _RingPainter(
              score: score,
              color: color,
              strokeWidth: strokeWidth,
            ),
          ),
          // Contenu centré
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                score.toStringAsFixed(0),
                style: TextStyle(
                  color: colors.text,
                  fontSize: size * 0.22,
                  fontWeight: FontWeight.w800,
                  height: 1,
                ),
              ),
              if (label != null)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    label!,
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: size * 0.085,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              if (sublabel != null)
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(
                    sublabel!,
                    style: TextStyle(
                      color: color,
                      fontSize: size * 0.075,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  static Color _scoreColor(double score, SomaColors colors) {
    if (score >= 75) return colors.accent;          // vert
    if (score >= 50) return const Color(0xFFFFB347); // orange
    return colors.danger;                            // rouge
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
    final radius = (size.width - strokeWidth) / 2;

    // Piste de fond
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..color = const Color(0xFF2A2A2A)
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round,
    );

    // Arc de progression
    final sweepAngle = 2 * math.pi * (score / 100);
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,     // Départ à 12h
      sweepAngle,
      false,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(_RingPainter old) =>
      old.score != score || old.color != color;
}
