/// Tests modèles Sync — SOMA LOT 12.
///
/// ~10 tests : SyncAction, SyncStatus, SyncResult serialization.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/sync/sync_models.dart';

void main() {
  group('SyncAction', () {
    final now = DateTime(2026, 3, 8, 10, 0, 0);

    SyncAction _build({
      String id = 'test_id',
      SyncActionType type = SyncActionType.addNutritionEntry,
      SyncStatus status = SyncStatus.pending,
      int retryCount = 0,
    }) =>
        SyncAction(
          id: id,
          type: type,
          payload: {'meal': 'salad', 'calories': 350},
          queuedAt: now,
          status: status,
          retryCount: retryCount,
        );

    test('fromJson parse tous les champs', () {
      final action = _build();
      final json = action.toJson();
      final restored = SyncAction.fromJson(json);

      expect(restored.id, 'test_id');
      expect(restored.type, SyncActionType.addNutritionEntry);
      expect(restored.status, SyncStatus.pending);
      expect(restored.retryCount, 0);
      expect(restored.payload['meal'], 'salad');
    });

    test('toJson / fromJson round-trip pour tous les types', () {
      for (final type in SyncActionType.values) {
        final a = _build(id: 'id_${type.name}', type: type);
        final restored = SyncAction.fromJson(a.toJson());
        expect(restored.type, type,
            reason: 'Round-trip failed for ${type.name}');
      }
    });

    test('toJson / fromJson round-trip pour tous les statuts', () {
      for (final status in SyncStatus.values) {
        final a = _build(status: status);
        final restored = SyncAction.fromJson(a.toJson());
        expect(restored.status, status,
            reason: 'Round-trip failed for ${status.name}');
      }
    });

    test('copyWith préserve les champs non modifiés', () {
      final a = _build(retryCount: 2);
      final b = a.copyWith(status: SyncStatus.syncing);
      expect(b.id, a.id);
      expect(b.type, a.type);
      expect(b.retryCount, 2);
      expect(b.status, SyncStatus.syncing);
    });

    test('copyWith lastError', () {
      final a = _build();
      final b = a.copyWith(lastError: 'Network timeout');
      expect(b.lastError, 'Network timeout');
      expect(b.id, a.id);
    });

    test('maxRetries est 3', () {
      expect(SyncAction.maxRetries, 3);
    });

    test('retryCount initial est 0', () {
      final a = _build();
      expect(a.retryCount, 0);
    });

    test('lastError est null par défaut', () {
      final a = _build();
      expect(a.lastError, isNull);
    });
  });

  group('SyncResult', () {
    test('synced + failed + pending corrects', () {
      final result = SyncResult(synced: 5, failed: 2, pending: 1, errors: ['e1']);
      expect(result.synced, 5);
      expect(result.failed, 2);
      expect(result.pending, 1);
      expect(result.errors.length, 1);
    });

    test('SyncResult vide valide', () {
      final result = SyncResult(synced: 0, failed: 0, pending: 0, errors: []);
      expect(result.synced, 0);
      expect(result.errors, isEmpty);
    });
  });

  group('SyncActionType', () {
    test('9 types disponibles', () {
      expect(SyncActionType.values.length, 9);
    });

    test('contient les types essentiels', () {
      expect(SyncActionType.values, contains(SyncActionType.addNutritionEntry));
      expect(SyncActionType.values, contains(SyncActionType.addHydrationLog));
      expect(SyncActionType.values, contains(SyncActionType.addSleepLog));
      expect(SyncActionType.values, contains(SyncActionType.createWorkoutSession));
      expect(SyncActionType.values, contains(SyncActionType.saveVisionSession));
    });
  });
}
