/// LocalCache — Cache local JSON + TTL via SharedPreferences.
///
/// Design :
///   - stocke des `Map<String, dynamic>` sérialisés en JSON
///   - chaque entrée a une clé d'expiry (timestamp ms)
///   - purge des données expirées via [purgeExpired()]
///   - taille cache observable via [estimatedSizeBytes()]
///
/// Usage :
/// ```dart
/// final cache = ref.read(localCacheProvider);
/// await cache.set('key', {'foo': 'bar'}, ttl: const Duration(hours: 4));
/// final data = await cache.get('key');  // null si expiré
/// ```
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final localCacheProvider = Provider<LocalCache>((ref) => LocalCache());

// ── Service ───────────────────────────────────────────────────────────────────

/// Service de cache local basé sur SharedPreferences.
///
/// Thread-safe pour les opérations async Dart standard.
class LocalCache {
  static const _expiryTag = '_expiry';
  static const _updatedAtTag = '_updated_at';

  // ── API publique ───────────────────────────────────────────────────────────

  /// Stocke [data] sous [key] avec une durée de vie [ttl].
  ///
  /// [ttl] null = pas d'expiry (données permanentes).
  Future<void> set(
    String key,
    Map<String, dynamic> data, {
    Duration? ttl,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(data);
    await prefs.setString(key, encoded);

    final now = DateTime.now().millisecondsSinceEpoch;
    await prefs.setInt('$key$_updatedAtTag', now);

    if (ttl != null) {
      final expiryMs = now + ttl.inMilliseconds;
      await prefs.setInt('$key$_expiryTag', expiryMs);
    } else {
      await prefs.remove('$key$_expiryTag');
    }
  }

  /// Récupère les données sous [key].
  ///
  /// Retourne `null` si :
  ///   - clé inexistante
  ///   - données expirées (sauf si [ignoreExpiry] est vrai)
  Future<Map<String, dynamic>?> get(
    String key, {
    bool ignoreExpiry = false,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (!ignoreExpiry) {
      final expiryMs = prefs.getInt('$key$_expiryTag');
      if (expiryMs != null) {
        if (DateTime.now().millisecondsSinceEpoch > expiryMs) {
          return null; // expiré
        }
      }
    }
    final raw = prefs.getString(key);
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('[LocalCache] decode error for $key: $e');
      return null;
    }
  }

  /// Indique si la clé existe ET n'est pas expirée.
  Future<bool> has(String key) async => (await get(key)) != null;

  /// Indique si la clé existe, même si expirée.
  Future<bool> hasStale(String key) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey(key);
  }

  /// Retourne le timestamp de la dernière mise à jour ou null.
  Future<DateTime?> updatedAt(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final ms = prefs.getInt('$key$_updatedAtTag');
    if (ms == null) return null;
    return DateTime.fromMillisecondsSinceEpoch(ms);
  }

  /// Retourne l'âge des données en minutes (null si pas de données).
  Future<int?> ageMinutes(String key) async {
    final updated = await updatedAt(key);
    if (updated == null) return null;
    return DateTime.now().difference(updated).inMinutes;
  }

  /// Supprime une entrée.
  Future<void> remove(String key) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(key);
    await prefs.remove('$key$_expiryTag');
    await prefs.remove('$key$_updatedAtTag');
  }

  /// Purge toutes les entrées expirées.
  /// À appeler au démarrage ou à la demande depuis les Settings.
  Future<int> purgeExpired() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys().toList();
    final now = DateTime.now().millisecondsSinceEpoch;
    int purged = 0;

    for (final key in keys) {
      if (key.endsWith(_expiryTag)) {
        final expiryMs = prefs.getInt(key);
        if (expiryMs != null && now > expiryMs) {
          // Retrouver la clé principale
          final mainKey = key.substring(0, key.length - _expiryTag.length);
          await prefs.remove(mainKey);
          await prefs.remove(key);
          await prefs.remove('$mainKey$_updatedAtTag');
          purged++;
        }
      }
    }
    return purged;
  }

  /// Supprime toutes les entrées de cache SOMA (préfixe `soma_cache_`).
  Future<void> purgeAll() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys()
        .where((k) => k.startsWith('soma_cache_'))
        .toList();
    for (final key in keys) {
      await prefs.remove(key);
    }
  }

  /// Taille estimée du cache en bytes (longueur des JSON stockés).
  Future<int> estimatedSizeBytes() async {
    final prefs = await SharedPreferences.getInstance();
    int total = 0;
    for (final key in prefs.getKeys()) {
      if (key.startsWith('soma_cache_') && !key.endsWith(_expiryTag) &&
          !key.endsWith(_updatedAtTag)) {
        final raw = prefs.getString(key);
        if (raw != null) total += raw.length;
      }
    }
    return total;
  }

  /// Nombre d'entrées actives (non expirées).
  Future<int> activeEntryCount() async {
    final prefs = await SharedPreferences.getInstance();
    final now = DateTime.now().millisecondsSinceEpoch;
    int count = 0;
    for (final key in prefs.getKeys()) {
      if (!key.startsWith('soma_cache_') ||
          key.endsWith(_expiryTag) ||
          key.endsWith(_updatedAtTag)) continue;
      final expiryKey = '$key$_expiryTag';
      final expiryMs = prefs.getInt(expiryKey);
      if (expiryMs == null || now <= expiryMs) {
        count++;
      }
    }
    return count;
  }
}

// ── CacheEntry helper ─────────────────────────────────────────────────────────

/// Enveloppe un [data] avec ses métadonnées de fraîcheur.
class CacheEntry<T> {
  final T data;
  final DateTime updatedAt;
  final bool isStale;

  const CacheEntry({
    required this.data,
    required this.updatedAt,
    required this.isStale,
  });

  /// Âge en minutes.
  int get ageMinutes => DateTime.now().difference(updatedAt).inMinutes;

  /// Label de fraîcheur formaté (ex: "il y a 5 min").
  String get freshnessLabel {
    final mins = ageMinutes;
    if (mins < 1) return 'À l\'instant';
    if (mins < 60) return 'il y a $mins min';
    final hrs = mins ~/ 60;
    if (hrs < 24) return 'il y a $hrs h';
    return 'il y a ${hrs ~/ 24} j';
  }
}
