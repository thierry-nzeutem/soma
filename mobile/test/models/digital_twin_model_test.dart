/// Tests modèle Digital Twin — SOMA LOT 11.
///
/// ~20 tests : parsing JSON, valeurs par défaut, edge cases.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/digital_twin.dart';

void main() {
  group('TwinComponent', () {
    test('fromJson parse tous les champs', () {
      final json = {
        'value': 75.5,
        'status': 'good',
        'confidence': 0.85,
        'explanation': 'Bonne récupération',
        'variables_used': ['sleep_duration', 'fatigue'],
      };
      final comp = TwinComponent.fromJson(json);
      expect(comp.value, 75.5);
      expect(comp.status, 'good');
      expect(comp.confidence, 0.85);
      expect(comp.explanation, 'Bonne récupération');
      expect(comp.variablesUsed, ['sleep_duration', 'fatigue']);
    });

    test('fromJson valeurs par défaut si champs manquants', () {
      final comp = TwinComponent.fromJson({});
      expect(comp.value, 0.0);
      expect(comp.status, 'unknown');
      expect(comp.confidence, 0.0);
      expect(comp.explanation, '');
      expect(comp.variablesUsed, isEmpty);
    });

    test('toJson round-trip', () {
      final comp = TwinComponent(
        value: 42.0,
        status: 'moderate',
        confidence: 0.6,
        explanation: 'Test',
        variablesUsed: ['var1'],
      );
      final json = comp.toJson();
      final restored = TwinComponent.fromJson(json);
      expect(restored.value, 42.0);
      expect(restored.status, 'moderate');
    });
  });

  group('DigitalTwinState', () {
    Map<String, dynamic> _componentJson({
      double value = 50.0,
      String status = 'moderate',
      double confidence = 0.7,
    }) =>
        {
          'value': value,
          'status': status,
          'confidence': confidence,
          'explanation': '',
          'variables_used': [],
        };

    Map<String, dynamic> _fullJson() => {
          'snapshot_date': '2026-03-08',
          'overall_status': 'good',
          'primary_concern': '',
          'global_confidence': 0.8,
          'plateau_risk': false,
          'under_recovery_risk': false,
          'recommendations': ['Boire plus d\'eau'],
          'energy_balance': _componentJson(value: -200, status: 'moderate'),
          'glycogen': _componentJson(value: 280, status: 'normal'),
          'carb_availability': _componentJson(status: 'normal'),
          'protein_status': _componentJson(status: 'good'),
          'hydration': _componentJson(status: 'good'),
          'fatigue': _componentJson(value: 35, status: 'low'),
          'sleep_debt': _componentJson(value: 20, status: 'low'),
          'inflammation': _componentJson(value: 25, status: 'low'),
          'recovery_capacity': _componentJson(value: 75, status: 'good'),
          'training_readiness': _componentJson(value: 80, status: 'good'),
          'stress_load': _componentJson(value: 30, status: 'low'),
          'metabolic_flexibility': _componentJson(value: 65, status: 'moderate'),
        };

    test('fromJson parse le statut global', () {
      final twin = DigitalTwinState.fromJson(_fullJson());
      expect(twin.overallStatus, 'good');
      expect(twin.globalConfidence, 0.8);
    });

    test('fromJson parse les TwinComponents', () {
      final twin = DigitalTwinState.fromJson(_fullJson());
      expect(twin.fatigue.value, 35.0);
      expect(twin.fatigue.status, 'low');
      expect(twin.glycogen.value, 280.0);
      expect(twin.trainingReadiness.value, 80.0);
    });

    test('fromJson parse plateau_risk et under_recovery_risk', () {
      final json = _fullJson();
      json['plateau_risk'] = true;
      json['under_recovery_risk'] = true;
      final twin = DigitalTwinState.fromJson(json);
      expect(twin.plateauRisk, isTrue);
      expect(twin.underRecoveryRisk, isTrue);
    });

    test('fromJson parse les recommandations', () {
      final twin = DigitalTwinState.fromJson(_fullJson());
      expect(twin.recommendations.length, 1);
      expect(twin.recommendations[0], 'Boire plus d\'eau');
    });

    test('overallStatusLabel retourne le bon label', () {
      for (final entry in {
        'fresh': 'Frais',
        'good': 'Bon',
        'moderate': 'Modéré',
        'tired': 'Fatigué',
        'critical': 'Critique',
      }.entries) {
        final json = _fullJson();
        json['overall_status'] = entry.key;
        final twin = DigitalTwinState.fromJson(json);
        expect(twin.overallStatusLabel, entry.value);
      }
    });

    test('fromJson gère les champs manquants sans exception', () {
      expect(() => DigitalTwinState.fromJson({}), returnsNormally);
    });

    test('toJson round-trip preserves overall_status', () {
      final twin = DigitalTwinState.fromJson(_fullJson());
      final json = twin.toJson();
      expect(json['overall_status'], 'good');
      expect(json['global_confidence'], 0.8);
    });
  });

  group('DigitalTwinHistory', () {
    test('fromJson parse la liste d\'items', () {
      final json = {
        'snapshots': [
          {
            'snapshot_date': '2026-03-07',
            'overall_status': 'good',
            'global_confidence': 0.7,
            'training_readiness': 75.0,
            'fatigue': 40.0,
            'plateau_risk': false,
          },
          {
            'snapshot_date': '2026-03-06',
            'overall_status': 'tired',
            'global_confidence': 0.6,
            'training_readiness': 50.0,
            'fatigue': 70.0,
            'plateau_risk': false,
          },
        ],
        'total_count': 2,
      };
      final history = DigitalTwinHistory.fromJson(json);
      expect(history.snapshots.length, 2);
      expect(history.snapshots[0].overallStatus, 'good');
      expect(history.snapshots[1].overallStatus, 'tired');
    });

    test('fromJson liste vide si snapshots absent', () {
      final history = DigitalTwinHistory.fromJson({});
      expect(history.snapshots, isEmpty);
    });
  });

  group('DigitalTwinHistoryItem', () {
    test('fromJson parse tous les champs', () {
      final json = {
        'snapshot_date': '2026-03-08',
        'overall_status': 'fresh',
        'global_confidence': 0.9,
        'training_readiness': 90.0,
        'fatigue': 15.0,
        'plateau_risk': false,
      };
      final item = DigitalTwinHistoryItem.fromJson(json);
      expect(item.snapshotDate, '2026-03-08');
      expect(item.overallStatus, 'fresh');
      expect(item.trainingReadiness, 90.0);
      expect(item.fatigue, 15.0);
      expect(item.plateauRisk, isFalse);
    });

    test('fromJson valeurs par défaut', () {
      final item = DigitalTwinHistoryItem.fromJson({});
      expect(item.snapshotDate, '');
      expect(item.overallStatus, 'moderate');
      expect(item.globalConfidence, 0.0);
    });
  });
}
