/// SyncQueue — File d'actions offline persistée dans SharedPreferences.
///
/// La queue est sérialisée en JSON dans SharedPreferences.
/// Thread-safe pour les opérations async standard Dart.
///
/// Usage :
/// ```dart
/// final queue = ref.read(syncQueueProvider);
/// await queue.enqueue(SyncAction(
///   id: uuid(),
///   type: SyncActionType.addHydrationLog,
///   payload: {'amount_ml': 250},
///   queuedAt: DateTime.now(),
/// ));
/// ```
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'sync_models.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

final syncQueueProvider = Provider<SyncQueue>((ref) => SyncQueue());

// ── Service ───────────────────────────────────────────────────────────────────

class SyncQueue {
  static const _storageKey = 'soma_sync_queue';

  // ── API publique ───────────────────────────────────────────────────────────

  /// Ajoute une action en queue. Idempotent par [SyncAction.id].
  Future<void> enqueue(SyncAction action) async {
    final actions = await _loadAll();
    // Éviter les doublons
    if (actions.any((a) => a.id == action.id)) return;
    actions.add(action);
    await _saveAll(actions);
    debugPrint('[SyncQueue] enqueued ${action.type.name} (${action.id})');
  }

  /// Charge toutes les actions (tous statuts).
  Future<List<SyncAction>> getAll() async => _loadAll();

  /// Actions en attente uniquement (pending + failed + retryable).
  Future<List<SyncAction>> getPending() async {
    final all = await _loadAll();
    return all
        .where((a) =>
            a.status == SyncStatus.pending ||
            (a.status == SyncStatus.failed && a.canRetry))
        .toList();
  }

  /// Nombre d'actions en attente.
  Future<int> pendingCount() async => (await getPending()).length;

  /// Met à jour une action existante par [id].
  Future<void> update(String id, SyncAction updated) async {
    final actions = await _loadAll();
    final idx = actions.indexWhere((a) => a.id == id);
    if (idx >= 0) {
      actions[idx] = updated;
      await _saveAll(actions);
    }
  }

  /// Supprime une action par [id].
  Future<void> remove(String id) async {
    final actions = await _loadAll();
    actions.removeWhere((a) => a.id == id);
    await _saveAll(actions);
  }

  /// Supprime toutes les actions synchronisées.
  Future<int> purgeSynced() async {
    final actions = await _loadAll();
    final before = actions.length;
    actions.removeWhere((a) => a.status == SyncStatus.synced);
    await _saveAll(actions);
    return before - actions.length;
  }

  /// Vide complètement la queue.
  Future<void> purgeAll() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }

  // ── Privé ──────────────────────────────────────────────────────────────────

  Future<List<SyncAction>> _loadAll() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw == null) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .map((e) => SyncAction.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('[SyncQueue] decode error: $e — resetting queue');
      await prefs.remove(_storageKey);
      return [];
    }
  }

  Future<void> _saveAll(List<SyncAction> actions) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(actions.map((a) => a.toJson()).toList());
    await prefs.setString(_storageKey, encoded);
  }
}
