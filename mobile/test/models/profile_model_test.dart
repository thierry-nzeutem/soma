/// Tests parsing modèles Profile + Hydration + Sleep — LOT 6.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/hydration.dart';
import 'package:soma_mobile/core/models/profile.dart';
import 'package:soma_mobile/core/models/sleep_log.dart';

void main() {
  // ── UserProfile ─────────────────────────────────────────────────────────────

  group('UserProfile', () {
    final json = {
      'id': 'user1',
      'first_name': 'Alice',
      'age': 30,
      'sex': 'female',
      'height_cm': 165.0,
      'current_weight_kg': 60.0,
      'goal_weight_kg': 58.0,
      'primary_goal': 'weight_loss',
      'activity_level': 'moderate',
      'fitness_level': 'intermediate',
      'dietary_regime': 'mediterranean',
      'intermittent_fasting': true,
      'fasting_protocol': '16:8',
      'meals_per_day': 3,
      'home_equipment': ['dumbbells', 'yoga_mat'],
      'gym_access': true,
      'computed': {
        'bmi': 22.0,
        'bmr_kcal': 1400.0,
        'tdee_kcal': 2170.0,
        'target_calories_kcal': 1870.0,
        'target_protein_g': 120.0,
        'target_hydration_ml': 2500.0,
      },
      'profile_completeness_score': 88.0,
    };

    test('fromJson parses all fields', () {
      final p = UserProfile.fromJson(json);
      expect(p.id, 'user1');
      expect(p.firstName, 'Alice');
      expect(p.age, 30);
      expect(p.heightCm, 165.0);
      expect(p.intermittentFasting, isTrue);
      expect(p.homeEquipment, ['dumbbells', 'yoga_mat']);
      expect(p.gymAccess, isTrue);
    });

    test('displayName returns firstName', () {
      expect(UserProfile.fromJson(json).displayName, 'Alice');
    });

    test('displayName defaults to Utilisateur', () {
      final j = Map<String, dynamic>.from(json)..remove('first_name');
      j['computed'] = <String, dynamic>{};
      expect(UserProfile.fromJson(j).displayName, 'Utilisateur');
    });

    test('goalLabel for weight_loss', () {
      expect(UserProfile.fromJson(json).goalLabel, 'Perte de poids');
    });

    test('goalLabel for muscle_gain', () {
      final j = Map<String, dynamic>.from(json)
        ..['primary_goal'] = 'muscle_gain'
        ..['computed'] = <String, dynamic>{};
      expect(UserProfile.fromJson(j).goalLabel, 'Prise de masse');
    });

    test('activityLabel for moderate', () {
      expect(
          UserProfile.fromJson(json).activityLabel, 'Modérément actif');
    });

    test('fitnessLabel for intermediate', () {
      expect(UserProfile.fromJson(json).fitnessLabel, 'Intermédiaire');
    });

    test('computed.bmi parsed correctly', () {
      expect(UserProfile.fromJson(json).computed.bmi, 22.0);
    });

    test('computed.targetHydrationMl parsed', () {
      expect(
          UserProfile.fromJson(json).computed.targetHydrationMl, 2500.0);
    });

    test('intermittent_fasting defaults to false', () {
      final j = Map<String, dynamic>.from(json)
        ..remove('intermittent_fasting')
        ..['computed'] = <String, dynamic>{};
      expect(UserProfile.fromJson(j).intermittentFasting, isFalse);
    });

    test('home_equipment defaults to empty list', () {
      final j = Map<String, dynamic>.from(json)
        ..remove('home_equipment')
        ..['computed'] = <String, dynamic>{};
      expect(UserProfile.fromJson(j).homeEquipment, isEmpty);
    });
  });

  group('ComputedMetrics', () {
    test('fromJson with empty map returns all null', () {
      final cm = ComputedMetrics.fromJson({});
      expect(cm.bmi, isNull);
      expect(cm.bmrKcal, isNull);
    });

    test('toJson excludes null values', () {
      const cm = ComputedMetrics(bmi: 22.0);
      final json = cm.toJson();
      expect(json.containsKey('bmi'), isTrue);
      expect(json.containsKey('bmr_kcal'), isFalse);
    });
  });

  // ── HydrationSummary ─────────────────────────────────────────────────────────

  group('HydrationSummary', () {
    final json = {
      'date': '2026-03-07',
      'total_ml': 1500,
      'target_ml': 2500,
      'pct': 60.0,
      'entries': [
        {
          'id': 'h1',
          'volume_ml': 500,
          'logged_at': '2026-03-07T08:00:00Z',
          'beverage_type': 'water',
        },
        {
          'id': 'h2',
          'volume_ml': 1000,
          'logged_at': '2026-03-07T12:00:00Z',
          'beverage_type': 'coffee',
        },
      ],
    };

    test('fromJson parses correctly', () {
      final s = HydrationSummary.fromJson(json);
      expect(s.totalMl, 1500);
      expect(s.targetMl, 2500);
      expect(s.pct, 60.0);
      expect(s.entries.length, 2);
    });

    test('progress is pct/100 clamped 0-1', () {
      final s = HydrationSummary.fromJson(json);
      expect(s.progress, closeTo(0.6, 0.001));
    });

    test('remainingMl computed correctly', () {
      final s = HydrationSummary.fromJson(json);
      expect(s.remainingMl, 1000);
    });

    test('remainingMl is 0 when over target', () {
      final j = Map<String, dynamic>.from(json)
        ..['total_ml'] = 3000
        ..['target_ml'] = 2500;
      expect(HydrationSummary.fromJson(j).remainingMl, 0);
    });
  });

  group('HydrationLog', () {
    test('beverageLabel for water', () {
      final log = HydrationLog.fromJson({
        'id': 'h1',
        'volume_ml': 250,
        'logged_at': '2026-03-07T08:00:00Z',
        'beverage_type': 'water',
      });
      expect(log.beverageLabel, 'Eau');
      expect(log.beverageEmoji, '💧');
    });

    test('beverageLabel for coffee', () {
      final log = HydrationLog.fromJson({
        'id': 'h2',
        'volume_ml': 200,
        'logged_at': '2026-03-07T09:00:00Z',
        'beverage_type': 'coffee',
      });
      expect(log.beverageLabel, 'Café');
    });

    test('beverageLabel defaults to type for unknown', () {
      final log = HydrationLog.fromJson({
        'id': 'h3',
        'volume_ml': 300,
        'logged_at': '2026-03-07T10:00:00Z',
        'beverage_type': 'kombucha',
      });
      expect(log.beverageLabel, 'kombucha');
    });
  });

  // ── SleepSession ─────────────────────────────────────────────────────────────

  group('SleepSession', () {
    final json = {
      'id': 'sl1',
      'start_at': '2026-03-06T23:00:00Z',
      'end_at': '2026-03-07T07:00:00Z',
      'duration_hours': 8.0,
      'perceived_quality': 4,
      'notes': 'Bonne nuit',
    };

    test('fromJson parses correctly', () {
      final s = SleepSession.fromJson(json);
      expect(s.id, 'sl1');
      expect(s.durationHours, 8.0);
      expect(s.perceivedQuality, 4);
      expect(s.notes, 'Bonne nuit');
    });

    test('qualityLabel for quality 4', () {
      final s = SleepSession.fromJson(json);
      expect(s.qualityLabel, 'Bonne');
    });

    test('qualityLabel for quality 1', () {
      final j = Map<String, dynamic>.from(json)..['perceived_quality'] = 1;
      expect(SleepSession.fromJson(j).qualityLabel, 'Mauvaise');
    });

    test('qualityLabel for quality 5', () {
      final j = Map<String, dynamic>.from(json)..['perceived_quality'] = 5;
      expect(SleepSession.fromJson(j).qualityLabel, 'Excellente');
    });

    test('durationLabel for 8.0h', () {
      final s = SleepSession.fromJson(json);
      expect(s.durationLabel, '8h00');
    });

    test('qualityEmoji for quality 5', () {
      final j = Map<String, dynamic>.from(json)..['perceived_quality'] = 5;
      expect(SleepSession.fromJson(j).qualityEmoji, '😴');
    });

    test('qualityEmoji for quality 1', () {
      final j = Map<String, dynamic>.from(json)..['perceived_quality'] = 1;
      expect(SleepSession.fromJson(j).qualityEmoji, '😫');
    });
  });
}
