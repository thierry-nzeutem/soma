/// SOMA Theme Extensions — Convenient access to SOMA colors via BuildContext.
///
/// Usage :
///   ```dart
///   final bg = context.somaColors.background;
///   final accent = context.somaColors.accent;
///   ```
///
/// This resolves the current brightness (dark/light) and returns
/// the matching [SomaColors] palette.
library;

import 'package:flutter/material.dart';
import 'soma_colors.dart';

extension SomaThemeExtension on BuildContext {
  /// Returns the [SomaColors] palette matching the current theme brightness.
  SomaColors get somaColors =>
      Theme.of(this).brightness == Brightness.dark
          ? SomaColors.dark
          : SomaColors.light;

  /// Shorthand for `Theme.of(this).brightness == Brightness.dark`.
  bool get isDarkMode => Theme.of(this).brightness == Brightness.dark;
}
