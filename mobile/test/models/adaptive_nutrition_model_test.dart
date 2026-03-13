/// Tests modèle Adaptive Nutrition — SOMA LOT 11.
///
/// ~15 tests : parsing JSON, DayType, getters, edge cases.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/adaptive_nutrition.dart';

void main() {
  group('DayType', () {
    test('label retourne les bons labels', () {
      expect(DayType.label(DayType.rest), 'Repos');
      expect(DayType.label(DayType.training), 'Entraînement');
      expect(DayType.label(DayType.intenseTraining), 'Entraînement intensif');
      expect(DayType.label(DayType.recovery), 'Récupération');
      expect(DayType.label(DayType.deload), 'Décharge');
    });

    test('label retourne type inconnu tel quel', () {
      expect(DayType.label('unknown_type'), 'unknown_type');
    });

    test('isTrainingDay est vrai pour training et intense_training', () {
      expect(DayType.isTrainingDay(DayType.training), isTrue);
      expect(DayType.isTrainingDay(DayType.intenseTraining), isTrue);
      expect(DayType.isTrainingDay(DayType.rest), isFalse);
      expect(DayType.isTrainingDay(DayType.recovery), isFalse);
      expect(DayType.isTrainingDay(DayType.deload), isFalse);
    });
  });

  group('NutritionTarget', () {
    test('fromJson parse tous les champs', () {
      final json = {
        'value': 150.0,
        'unit': 'g',
        'rationale': 'Intensité élevée',
        'priority': 'high',
      };
      final target = NutritionTarget.fromJson(json);
      expect(target.value, 150.0);
      expect(target.unit, 'g');
      expect(target.rationale, 'Intensité élevée');
      expect(target.priority, 'high');
    });

    test('fromJson valeurs par défaut', () {
      final target = NutritionTarget.fromJson({});
      expect(target.value, 0.0);
      expect(target.unit, '');
      expect(target.priority, 'normal');
    });

    test('toJson round-trip', () {
      final target = NutritionTarget(
        value: 200.0,
        unit: 'g',
        rationale: 'Test',
        priority: 'critical',
      );
      final restored = NutritionTarget.fromJson(target.toJson());
      expect(restored.value, 200.0);
      expect(restored.priority, 'critical');
    });
  });

  group('AdaptiveNutritionPlan', () {
    Map<String, dynamic> _targetJson({
      double value = 100.0,
      String unit = 'g',
      String priority = 'normal',
    }) =>
        {
          'value': value,
          'unit': unit,
          'rationale': '',
          'priority': priority,
        };

    Map<String, dynamic> _planJson({
      String dayType = 'training',
    }) =>
        {
          'target_date': '2026-03-08',
          'day_type': dayType,
          'glycogen_status': 'normal',
          'calorie_target': _targetJson(value: 2500, unit: 'kcal'),
          'protein_target': _targetJson(value: 135, unit: 'g'),
          'carb_target': _targetJson(value: 300, unit: 'g'),
          'fat_target': _targetJson(value: 70, unit: 'g'),
          'fiber_target': _targetJson(value: 30, unit: 'g'),
          'hydration_target': _targetJson(value: 2625, unit: 'ml'),
          'meal_timing_strategy': 'Repas toutes les 3-4h',
          'fasting_compatible': false,
          'fasting_rationale': '',
          'pre_workout_guidance': 'Glucides 1-2h avant',
          'post_workout_guidance': 'Protéines dans les 30 min',
          'recovery_nutrition_focus': 'Glucides + protéines',
          'electrolyte_focus': 'Sodium + potassium',
          'supplementation_focus': ['Créatine', 'Protéines'],
          'confidence': 0.8,
          'assumptions': ['Poids 75kg'],
          'alerts': [],
        };

    test('fromJson parse le day_type', () {
      final plan = AdaptiveNutritionPlan.fromJson(_planJson());
      expect(plan.dayType, 'training');
    });

    test('fromJson parse les cibles macro', () {
      final plan = AdaptiveNutritionPlan.fromJson(_planJson());
      expect(plan.calorieTarget.value, 2500.0);
      expect(plan.proteinTarget.value, 135.0);
      expect(plan.carbTarget.value, 300.0);
      expect(plan.fatTarget.value, 70.0);
      expect(plan.hydrationTarget.unit, 'ml');
    });

    test('dayTypeLabel retourne le bon label', () {
      final plan = AdaptiveNutritionPlan.fromJson(_planJson(dayType: 'rest'));
      expect(plan.dayTypeLabel, 'Repos');
    });

    test('isTrainingDay est vrai pour training', () {
      final plan = AdaptiveNutritionPlan.fromJson(_planJson());
      expect(plan.isTrainingDay, isTrue);
    });

    test('isTrainingDay est faux pour rest', () {
      final plan =
          AdaptiveNutritionPlan.fromJson(_planJson(dayType: 'rest'));
      expect(plan.isTrainingDay, isFalse);
    });

    test('fromJson parse fasting_compatible', () {
      final plan = AdaptiveNutritionPlan.fromJson(_planJson());
      expect(plan.fastingCompatible, isFalse);
    });

    test('fromJson parse supplementation_focus', () {
      final plan = AdaptiveNutritionPlan.fromJson(_planJson());
      expect(plan.supplementationFocus.length, 2);
      expect(plan.supplementationFocus, contains('Créatine'));
    });

    test('fromJson parse intense_training day_type', () {
      final plan = AdaptiveNutritionPlan.fromJson(
          _planJson(dayType: 'intense_training'));
      expect(plan.dayType, 'intense_training');
      expect(plan.isTrainingDay, isTrue);
    });

    test('fromJson gère champs manquants', () {
      expect(() => AdaptiveNutritionPlan.fromJson({}), returnsNormally);
    });
  });
}
