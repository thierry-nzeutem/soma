/// SOMA Locale Provider — Riverpod state for app locale (FR / EN).
///
/// Persists user choice via SharedPreferences.
/// Falls back to platform locale, then to French.
library;

import 'dart:ui';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ── Supported locales ────────────────────────────────────────────────────────

const kSupportedLocales = [
  Locale('fr'),
  Locale('en'),
];

const _kPrefsKey = 'soma_locale';
const _kDefaultLocale = Locale('fr');

// ── Provider ────────────────────────────────────────────────────────────────

final localeProvider =
    StateNotifierProvider<LocaleNotifier, Locale>((_) => LocaleNotifier());

// ── Notifier ────────────────────────────────────────────────────────────────

class LocaleNotifier extends StateNotifier<Locale> {
  LocaleNotifier() : super(_resolveInitialLocale()) {
    _loadFromPrefs();
  }

  /// Resolve initial locale from platform locale.
  static Locale _resolveInitialLocale() {
    final platformLocale = PlatformDispatcher.instance.locale;
    final langCode = platformLocale.languageCode;
    if (kSupportedLocales.any((l) => l.languageCode == langCode)) {
      return Locale(langCode);
    }
    return _kDefaultLocale;
  }

  Future<void> _loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_kPrefsKey);
    if (saved != null &&
        kSupportedLocales.any((l) => l.languageCode == saved)) {
      state = Locale(saved);
    }
  }

  /// Set the app locale. Persists to SharedPreferences.
  Future<void> setLocale(Locale locale) async {
    if (!kSupportedLocales.contains(locale)) return;
    state = locale;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kPrefsKey, locale.languageCode);
  }

  /// Shorthand for switching by language code string.
  Future<void> setLanguageCode(String code) async {
    await setLocale(Locale(code));
  }
}
