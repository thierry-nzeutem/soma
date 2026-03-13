/// QualityScoreWidget — anneau de score biomécanique (LOT 7).
///
/// Affiche un score [0-100] avec un anneau de progression circulaire
/// coloré en fonction du score (rouge / orange / vert).
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/theme/theme_extensions.dart';

// ── Widget ────────────────────────────────────────────────────────────────────

class QualityScoreWidget extends StatelessWidget {
  /// Score [0-100].
  final double score;

  /// Label qualitatif (ex. "Bon", "Excellent").
  final String label;

  /// Diamètre du widget en pixels.
  final double size;

  const QualityScoreWidget({
    super.key,
    required this.score,
    required this.label,
    this.size = 80,
  });

  Color get _color {
    if (score >= 80) return const Color(0xFF00E5A0);
    if (score >= 60) return const Color(0xFFFFB347);
    return const Color(0xFFFF6B6B);
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _RingPainter(
          progress: score / 100.0,
          color: _color,
          ringBackgroundColor: colors.border,
          strokeWidth: size * 0.1,
        ),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                score.round().toString(),
                style: TextStyle(
                  color: _color,
                  fontWeight: FontWeight.w900,
                  fontSize: size * 0.28,
                  height: 1.0,
                ),
              ),
              Text(
                label,
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: size * 0.11,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── CustomPainter de l'anneau ─────────────────────────────────────────────────

class _RingPainter extends CustomPainter {
  final double progress; // [0.0, 1.0]
  final Color color;
  final Color ringBackgroundColor;
  final double strokeWidth;

  _RingPainter({
    required this.progress,
    required this.color,
    required this.ringBackgroundColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Fond anneau
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..color = ringBackgroundColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth,
    );

    // Anneau de progression
    if (progress > 0) {
      final rect = Rect.fromCircle(center: center, radius: radius);
      canvas.drawArc(
        rect,
        -math.pi / 2, // départ en haut
        2 * math.pi * progress.clamp(0.0, 1.0),
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
  bool shouldRepaint(_RingPainter old) =>
      old.progress != progress ||
      old.color != color ||
      old.ringBackgroundColor != ringBackgroundColor;
}
