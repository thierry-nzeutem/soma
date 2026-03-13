/// Tests modèle Motion Intelligence — SOMA LOT 11.
///
/// ~15 tests : parsing JSON, getters, edge cases.
import 'package:flutter_test/flutter_test.dart';
import 'package:soma_mobile/core/models/motion_intelligence.dart';

void main() {
  group('ExerciseMotionProfile', () {
    Map<String, dynamic> _profileJson({
      String qualityTrend = 'stable',
      double avgQuality = 72.0,
    }) =>
        {
          'exercise_type': 'squat',
          'sessions_analyzed': 5,
          'avg_stability': 68.0,
          'avg_amplitude': 75.0,
          'avg_quality': avgQuality,
          'stability_trend': 'improving',
          'amplitude_trend': 'stable',
          'quality_trend': qualityTrend,
          'quality_variance': 8.5,
          'last_session_date': '2026-03-07',
          'alerts': [],
        };

    test('fromJson parse tous les champs', () {
      final profile = ExerciseMotionProfile.fromJson(_profileJson());
      expect(profile.exerciseType, 'squat');
      expect(profile.sessionsAnalyzed, 5);
      expect(profile.avgStability, 68.0);
      expect(profile.avgAmplitude, 75.0);
      expect(profile.avgQuality, 72.0);
      expect(profile.stabilityTrend, 'improving');
      expect(profile.lastSessionDate, '2026-03-07');
    });

    test('fromJson valeurs par défaut si champs manquants', () {
      final profile = ExerciseMotionProfile.fromJson({});
      expect(profile.exerciseType, '');
      expect(profile.sessionsAnalyzed, 0);
      expect(profile.avgQuality, 0.0);
      expect(profile.stabilityTrend, 'stable');
      expect(profile.alerts, isEmpty);
    });

    test('trendLabel retourne ↑ pour improving', () {
      final profile =
          ExerciseMotionProfile.fromJson(_profileJson(qualityTrend: 'improving'));
      expect(profile.trendLabel, '↑');
    });

    test('trendLabel retourne ↓ pour declining', () {
      final profile =
          ExerciseMotionProfile.fromJson(_profileJson(qualityTrend: 'declining'));
      expect(profile.trendLabel, '↓');
    });

    test('trendLabel retourne → pour stable', () {
      final profile =
          ExerciseMotionProfile.fromJson(_profileJson(qualityTrend: 'stable'));
      expect(profile.trendLabel, '→');
    });

    test('exerciseDisplayName convertit underscores en espaces capitalisés', () {
      final profile = ExerciseMotionProfile.fromJson({
        ...ExerciseMotionProfile.fromJson(_profileJson()).toJson(),
        'exercise_type': 'jumping_jack',
      });
      expect(profile.exerciseDisplayName, 'Jumping Jack');
    });

    test('toJson round-trip', () {
      final profile = ExerciseMotionProfile.fromJson(_profileJson());
      final json = profile.toJson();
      final restored = ExerciseMotionProfile.fromJson(json);
      expect(restored.exerciseType, 'squat');
      expect(restored.avgQuality, 72.0);
    });
  });

  group('MotionIntelligenceResult', () {
    Map<String, dynamic> _resultJson({
      String trend = 'stable',
      double asymmetry = 15.0,
    }) =>
        {
          'analysis_date': '2026-03-08',
          'sessions_analyzed': 10,
          'days_analyzed': 30,
          'movement_health_score': 72.0,
          'stability_score': 68.0,
          'mobility_score': 75.0,
          'asymmetry_score': asymmetry,
          'overall_quality_trend': trend,
          'consecutive_quality_sessions': 3,
          'exercise_profiles': {
            'squat': {
              'exercise_type': 'squat',
              'sessions_analyzed': 5,
              'avg_stability': 68.0,
              'avg_amplitude': 75.0,
              'avg_quality': 72.0,
              'stability_trend': 'stable',
              'amplitude_trend': 'stable',
              'quality_trend': 'stable',
              'quality_variance': 5.0,
              'last_session_date': null,
              'alerts': [],
            }
          },
          'recommendations': ['Travaillez la symétrie'],
          'risk_alerts': [],
          'confidence': 0.5,
        };

    test('fromJson parse les champs globaux', () {
      final result = MotionIntelligenceResult.fromJson(_resultJson());
      expect(result.sessionsAnalyzed, 10);
      expect(result.movementHealthScore, 72.0);
      expect(result.stabilityScore, 68.0);
      expect(result.mobilityScore, 75.0);
      expect(result.asymmetryScore, 15.0);
      expect(result.confidence, 0.5);
    });

    test('fromJson parse exerciseProfiles', () {
      final result = MotionIntelligenceResult.fromJson(_resultJson());
      expect(result.exerciseProfiles.containsKey('squat'), isTrue);
      expect(result.exerciseProfiles['squat']!.avgQuality, 72.0);
    });

    test('trendLabel improving retourne ↑ Amélioration', () {
      final result =
          MotionIntelligenceResult.fromJson(_resultJson(trend: 'improving'));
      expect(result.trendLabel, '↑ Amélioration');
    });

    test('trendLabel declining retourne ↓ Déclin', () {
      final result =
          MotionIntelligenceResult.fromJson(_resultJson(trend: 'declining'));
      expect(result.trendLabel, '↓ Déclin');
    });

    test('trendLabel stable retourne → Stable', () {
      final result =
          MotionIntelligenceResult.fromJson(_resultJson(trend: 'stable'));
      expect(result.trendLabel, '→ Stable');
    });

    test('asymmetryRiskLevel Faible pour < 15', () {
      final result = MotionIntelligenceResult.fromJson(
          _resultJson(asymmetry: 10.0));
      expect(result.asymmetryRiskLevel, 'Faible');
    });

    test('asymmetryRiskLevel Modéré pour 15-35', () {
      final result = MotionIntelligenceResult.fromJson(
          _resultJson(asymmetry: 25.0));
      expect(result.asymmetryRiskLevel, 'Modéré');
    });

    test('asymmetryRiskLevel Élevé pour >= 35', () {
      final result = MotionIntelligenceResult.fromJson(
          _resultJson(asymmetry: 40.0));
      expect(result.asymmetryRiskLevel, 'Élevé');
    });

    test('fromJson parse les recommandations', () {
      final result = MotionIntelligenceResult.fromJson(_resultJson());
      expect(result.recommendations.length, 1);
    });

    test('fromJson gère champs manquants', () {
      expect(() => MotionIntelligenceResult.fromJson({}), returnsNormally);
    });

    test('fromJson exerciseProfiles vide si absent', () {
      final result = MotionIntelligenceResult.fromJson({});
      expect(result.exerciseProfiles, isEmpty);
    });
  });

  group('MotionHistoryItem', () {
    test('fromJson parse tous les champs', () {
      final json = {
        'snapshot_date': '2026-03-08',
        'movement_health_score': 72.0,
        'stability_score': 68.0,
        'mobility_score': 75.0,
        'asymmetry_score': 15.0,
        'overall_quality_trend': 'improving',
        'confidence': 0.5,
      };
      final item = MotionHistoryItem.fromJson(json);
      expect(item.snapshotDate, '2026-03-08');
      expect(item.movementHealthScore, 72.0);
      expect(item.overallQualityTrend, 'improving');
    });

    test('fromJson valeurs par défaut', () {
      final item = MotionHistoryItem.fromJson({});
      expect(item.snapshotDate, '');
      expect(item.movementHealthScore, 0.0);
      expect(item.overallQualityTrend, 'stable');
    });
  });
}
