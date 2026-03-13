/// Tests CacheConfig — SOMA LOT 12.
///
/// ~10 tests : CacheTTL, CacheKeys builders.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/cache/cache_config.dart';

void main() {
  group('CacheTTL', () {
    test('homeSummary est 4 heures', () {
      expect(CacheTTL.homeSummary, const Duration(hours: 4));
    });

    test('healthPlan est 6 heures', () {
      expect(CacheTTL.healthPlan, const Duration(hours: 6));
    });

    test('twinToday est 4 heures', () {
      expect(CacheTTL.twinToday, const Duration(hours: 4));
    });

    test('biologicalAge est 24 heures', () {
      expect(CacheTTL.biologicalAge, const Duration(hours: 24));
    });

    test('insights est 3 heures', () {
      expect(CacheTTL.insights, const Duration(hours: 3));
    });

    test('motionSummary est 6 heures', () {
      expect(CacheTTL.motionSummary, const Duration(hours: 6));
    });

    test('adaptiveNutrition est 6 heures', () {
      expect(CacheTTL.adaptiveNutrition, const Duration(hours: 6));
    });
  });

  group('CacheKeys', () {
    test('homeSummary génère une clé avec userId', () {
      final key = CacheKeys.homeSummary('user123');
      expect(key, contains('home_summary'));
      expect(key, contains('user123'));
    });

    test('healthPlan génère une clé avec userId', () {
      final key = CacheKeys.healthPlan('user456');
      expect(key, contains('health_plan'));
      expect(key, contains('user456'));
    });

    test('twinToday génère une clé avec userId', () {
      final key = CacheKeys.twinToday('userA');
      expect(key, contains('twin_today'));
      expect(key, contains('userA'));
    });

    test('biologicalAge génère une clé avec userId', () {
      final key = CacheKeys.biologicalAge('userB');
      expect(key, contains('biological_age'));
      expect(key, contains('userB'));
    });

    test('insights génère une clé avec userId', () {
      final key = CacheKeys.insights('userC');
      expect(key, contains('insights'));
      expect(key, contains('userC'));
    });

    test('expiry ajoute le suffixe _expiry', () {
      final key = CacheKeys.expiry('some_key');
      expect(key, 'some_key_expiry');
    });

    test('updatedAt ajoute le suffixe _updated_at', () {
      final key = CacheKeys.updatedAt('some_key');
      expect(key, 'some_key_updated_at');
    });

    test('deux userId différents → deux clés différentes', () {
      final k1 = CacheKeys.homeSummary('user1');
      final k2 = CacheKeys.homeSummary('user2');
      expect(k1, isNot(k2));
    });

    test('allPrefixes contient les préfixes essentiels', () {
      expect(CacheKeys.allPrefixes, contains('home_summary_'));
      expect(CacheKeys.allPrefixes, contains('health_plan_'));
      expect(CacheKeys.allPrefixes, contains('twin_today_'));
      expect(CacheKeys.allPrefixes, contains('insights_'));
    });
  });
}
