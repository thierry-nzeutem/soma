/// Tests modèles Notifications — SOMA LOT 12.
///
/// ~15 tests : NotificationCategory, NotificationPreference, serialization.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/notifications/notification_models.dart';

void main() {
  group('NotificationCategory', () {
    test('displayName retourne le bon label pour chaque catégorie', () {
      expect(NotificationCategory.daily.displayName, 'Briefing quotidien');
      expect(NotificationCategory.hydration.displayName, 'Hydratation');
      expect(NotificationCategory.activity.displayName, 'Activité');
      expect(NotificationCategory.recovery.displayName, 'Récupération');
      expect(NotificationCategory.coach.displayName, 'Coach IA');
      expect(NotificationCategory.safety.displayName, 'Alertes sécurité');
    });

    test('canDisable est false uniquement pour safety', () {
      expect(NotificationCategory.safety.canDisable, isFalse);
      expect(NotificationCategory.daily.canDisable, isTrue);
      expect(NotificationCategory.hydration.canDisable, isTrue);
      expect(NotificationCategory.activity.canDisable, isTrue);
      expect(NotificationCategory.recovery.canDisable, isTrue);
      expect(NotificationCategory.coach.canDisable, isTrue);
    });

    test('description est non vide pour toutes les catégories', () {
      for (final cat in NotificationCategory.values) {
        expect(cat.description.isNotEmpty, isTrue);
      }
    });
  });

  group('NotificationPreference', () {
    test('fromJson parse tous les champs', () {
      final json = {
        'category': 'daily',
        'enabled': true,
        'scheduledHour': 7,
        'scheduledMinute': 30,
      };
      final pref = NotificationPreference.fromJson(json);
      expect(pref.category, NotificationCategory.daily);
      expect(pref.enabled, isTrue);
      expect(pref.scheduledHour, 7);
      expect(pref.scheduledMinute, 30);
    });

    test('fromJson valeurs par défaut', () {
      final pref = NotificationPreference.fromJson({});
      expect(pref.enabled, isTrue);
      expect(pref.scheduledHour, isNull);
      expect(pref.scheduledMinute, isNull);
    });

    test('toJson round-trip', () {
      const pref = NotificationPreference(
        category: NotificationCategory.hydration,
        enabled: false,
        scheduledHour: 15,
        scheduledMinute: 0,
      );
      final json = pref.toJson();
      final restored = NotificationPreference.fromJson(json);
      expect(restored.category, NotificationCategory.hydration);
      expect(restored.enabled, isFalse);
      expect(restored.scheduledHour, 15);
      expect(restored.scheduledMinute, 0);
    });

    test('copyWith enabled change uniquement enabled', () {
      const pref = NotificationPreference(
        category: NotificationCategory.daily,
        enabled: true,
        scheduledHour: 8,
        scheduledMinute: 0,
      );
      final updated = pref.copyWith(enabled: false);
      expect(updated.enabled, isFalse);
      expect(updated.category, NotificationCategory.daily);
      expect(updated.scheduledHour, 8);
    });

    test('copyWith scheduledHour met à jour l\'heure', () {
      const pref = NotificationPreference(
        category: NotificationCategory.hydration,
        enabled: true,
        scheduledHour: 12,
        scheduledMinute: 0,
      );
      final updated = pref.copyWith(scheduledHour: 16, scheduledMinute: 30);
      expect(updated.scheduledHour, 16);
      expect(updated.scheduledMinute, 30);
    });

    test('fromJson avec catégorie inconnue fallback sur daily', () {
      final pref = NotificationPreference.fromJson({'category': 'unknown_cat'});
      expect(pref.category, NotificationCategory.daily);
    });
  });

  group('NotificationPreference.defaults()', () {
    test('retourne 6 catégories', () {
      final defaults = NotificationPreference.defaults();
      expect(defaults.length, 6);
    });

    test('inclut toutes les catégories', () {
      final defaults = NotificationPreference.defaults();
      final cats = defaults.map((p) => p.category).toSet();
      for (final cat in NotificationCategory.values) {
        expect(cats.contains(cat), isTrue,
            reason: '$cat manquant dans defaults');
      }
    });

    test('safety est activé par défaut', () {
      final defaults = NotificationPreference.defaults();
      final safety = defaults.firstWhere(
        (p) => p.category == NotificationCategory.safety,
      );
      expect(safety.enabled, isTrue);
    });

    test('daily a une heure planifiée', () {
      final defaults = NotificationPreference.defaults();
      final daily = defaults.firstWhere(
        (p) => p.category == NotificationCategory.daily,
      );
      expect(daily.scheduledHour, 7);
      expect(daily.scheduledMinute, 30);
    });

    test('hydration a une heure planifiée', () {
      final defaults = NotificationPreference.defaults();
      final hydration = defaults.firstWhere(
        (p) => p.category == NotificationCategory.hydration,
      );
      expect(hydration.scheduledHour, 15);
      expect(hydration.scheduledMinute, 0);
    });
  });

  group('NotificationIds', () {
    test('tous les IDs sont distincts', () {
      final ids = [
        NotificationIds.morningBriefing,
        NotificationIds.hydrationReminder,
        NotificationIds.sleepReminder,
        NotificationIds.activityReminder,
        NotificationIds.recoveryAlert,
        NotificationIds.coachMessage,
        NotificationIds.safetyAlert,
        NotificationIds.syncComplete,
      ];
      expect(ids.toSet().length, ids.length);
    });
  });
}
