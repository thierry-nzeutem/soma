/// SyncManager — Orchestre le replay de la file d'actions offline.
///
/// Responsabilités :
///   - écoute [isOnlineProvider]
///   - déclenche [_processPendingActions()] à la reconnexion
///   - retry avec backoff simple (retryCount × 2s)
///   - expose [syncStatusProvider] pour l'UI (Settings, banner)
///
/// Platform :
///   - fonctionne entièrement en mémoire / SharedPreferences
///   - pas de background isolate requis (replay opportuniste)
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../api/api_constants.dart';
import '../offline/connectivity_service.dart';
import 'sync_models.dart';
import 'sync_queue.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

/// État de synchronisation exposé à l'UI.
final syncStatusProvider =
    StateNotifierProvider<SyncStatusNotifier, SyncManagerState>(
  (ref) => SyncStatusNotifier(ref),
);

/// Service singleton de synchronisation.
final syncManagerProvider = Provider<SyncManager>((ref) => SyncManager(ref));

// ── State ─────────────────────────────────────────────────────────────────────

class SyncManagerState {
  final bool isSyncing;
  final int pendingCount;
  final DateTime? lastSyncAt;
  final String? lastError;

  const SyncManagerState({
    this.isSyncing = false,
    this.pendingCount = 0,
    this.lastSyncAt,
    this.lastError,
  });

  SyncManagerState copyWith({
    bool? isSyncing,
    int? pendingCount,
    DateTime? lastSyncAt,
    String? lastError,
    bool clearError = false,
  }) =>
      SyncManagerState(
        isSyncing: isSyncing ?? this.isSyncing,
        pendingCount: pendingCount ?? this.pendingCount,
        lastSyncAt: lastSyncAt ?? this.lastSyncAt,
        lastError: clearError ? null : (lastError ?? this.lastError),
      );
}

// ── Notifier UI ───────────────────────────────────────────────────────────────

class SyncStatusNotifier extends StateNotifier<SyncManagerState> {
  final Ref _ref;

  SyncStatusNotifier(this._ref) : super(const SyncManagerState()) {
    _init();
  }

  Future<void> _init() async {
    await _refreshPendingCount();

    // Déclencher sync à la reconnexion
    _ref.listen<bool>(isOnlineProvider, (wasOnline, isOnline) async {
      if (!wasOnline! && isOnline) {
        debugPrint('[SyncManager] reconnecté — déclenchement sync');
        await _ref.read(syncManagerProvider).processPending(this);
      }
    });
  }

  Future<void> _refreshPendingCount() async {
    final queue = _ref.read(syncQueueProvider);
    final count = await queue.pendingCount();
    state = state.copyWith(pendingCount: count);
  }

  void setSyncing(bool value) =>
      state = state.copyWith(isSyncing: value, clearError: value);

  void setError(String error) =>
      state = state.copyWith(isSyncing: false, lastError: error);

  void setSynced(int remaining) => state = state.copyWith(
        isSyncing: false,
        pendingCount: remaining,
        lastSyncAt: DateTime.now(),
        clearError: true,
      );

  Future<void> refreshCount() async => _refreshPendingCount();
}

// ── Sync Manager ──────────────────────────────────────────────────────────────

class SyncManager {
  final Ref _ref;

  SyncManager(this._ref);

  /// Traite toutes les actions pending. Appelé à la reconnexion ou manuellement.
  Future<SyncResult> processPending(SyncStatusNotifier notifier) async {
    final queue = _ref.read(syncQueueProvider);
    final pending = await queue.getPending();

    if (pending.isEmpty) return const SyncResult(synced: 0, failed: 0, pending: 0);

    notifier.setSyncing(true);
    int synced = 0;
    int failed = 0;
    final errors = <String>[];

    for (final action in pending) {
      // Marquer en cours
      await queue.update(action.id, action.copyWith(status: SyncStatus.syncing));

      try {
        await _executeAction(action);
        await queue.update(action.id, action.copyWith(status: SyncStatus.synced));
        synced++;
      } catch (e) {
        final newRetry = action.retryCount + 1;
        final newStatus = newRetry >= SyncAction.maxRetries
            ? SyncStatus.failed
            : SyncStatus.pending;
        await queue.update(
          action.id,
          action.copyWith(
            status: newStatus,
            retryCount: newRetry,
            lastError: e.toString(),
          ),
        );
        errors.add('${action.type.name}: $e');
        failed++;
      }
    }

    // Purge les synced pour alléger la queue
    await queue.purgeSynced();

    final remaining = await queue.pendingCount();
    notifier.setSynced(remaining);

    return SyncResult(
      synced: synced,
      failed: failed,
      pending: remaining,
      errors: errors,
    );
  }

  /// Enqueue une action offline (appelé depuis les notifiers features).
  Future<void> enqueue(SyncAction action) async {
    final queue = _ref.read(syncQueueProvider);
    await queue.enqueue(action);

    // Si online, tenter de l'exécuter immédiatement
    final isOnline = _ref.read(isOnlineProvider);
    if (isOnline) {
      final notifier = _ref.read(syncStatusProvider.notifier);
      await processPending(notifier);
    } else {
      await _ref.read(syncStatusProvider.notifier).refreshCount();
    }
  }

  // ── Exécution des actions ──────────────────────────────────────────────────

  Future<void> _executeAction(SyncAction action) async {
    final client = _ref.read(apiClientProvider);
    switch (action.type) {
      case SyncActionType.addNutritionEntry:
        await client.post(ApiConstants.nutritionEntries, data: action.payload);

      case SyncActionType.addHydrationLog:
        await client.post(ApiConstants.hydrationLog, data: action.payload);

      case SyncActionType.addSleepLog:
        await client.post(ApiConstants.sleepLog, data: action.payload);

      case SyncActionType.createWorkoutSession:
        await client.post(ApiConstants.sessions, data: action.payload);

      case SyncActionType.addWorkoutSet:
        final sessionId = action.payload['session_id'] as String;
        await client.post(
          '${ApiConstants.sessions}/$sessionId/sets',
          data: action.payload,
        );

      case SyncActionType.completeWorkoutSession:
        final sessionId = action.payload['session_id'] as String;
        await client.patch('${ApiConstants.sessions}/$sessionId/complete');

      case SyncActionType.markInsightRead:
        final id = action.payload['insight_id'] as String;
        await client.patch('${ApiConstants.insights}/$id/read');

      case SyncActionType.dismissInsight:
        final id = action.payload['insight_id'] as String;
        await client.patch('${ApiConstants.insights}/$id/dismiss');

      case SyncActionType.saveVisionSession:
        await client.post(ApiConstants.visionSessions, data: action.payload);
    }
  }
}
