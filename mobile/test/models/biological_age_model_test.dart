/// Tests modèle Biological Age — SOMA LOT 11.
///
/// ~15 tests : parsing JSON, getters, edge cases.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/biological_age.dart';

void main() {
  group('BiologicalAgeComponent', () {
    test('fromJson parse tous les champs', () {
      final json = {
        'factor_name': 'cardiovascular',
        'display_name': 'Cardiovasculaire',
        'score': 78.5,
        'weight': 0.20,
        'age_delta_years': -0.7,
        'explanation': 'Bonne condition cardio',
        'is_available': true,
      };
      final comp = BiologicalAgeComponent.fromJson(json);
      expect(comp.factorName, 'cardiovascular');
      expect(comp.displayName, 'Cardiovasculaire');
      expect(comp.score, 78.5);
      expect(comp.weight, 0.20);
      expect(comp.ageDeltaYears, -0.7);
      expect(comp.isAvailable, isTrue);
    });

    test('fromJson valeurs par défaut', () {
      final comp = BiologicalAgeComponent.fromJson({});
      expect(comp.factorName, '');
      expect(comp.score, 0.0);
      expect(comp.weight, 0.0);
      expect(comp.isAvailable, isFalse);
    });

    test('toJson round-trip', () {
      final comp = BiologicalAgeComponent(
        factorName: 'sleep',
        displayName: 'Sommeil',
        score: 82.0,
        weight: 0.15,
        ageDeltaYears: -1.05,
        explanation: 'Excellent sommeil',
        isAvailable: true,
      );
      final restored = BiologicalAgeComponent.fromJson(comp.toJson());
      expect(restored.factorName, 'sleep');
      expect(restored.score, 82.0);
    });
  });

  group('BiologicalAgeLever', () {
    Map<String, dynamic> _leverJson() => {
          'lever_id': 'improve_sleep',
          'title': 'Améliorer le sommeil',
          'description': 'Visez 7-9h de sommeil par nuit',
          'potential_years_gained': 2.1,
          'difficulty': 'moderate',
          'timeframe': 'weeks',
          'component': 'sleep',
        };

    test('fromJson parse tous les champs', () {
      final lever = BiologicalAgeLever.fromJson(_leverJson());
      expect(lever.leverId, 'improve_sleep');
      expect(lever.title, 'Améliorer le sommeil');
      expect(lever.potentialYearsGained, 2.1);
      expect(lever.difficulty, 'moderate');
      expect(lever.timeframe, 'weeks');
    });

    test('difficultyLabel retourne le bon label', () {
      for (final entry in {
        'easy': 'Facile',
        'moderate': 'Modéré',
        'hard': 'Difficile',
      }.entries) {
        final json = _leverJson();
        json['difficulty'] = entry.key;
        expect(BiologicalAgeLever.fromJson(json).difficultyLabel, entry.value);
      }
    });

    test('timeframeLabel retourne le bon label', () {
      for (final entry in {
        'weeks': 'Semaines',
        'months': 'Mois',
        'years': 'Années',
      }.entries) {
        final json = _leverJson();
        json['timeframe'] = entry.key;
        expect(BiologicalAgeLever.fromJson(json).timeframeLabel, entry.value);
      }
    });
  });

  group('BiologicalAgeResult', () {
    Map<String, dynamic> _resultJson({
      int chrono = 35,
      double bio = 32.0,
      double delta = -3.0,
      String trend = 'improving',
    }) =>
        {
          'chronological_age': chrono,
          'biological_age': bio,
          'biological_age_delta': delta,
          'longevity_risk_score': 25.0,
          'trend_direction': trend,
          'confidence': 0.75,
          'explanation': 'Bonne condition générale',
          'components': [],
          'levers': [],
        };

    test('fromJson parse les champs principaux', () {
      final result = BiologicalAgeResult.fromJson(_resultJson());
      expect(result.chronologicalAge, 35);
      expect(result.biologicalAge, 32.0);
      expect(result.biologicalAgeDelta, -3.0);
      expect(result.trendDirection, 'improving');
      expect(result.confidence, 0.75);
    });

    test('isYoungerThanChrono est vrai si delta négatif', () {
      final result = BiologicalAgeResult.fromJson(_resultJson(delta: -3.0));
      expect(result.isYoungerThanChrono, isTrue);
      expect(result.isOlderThanChrono, isFalse);
    });

    test('isOlderThanChrono est vrai si delta positif', () {
      final result = BiologicalAgeResult.fromJson(
          _resultJson(bio: 39.0, delta: 4.0));
      expect(result.isOlderThanChrono, isTrue);
      expect(result.isYoungerThanChrono, isFalse);
    });

    test('trendLabel retourne les bonnes flèches', () {
      expect(BiologicalAgeResult.fromJson(_resultJson(trend: 'improving'))
          .trendLabel, '↓ En amélioration');
      expect(BiologicalAgeResult.fromJson(_resultJson(trend: 'declining'))
          .trendLabel, '↑ En déclin');
      expect(BiologicalAgeResult.fromJson(_resultJson(trend: 'stable'))
          .trendLabel, '→ Stable');
    });

    test('deltaFormatted avec signe + pour delta positif', () {
      final result = BiologicalAgeResult.fromJson(
          _resultJson(bio: 39.0, delta: 4.0));
      expect(result.deltaFormatted, startsWith('+'));
    });

    test('deltaFormatted avec signe − pour delta négatif', () {
      final result = BiologicalAgeResult.fromJson(_resultJson(delta: -3.0));
      expect(result.deltaFormatted, startsWith('−'));
    });

    test('fromJson parse les composantes', () {
      final json = _resultJson();
      json['components'] = [
        {
          'factor_name': 'sleep',
          'display_name': 'Sommeil',
          'score': 82.0,
          'weight': 0.15,
          'age_delta_years': -1.05,
          'explanation': '',
          'is_available': true,
        }
      ];
      final result = BiologicalAgeResult.fromJson(json);
      expect(result.components.length, 1);
      expect(result.components[0].factorName, 'sleep');
    });

    test('fromJson gère champs manquants', () {
      expect(() => BiologicalAgeResult.fromJson({}), returnsNormally);
    });
  });
}
