/// SOMA Design System — ThemeData Builder
///
/// Builds a complete [ThemeData] from a [SomaColors] palette.
/// Usage :
///   final theme = buildSomaTheme(SomaColors.light, Brightness.light);
library;

import 'package:flutter/material.dart';
import 'soma_colors.dart';

/// Builds a fully-configured [ThemeData] for the given [colors] and [brightness].
ThemeData buildSomaTheme(SomaColors colors, Brightness brightness) {
  final isDark = brightness == Brightness.dark;

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    scaffoldBackgroundColor: colors.background,
    colorScheme: ColorScheme(
      brightness: brightness,
      primary: colors.accent,
      secondary: colors.info,
      surface: colors.surface,
      error: colors.danger,
      onPrimary: Colors.black,
      onSecondary: Colors.black,
      onSurface: colors.text,
      onError: Colors.white,
    ),
    fontFamily: 'Inter',
    textTheme: TextTheme(
      displayLarge: TextStyle(
        color: colors.text,
        fontWeight: FontWeight.w800,
      ),
      titleLarge: TextStyle(
        color: colors.text,
        fontWeight: FontWeight.w600,
      ),
      bodyMedium: TextStyle(
        color: colors.textSecondary,
      ),
      bodySmall: TextStyle(
        color: colors.textMuted,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: colors.accent,
        foregroundColor: Colors.black,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
    dividerColor: colors.border,
    appBarTheme: AppBarTheme(
      backgroundColor: colors.navBackground,
      foregroundColor: colors.text,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
    ),
    cardTheme: CardThemeData(
      color: colors.cardBackground,
      elevation: isDark ? 0 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: colors.border, width: isDark ? 1 : 0),
      ),
    ),
    bottomNavigationBarTheme: BottomNavigationBarThemeData(
      backgroundColor: colors.navBackground,
      selectedItemColor: colors.accent,
      unselectedItemColor: colors.textMuted,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
      selectedLabelStyle: const TextStyle(fontSize: 11),
      unselectedLabelStyle: const TextStyle(fontSize: 11),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: colors.surface,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: colors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: colors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: colors.accent, width: 1.5),
      ),
      hintStyle: TextStyle(color: colors.textMuted),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: colors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: colors.surface,
      surfaceTintColor: Colors.transparent,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: colors.surface,
      contentTextStyle: TextStyle(color: colors.text),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      behavior: SnackBarBehavior.floating,
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(
      color: colors.accent,
      linearTrackColor: colors.border,
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return colors.accent;
        return colors.textMuted;
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return colors.accent.withValues(alpha: 0.3);
        }
        return colors.border;
      }),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: colors.surface,
      selectedColor: colors.accent.withValues(alpha: 0.15),
      labelStyle: TextStyle(color: colors.text, fontSize: 13),
      side: BorderSide(color: colors.border),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    ),
  );
}
