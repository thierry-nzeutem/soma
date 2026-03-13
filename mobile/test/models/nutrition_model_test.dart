/// Tests parsing modèles Nutrition — LOT 6.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/nutrition.dart';

void main() {
  group('FoodItem', () {
    final json = {
      'id': 'f1',
      'name': 'Chicken breast',
      'name_fr': 'Poulet rôti',
      'calories_per_100g': 165.0,
      'protein_g_per_100g': 31.0,
      'carbs_g_per_100g': 0.0,
      'fat_g_per_100g': 3.6,
      'fiber_g_per_100g': 0.0,
      'food_group': 'Viandes',
      'source': 'ciqual',
    };

    test('fromJson parses all fields', () {
      final item = FoodItem.fromJson(json);
      expect(item.id, 'f1');
      expect(item.name, 'Chicken breast');
      expect(item.nameFr, 'Poulet rôti');
      expect(item.caloriesPer100g, 165.0);
      expect(item.proteinGPer100g, 31.0);
    });

    test('displayName returns nameFr when available', () {
      final item = FoodItem.fromJson(json);
      expect(item.displayName, 'Poulet rôti');
    });

    test('displayName falls back to name', () {
      final noFr = Map<String, dynamic>.from(json)..remove('name_fr');
      final item = FoodItem.fromJson(noFr);
      expect(item.displayName, 'Chicken breast');
    });

    test('calories() calculates for given quantity', () {
      final item = FoodItem.fromJson(json);
      expect(item.calories(200), closeTo(330.0, 0.1));
    });

    test('protein() calculates for given quantity', () {
      final item = FoodItem.fromJson(json);
      expect(item.protein(100), closeTo(31.0, 0.1));
    });
  });

  group('NutritionEntry', () {
    final json = {
      'id': 'e1',
      'logged_at': '2026-03-07T12:00:00Z',
      'meal_type': 'lunch',
      'meal_name': 'Salade césar',
      'calories': 450.0,
      'protein_g': 25.0,
      'carbs_g': 30.0,
      'fat_g': 20.0,
      'fiber_g': 5.0,
      'quantity_g': 350.0,
      'food_item_id': null,
      'food_item_name': null,
      'data_quality': 'manual',
      'notes': null,
    };

    test('fromJson parses correctly', () {
      final entry = NutritionEntry.fromJson(json);
      expect(entry.id, 'e1');
      expect(entry.mealType, 'lunch');
      expect(entry.calories, 450.0);
    });

    test('mealTypeLabel returns French label', () {
      final entry = NutritionEntry.fromJson(json);
      expect(entry.mealTypeLabel, 'Déjeuner');
    });

    test('mealTypeLabel for breakfast', () {
      final j = Map<String, dynamic>.from(json)..['meal_type'] = 'breakfast';
      expect(NutritionEntry.fromJson(j).mealTypeLabel, 'Petit-déjeuner');
    });

    test('mealTypeLabel for dinner', () {
      final j = Map<String, dynamic>.from(json)..['meal_type'] = 'dinner';
      expect(NutritionEntry.fromJson(j).mealTypeLabel, 'Dîner');
    });

    test('mealTypeLabel for snack', () {
      final j = Map<String, dynamic>.from(json)..['meal_type'] = 'snack';
      expect(NutritionEntry.fromJson(j).mealTypeLabel, 'En-cas');
    });

    test('data_quality defaults to estimated if missing', () {
      final j = Map<String, dynamic>.from(json)..remove('data_quality');
      expect(NutritionEntry.fromJson(j).dataQuality, 'estimated');
    });
  });

  group('MacroTotals', () {
    test('fromJson parses correctly', () {
      final json = {
        'calories': 2000.0,
        'protein_g': 150.0,
        'carbs_g': 200.0,
        'fat_g': 70.0,
        'fiber_g': 25.0,
      };
      final totals = MacroTotals.fromJson(json);
      expect(totals.calories, 2000.0);
      expect(totals.proteinG, 150.0);
    });

    test('fromJson defaults to 0 if null', () {
      final totals = MacroTotals.fromJson({});
      expect(totals.calories, 0.0);
      expect(totals.proteinG, 0.0);
    });
  });

  group('DailyNutritionSummary', () {
    final json = {
      'date': '2026-03-07',
      'meal_count': 3,
      'totals': {
        'calories': 1800.0,
        'protein_g': 120.0,
        'carbs_g': 200.0,
        'fat_g': 60.0,
        'fiber_g': 30.0,
      },
      'goals': {
        'calories_target': 2000.0,
        'protein_target_g': 150.0,
      },
      'meals': [],
      'data_completeness_pct': 75.0,
    };

    test('fromJson parses all fields', () {
      final s = DailyNutritionSummary.fromJson(json);
      expect(s.date, '2026-03-07');
      expect(s.mealCount, 3);
      expect(s.totals.calories, 1800.0);
      expect(s.goals.caloriesTarget, 2000.0);
    });

    test('caloriePct computed correctly', () {
      final s = DailyNutritionSummary.fromJson(json);
      expect(s.caloriePct, closeTo(90.0, 0.1));
    });

    test('proteinPct computed correctly', () {
      final s = DailyNutritionSummary.fromJson(json);
      expect(s.proteinPct, closeTo(80.0, 0.1));
    });

    test('caloriePct returns 0 if no target', () {
      final noTarget = Map<String, dynamic>.from(json)
        ..['goals'] = <String, dynamic>{};
      final s = DailyNutritionSummary.fromJson(noTarget);
      expect(s.caloriePct, 0.0);
    });
  });

  group('NutritionPhoto', () {
    test('isPending when status is analyzing', () {
      final photo = NutritionPhoto.fromJson({
        'photo_id': 'p1',
        'analysis_status': 'analyzing',
        'identified_foods': [],
      });
      expect(photo.isPending, isTrue);
      expect(photo.isAnalyzed, isFalse);
      expect(photo.isFailed, isFalse);
    });

    test('isAnalyzed when status is analyzed', () {
      final photo = NutritionPhoto.fromJson({
        'photo_id': 'p1',
        'analysis_status': 'analyzed',
        'identified_foods': [],
      });
      expect(photo.isAnalyzed, isTrue);
    });

    test('isFailed when status is failed', () {
      final photo = NutritionPhoto.fromJson({
        'photo_id': 'p1',
        'analysis_status': 'failed',
        'identified_foods': [],
      });
      expect(photo.isFailed, isTrue);
    });

    test('parses identified_foods list', () {
      final photo = NutritionPhoto.fromJson({
        'photo_id': 'p1',
        'analysis_status': 'analyzed',
        'identified_foods': [
          {'name': 'Salade', 'quantity_g': 150.0, 'calories_estimated': 20.0},
          {'name': 'Tomates', 'quantity_g': 100.0},
        ],
        'estimated_calories': 200.0,
      });
      expect(photo.identifiedFoods.length, 2);
      expect(photo.identifiedFoods[0].name, 'Salade');
      expect(photo.estimatedCalories, 200.0);
    });
  });
}
