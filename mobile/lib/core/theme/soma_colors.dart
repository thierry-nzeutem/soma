/// SOMA Design System — Centralized Color Palette
///
/// Provides `SomaColors.dark` and `SomaColors.light` instances
/// used by `buildSomaTheme()` and `context.somaColors`.
///
/// Accent `#00E5A0` (vert menthe SOMA) is identical in both themes
/// to preserve brand identity.
library;

import 'package:flutter/material.dart';

class SomaColors {
  final Color background;
  final Color surface;
  final Color surfaceVariant;
  final Color border;
  final Color accent;
  final Color accentDim;
  final Color text;
  final Color textSecondary;
  final Color textMuted;
  final Color navBackground;
  final Color navBorder;
  final Color warning;
  final Color danger;
  final Color success;
  final Color info;
  final Color cardBackground;

  /// Colors used specifically in charts and data visualization.
  final Color chartLine;
  final Color chartArea;

  const SomaColors._({
    required this.background,
    required this.surface,
    required this.surfaceVariant,
    required this.border,
    required this.accent,
    required this.accentDim,
    required this.text,
    required this.textSecondary,
    required this.textMuted,
    required this.navBackground,
    required this.navBorder,
    required this.warning,
    required this.danger,
    required this.success,
    required this.info,
    required this.cardBackground,
    required this.chartLine,
    required this.chartArea,
  });

  // ── Dark theme colors (original SOMA palette) ──────────────────────────────

  static const dark = SomaColors._(
    background: Color(0xFF0A0A0A),
    surface: Color(0xFF141414),
    surfaceVariant: Color(0xFF1A1A1A),
    border: Color(0xFF1E1E1E),
    accent: Color(0xFF00E5A0),
    accentDim: Color(0xFF00B47A),
    text: Color(0xFFFFFFFF),
    textSecondary: Color(0xFFCCCCCC),
    textMuted: Color(0xFF888888),
    navBackground: Color(0xFF0D0D0D),
    navBorder: Color(0xFF1E1E1E),
    warning: Color(0xFFFF9500),
    danger: Color(0xFFFF3B30),
    success: Color(0xFF34C759),
    info: Color(0xFF00B4D8),
    cardBackground: Color(0xFF141414),
    chartLine: Color(0xFF00E5A0),
    chartArea: Color(0x3300E5A0),
  );

  // ── Light theme colors ─────────────────────────────────────────────────────

  static const light = SomaColors._(
    background: Color(0xFFFFFFFF),
    surface: Color(0xFFF5F5F7),
    surfaceVariant: Color(0xFFEEEEF0),
    border: Color(0xFFE5E5EA),
    accent: Color(0xFF00E5A0),
    accentDim: Color(0xFF00B47A),
    text: Color(0xFF1C1C1E),
    textSecondary: Color(0xFF636366),
    textMuted: Color(0xFF8E8E93),
    navBackground: Color(0xFFF8F8FA),
    navBorder: Color(0xFFE5E5EA),
    warning: Color(0xFFFF9500),
    danger: Color(0xFFFF3B30),
    success: Color(0xFF34C759),
    info: Color(0xFF00B4D8),
    cardBackground: Color(0xFFFFFFFF),
    chartLine: Color(0xFF00B47A),
    chartArea: Color(0x2200B47A),
  );

  /// Returns the correct palette for a given [brightness].
  static SomaColors fromBrightness(Brightness brightness) =>
      brightness == Brightness.dark ? dark : light;
}
