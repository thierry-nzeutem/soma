/// Tests SyncQueue — SOMA LOT 12.
///
/// ~20 tests : enqueue, idempotence, pending, update, remove, purge.
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:soma_mobile/core/sync/sync_models.dart';
import 'package:soma_mobile/core/sync/sync_queue.dart';

void main() {
  group('SyncQueue', () {
    late SyncQueue queue;

    setUp(() {
      SharedPreferences.setMockInitialValues({});
      queue = SyncQueue();
    });

    SyncAction _makeAction(String id, SyncActionType type) => SyncAction(
          id: id,
          type: type,
          payload: {'key': 'value'},
          queuedAt: DateTime.now(),
        );

    // ── enqueue ────────────────────────────────────────────────────────────

    test('enqueue ajoute une action', () async {
      final action = _makeAction('a1', SyncActionType.addNutritionEntry);
      await queue.enqueue(action);
      final all = await queue.getAll();
      expect(all.length, 1);
      expect(all[0].id, 'a1');
    });

    test('enqueue est idempotent (même id)', () async {
      final action = _makeAction('a1', SyncActionType.addNutritionEntry);
      await queue.enqueue(action);
      await queue.enqueue(action); // doublon
      final all = await queue.getAll();
      expect(all.length, 1);
    });

    test('enqueue de types différents avec même id : ignoré (dernier gagne pas)', () async {
      final a1 = _makeAction('same_id', SyncActionType.addNutritionEntry);
      final a2 = _makeAction('same_id', SyncActionType.addHydrationLog);
      await queue.enqueue(a1);
      await queue.enqueue(a2);
      final all = await queue.getAll();
      expect(all.length, 1);
      expect(all[0].type, SyncActionType.addNutritionEntry); // premier enregistré
    });

    test('enqueue multiples actions différentes', () async {
      await queue.enqueue(_makeAction('a1', SyncActionType.addNutritionEntry));
      await queue.enqueue(_makeAction('a2', SyncActionType.addHydrationLog));
      await queue.enqueue(_makeAction('a3', SyncActionType.addSleepLog));
      final all = await queue.getAll();
      expect(all.length, 3);
    });

    // ── getPending ─────────────────────────────────────────────────────────

    test('getPending retourne uniquement les actions pending', () async {
      await queue.enqueue(_makeAction('p1', SyncActionType.addNutritionEntry));
      await queue.enqueue(_makeAction('p2', SyncActionType.addHydrationLog));

      // Marquer une comme synced.
      await queue.update(
        (await queue.getAll())[0].copyWith(status: SyncStatus.synced),
      );

      final pending = await queue.getPending();
      expect(pending.length, 1);
      expect(pending[0].status, SyncStatus.pending);
    });

    test('getPending retourne liste vide si rien', () async {
      final pending = await queue.getPending();
      expect(pending, isEmpty);
    });

    // ── pendingCount ───────────────────────────────────────────────────────

    test('pendingCount retourne le bon nombre', () async {
      await queue.enqueue(_makeAction('x1', SyncActionType.markInsightRead));
      await queue.enqueue(_makeAction('x2', SyncActionType.dismissInsight));
      final count = await queue.pendingCount();
      expect(count, 2);
    });

    // ── update ─────────────────────────────────────────────────────────────

    test('update modifie l\'action existante', () async {
      final action = _makeAction('u1', SyncActionType.createWorkoutSession);
      await queue.enqueue(action);

      final updated = action.copyWith(status: SyncStatus.failed, lastError: 'timeout');
      await queue.update(updated);

      final all = await queue.getAll();
      expect(all[0].status, SyncStatus.failed);
      expect(all[0].lastError, 'timeout');
    });

    test('update incrémente retryCount', () async {
      final action = _makeAction('r1', SyncActionType.addWorkoutSet);
      await queue.enqueue(action);
      final updated = action.copyWith(retryCount: 1);
      await queue.update(updated);
      final all = await queue.getAll();
      expect(all[0].retryCount, 1);
    });

    // ── remove ─────────────────────────────────────────────────────────────

    test('remove supprime l\'action par id', () async {
      await queue.enqueue(_makeAction('del1', SyncActionType.saveVisionSession));
      await queue.remove('del1');
      final all = await queue.getAll();
      expect(all, isEmpty);
    });

    test('remove ne plante pas si id absent', () async {
      expect(
        () async => await queue.remove('not_in_queue'),
        returnsNormally,
      );
    });

    // ── purgeSynced ────────────────────────────────────────────────────────

    test('purgeSynced supprime uniquement les synced', () async {
      await queue.enqueue(_makeAction('s1', SyncActionType.addNutritionEntry));
      await queue.enqueue(_makeAction('s2', SyncActionType.addHydrationLog));

      final all = await queue.getAll();
      await queue.update(all[0].copyWith(status: SyncStatus.synced));

      await queue.purgeSynced();
      final remaining = await queue.getAll();
      expect(remaining.length, 1);
      expect(remaining[0].id, 's2');
    });

    // ── purgeAll ───────────────────────────────────────────────────────────

    test('purgeAll vide la queue', () async {
      await queue.enqueue(_makeAction('pa1', SyncActionType.addNutritionEntry));
      await queue.enqueue(_makeAction('pa2', SyncActionType.addHydrationLog));
      await queue.purgeAll();
      final all = await queue.getAll();
      expect(all, isEmpty);
    });

    // ── SyncAction helpers ─────────────────────────────────────────────────

    test('SyncAction.maxRetries est 3', () {
      expect(SyncAction.maxRetries, 3);
    });

    test('SyncAction retryCount initial est 0', () {
      final a = _makeAction('r0', SyncActionType.completeWorkoutSession);
      expect(a.retryCount, 0);
    });

    test('SyncAction.fromJson round-trip', () {
      final a = _makeAction('rt1', SyncActionType.markInsightRead);
      final restored = SyncAction.fromJson(a.toJson());
      expect(restored.id, 'rt1');
      expect(restored.type, SyncActionType.markInsightRead);
      expect(restored.status, SyncStatus.pending);
    });

    test('SyncAction.copyWith preserves id', () {
      final a = _makeAction('cp1', SyncActionType.addNutritionEntry);
      final b = a.copyWith(status: SyncStatus.syncing);
      expect(b.id, 'cp1');
      expect(b.status, SyncStatus.syncing);
    });
  });
}
