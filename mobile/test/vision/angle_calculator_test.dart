/// Tests AngleCalculator — LOT 7 Computer Vision.
library;

import 'package:flutter/material.dart' show Offset;
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/features/vision/services/angle_calculator.dart';

void main() {
  // ── angleBetween ──────────────────────────────────────────────────────────

  group('AngleCalculator.angleBetween', () {
    test('angle droit = 90°', () {
      // A au dessus de B, C à droite de B — angle droit
      const a = Offset(0, 0); // haut
      const b = Offset(0, 1); // vertex
      const c = Offset(1, 1); // droite
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, closeTo(90.0, 0.01));
    });

    test('angle plat = 180°', () {
      const a = Offset(0, 0);
      const b = Offset(1, 0);
      const c = Offset(2, 0);
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, closeTo(180.0, 0.01));
    });

    test('angle aigu 45°', () {
      const a = Offset(0, 1);
      const b = Offset(0, 0);
      const c = Offset(1, 1);
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, closeTo(45.0, 0.5));
    });

    test('angle obtus ~120°', () {
      // Triangle équilatéral → angle de 60° → supplémentaire 120° selon positionnement
      const a = Offset(-1, 0);
      const b = Offset(0, 0);
      const c = Offset(0.5, 0.866); // 60° angle entre BA et BC
      final angle = AngleCalculator.angleBetween(a, b, c);
      // L'angle entre (-1,0) et (0.5, 0.866) depuis (0,0) est 120°
      expect(angle, closeTo(120.0, 1.0));
    });

    test('retourne 0 si vecteur nul (a == b)', () {
      const a = Offset(1, 1);
      const b = Offset(1, 1); // même point
      const c = Offset(2, 1);
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, 0.0);
    });

    test('retourne 0 si c == b', () {
      const a = Offset(0, 0);
      const b = Offset(1, 1);
      const c = Offset(1, 1); // même point que b
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, 0.0);
    });

    test('angle est toujours positif', () {
      const a = Offset(2, 1);
      const b = Offset(1, 1);
      const c = Offset(0, 0);
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, greaterThanOrEqualTo(0.0));
    });

    test('angle est toujours <= 180°', () {
      const a = Offset(0, 0);
      const b = Offset(1, 0);
      const c = Offset(2, 0);
      final angle = AngleCalculator.angleBetween(a, b, c);
      expect(angle, lessThanOrEqualTo(180.0));
    });
  });
}
