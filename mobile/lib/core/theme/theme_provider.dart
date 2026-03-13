/// SOMA Theme Provider — Riverpod state management for theme preferences.
///
/// Providers :
///   - [themePreferenceProvider] : raw user choice (light | dark | system)
///   - [resolvedBrightnessProvider] : actual Brightness after resolving 'system'
///   - [somaThemeProvider] : ready-to-use ThemeData
///
/// Persistence : SharedPreferences key `soma_theme_preference`.
/// Backend sync : PATCH /api/v1/profile on change.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'soma_colors.dart';
import 'soma_theme.dart';

// ── Theme mode enum ──────────────────────────────────────────────────────────

enum SomaThemeMode {
  light,
  dark,
  system;

  /// Parse from stored string; defaults to [system].
  factory SomaThemeMode.fromString(String? value) => switch (value) {
        'light' => SomaThemeMode.light,
        'dark' => SomaThemeMode.dark,
        _ => SomaThemeMode.system,
      };

  /// API-compatible string value.
  String toApiValue() => name;
}

// ── Theme preference notifier ────────────────────────────────────────────────

const _kPrefKey = 'soma_theme_preference';

class ThemePreferenceNotifier extends StateNotifier<SomaThemeMode> {
  ThemePreferenceNotifier() : super(SomaThemeMode.system) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_kPrefKey);
    state = SomaThemeMode.fromString(stored);
  }

  Future<void> setTheme(SomaThemeMode mode) async {
    state = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kPrefKey, mode.toApiValue());
  }
}

// ── Providers ────────────────────────────────────────────────────────────────

/// Raw user preference (light | dark | system).
final themePreferenceProvider =
    StateNotifierProvider<ThemePreferenceNotifier, SomaThemeMode>(
  (ref) => ThemePreferenceNotifier(),
);

/// Platform brightness provider — updated via [WidgetsBindingObserver]
/// in the root widget. Defaults to [Brightness.light].
final platformBrightnessProvider = StateProvider<Brightness>(
  (ref) => WidgetsBinding.instance.platformDispatcher.platformBrightness,
);

/// Resolved brightness after evaluating 'system' preference.
final resolvedBrightnessProvider = Provider<Brightness>((ref) {
  final pref = ref.watch(themePreferenceProvider);
  return switch (pref) {
    SomaThemeMode.light => Brightness.light,
    SomaThemeMode.dark => Brightness.dark,
    SomaThemeMode.system => ref.watch(platformBrightnessProvider),
  };
});

/// Resolved [SomaColors] for current theme.
final somaColorsProvider = Provider<SomaColors>((ref) {
  final brightness = ref.watch(resolvedBrightnessProvider);
  return SomaColors.fromBrightness(brightness);
});

/// Ready-to-use [ThemeData].
final somaThemeProvider = Provider<ThemeData>((ref) {
  final brightness = ref.watch(resolvedBrightnessProvider);
  final colors = ref.watch(somaColorsProvider);
  return buildSomaTheme(colors, brightness);
});
