/// MovementHealthRing — Anneau de score pour la santé du mouvement.
///
/// Affiche le MovementHealthScore (0-100) avec un anneau circulaire coloré.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

class MovementHealthRing extends StatelessWidget {
  /// Score 0-100.
  final double score;
  final double size;
  final double strokeWidth;
  final String? label;

  const MovementHealthRing({
    super.key,
    required this.score,
    this.size = 140,
    this.strokeWidth = 12,
    this.label,
  });

  Color get _scoreColor {
    if (score >= 80) return const Color(0xFF22C55E);
    if (score >= 60) return const Color(0xFF84CC16);
    if (score >= 40) return const Color(0xFFF59E0B);
    if (score >= 20) return const Color(0xFFF97316);
    return const Color(0xFFEF4444);
  }

  String get _scoreLabel {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Bon';
    if (score >= 40) return 'Modéré';
    if (score >= 20) return 'Faible';
    return 'Insuffisant';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _RingPainter(
              progress: (score / 100).clamp(0.0, 1.0),
              color: _scoreColor,
              backgroundColor:
                  theme.colorScheme.onSurface.withOpacity(0.08),
              strokeWidth: strokeWidth,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                score.toStringAsFixed(0),
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: _scoreColor,
                ),
              ),
              Text(
                label ?? _scoreLabel,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color backgroundColor;
  final double strokeWidth;

  _RingPainter({
    required this.progress,
    required this.color,
    required this.backgroundColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width / 2) - strokeWidth / 2;
    const startAngle = -math.pi / 2;
    const fullSweep = 2 * math.pi;

    final bgPaint = Paint()
      ..color = backgroundColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      fullSweep,
      false,
      bgPaint,
    );

    if (progress > 0) {
      final fgPaint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round;
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        fullSweep * progress,
        false,
        fgPaint,
      );
    }
  }

  @override
  bool shouldRepaint(_RingPainter old) =>
      old.progress != progress || old.color != color;
}
