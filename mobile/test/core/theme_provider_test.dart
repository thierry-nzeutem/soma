import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/theme/soma_colors.dart';
import 'package:soma_mobile/core/theme/soma_theme.dart';
import 'package:soma_mobile/core/theme/theme_provider.dart';

void main() {
  group('SomaColors', () {
    test('dark palette has correct background', () {
      expect(SomaColors.dark.background, const Color(0xFF0A0A0A));
    });

    test('light palette has correct background', () {
      expect(SomaColors.light.background, const Color(0xFFFFFFFF));
    });

    test('accent is identical in both themes', () {
      expect(SomaColors.dark.accent, SomaColors.light.accent);
      expect(SomaColors.dark.accent, const Color(0xFF00E5A0));
    });

    test('dark text is white', () {
      expect(SomaColors.dark.text, const Color(0xFFFFFFFF));
    });

    test('light text is near-black', () {
      expect(SomaColors.light.text, const Color(0xFF1C1C1E));
    });

    test('dark surface is #141414', () {
      expect(SomaColors.dark.surface, const Color(0xFF141414));
    });

    test('light surface is #F5F5F7', () {
      expect(SomaColors.light.surface, const Color(0xFFF5F5F7));
    });

    test('fromBrightness returns dark for Brightness.dark', () {
      final colors = SomaColors.fromBrightness(Brightness.dark);
      expect(colors.background, SomaColors.dark.background);
    });

    test('fromBrightness returns light for Brightness.light', () {
      final colors = SomaColors.fromBrightness(Brightness.light);
      expect(colors.background, SomaColors.light.background);
    });

    test('warning color is same in both themes', () {
      expect(SomaColors.dark.warning, SomaColors.light.warning);
    });

    test('danger color is same in both themes', () {
      expect(SomaColors.dark.danger, SomaColors.light.danger);
    });

    test('success color is same in both themes', () {
      expect(SomaColors.dark.success, SomaColors.light.success);
    });

    test('all dark fields are non-null', () {
      final d = SomaColors.dark;
      expect(d.background, isNotNull);
      expect(d.surface, isNotNull);
      expect(d.border, isNotNull);
      expect(d.accent, isNotNull);
      expect(d.text, isNotNull);
      expect(d.textSecondary, isNotNull);
      expect(d.textMuted, isNotNull);
      expect(d.navBackground, isNotNull);
      expect(d.navBorder, isNotNull);
      expect(d.cardBackground, isNotNull);
    });

    test('all light fields are non-null', () {
      final l = SomaColors.light;
      expect(l.background, isNotNull);
      expect(l.surface, isNotNull);
      expect(l.border, isNotNull);
      expect(l.accent, isNotNull);
      expect(l.text, isNotNull);
      expect(l.textSecondary, isNotNull);
      expect(l.textMuted, isNotNull);
      expect(l.navBackground, isNotNull);
      expect(l.navBorder, isNotNull);
      expect(l.cardBackground, isNotNull);
    });

    test('dark and light backgrounds are different', () {
      expect(SomaColors.dark.background, isNot(SomaColors.light.background));
    });

    test('dark and light text are different', () {
      expect(SomaColors.dark.text, isNot(SomaColors.light.text));
    });
  });

  group('SomaThemeMode', () {
    test('fromString parses light', () {
      expect(SomaThemeMode.fromString('light'), SomaThemeMode.light);
    });

    test('fromString parses dark', () {
      expect(SomaThemeMode.fromString('dark'), SomaThemeMode.dark);
    });

    test('fromString parses system', () {
      expect(SomaThemeMode.fromString('system'), SomaThemeMode.system);
    });

    test('fromString defaults to system for null', () {
      expect(SomaThemeMode.fromString(null), SomaThemeMode.system);
    });

    test('fromString defaults to system for unknown', () {
      expect(SomaThemeMode.fromString('auto'), SomaThemeMode.system);
    });

    test('toApiValue returns correct strings', () {
      expect(SomaThemeMode.light.toApiValue(), 'light');
      expect(SomaThemeMode.dark.toApiValue(), 'dark');
      expect(SomaThemeMode.system.toApiValue(), 'system');
    });
  });

  group('buildSomaTheme', () {
    test('dark theme has dark brightness', () {
      final theme = buildSomaTheme(SomaColors.dark, Brightness.dark);
      expect(theme.brightness, Brightness.dark);
    });

    test('light theme has light brightness', () {
      final theme = buildSomaTheme(SomaColors.light, Brightness.light);
      expect(theme.brightness, Brightness.light);
    });

    test('dark theme scaffold background matches dark palette', () {
      final theme = buildSomaTheme(SomaColors.dark, Brightness.dark);
      expect(theme.scaffoldBackgroundColor, SomaColors.dark.background);
    });

    test('light theme scaffold background matches light palette', () {
      final theme = buildSomaTheme(SomaColors.light, Brightness.light);
      expect(theme.scaffoldBackgroundColor, SomaColors.light.background);
    });

    test('theme uses Inter font family', () {
      final theme = buildSomaTheme(SomaColors.dark, Brightness.dark);
      expect(theme.fontFamily, 'Inter');
    });

    test('theme primary color is accent', () {
      final theme = buildSomaTheme(SomaColors.dark, Brightness.dark);
      expect(theme.colorScheme.primary, SomaColors.dark.accent);
    });

    test('theme uses Material 3', () {
      final theme = buildSomaTheme(SomaColors.light, Brightness.light);
      expect(theme.useMaterial3, true);
    });

    test('dark appbar background matches nav background', () {
      final theme = buildSomaTheme(SomaColors.dark, Brightness.dark);
      expect(theme.appBarTheme.backgroundColor, SomaColors.dark.navBackground);
    });

    test('light appbar background matches nav background', () {
      final theme = buildSomaTheme(SomaColors.light, Brightness.light);
      expect(theme.appBarTheme.backgroundColor, SomaColors.light.navBackground);
    });
  });
}
