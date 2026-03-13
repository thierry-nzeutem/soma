/// SOMA LOT 16 — Biomarker models.
///
/// Maps to: GET /api/v1/labs/analysis
import 'package:flutter/foundation.dart';

@immutable
class BiomarkerMarker {
  final String markerName;
  final double value;
  final String unit;
  final String status;
  final double score;
  final double deviationPct;
  final String interpretation;
  final List<String> recommendations;

  const BiomarkerMarker({
    required this.markerName,
    required this.value,
    required this.unit,
    required this.status,
    required this.score,
    required this.deviationPct,
    required this.interpretation,
    required this.recommendations,
  });

  factory BiomarkerMarker.fromJson(Map<String, dynamic> json) {
    return BiomarkerMarker(
      markerName: json['marker_name'] as String? ?? '',
      value: (json['value'] as num?)?.toDouble() ?? 0.0,
      unit: json['unit'] as String? ?? '',
      status: json['status'] as String? ?? 'unknown',
      score: (json['score'] as num?)?.toDouble() ?? 50.0,
      deviationPct: (json['deviation_pct'] as num?)?.toDouble() ?? 0.0,
      interpretation: json['interpretation'] as String? ?? '',
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  bool get isOptimal => status == 'optimal';
  bool get isCritical => status == 'toxic' || status == 'deficient';

  String get statusLabel => switch (status) {
        'optimal' => 'Optimal',
        'adequate' => 'Correct',
        'suboptimal' => 'Suboptimal',
        'deficient' => 'Carence',
        'elevated' => 'Élevé',
        'toxic' => 'Toxique',
        _ => status,
      };

  String get displayName => switch (markerName) {
        'vitamin_d' => 'Vitamine D',
        'ferritin' => 'Ferritine',
        'crp' => 'CRP',
        'testosterone_total' => 'Testostérone',
        'hba1c' => 'HbA1c',
        'fasting_glucose' => 'Glycémie jeûne',
        'cholesterol_total' => 'Cholestérol total',
        'hdl' => 'HDL',
        'ldl' => 'LDL',
        'triglycerides' => 'Triglycérides',
        'cortisol' => 'Cortisol',
        'homocysteine' => 'Homocystéine',
        'magnesium' => 'Magnésium',
        'omega3_index' => 'Index Oméga-3',
        _ => markerName,
      };
}

@immutable
class BiomarkerAnalysis {
  final String analysisDate;
  final double metabolicHealthScore;
  final double inflammationScore;
  final double cardiovascularRisk;
  final double longevityModifier;
  final int markersAnalyzed;
  final int optimalMarkers;
  final int suboptimalMarkers;
  final List<String> deficientMarkers;
  final List<String> elevatedMarkers;
  final List<String> priorityActions;
  final List<String> supplementationRecommendations;
  final List<String> dietaryRecommendations;
  final double confidence;
  final List<BiomarkerMarker> markerAnalyses;

  const BiomarkerAnalysis({
    required this.analysisDate,
    required this.metabolicHealthScore,
    required this.inflammationScore,
    required this.cardiovascularRisk,
    required this.longevityModifier,
    required this.markersAnalyzed,
    required this.optimalMarkers,
    required this.suboptimalMarkers,
    required this.deficientMarkers,
    required this.elevatedMarkers,
    required this.priorityActions,
    required this.supplementationRecommendations,
    required this.dietaryRecommendations,
    required this.confidence,
    required this.markerAnalyses,
  });

  factory BiomarkerAnalysis.fromJson(Map<String, dynamic> json) {
    return BiomarkerAnalysis(
      analysisDate: json['analysis_date'] as String? ?? '',
      metabolicHealthScore: (json['metabolic_health_score'] as num?)?.toDouble() ?? 70.0,
      inflammationScore: (json['inflammation_score'] as num?)?.toDouble() ?? 20.0,
      cardiovascularRisk: (json['cardiovascular_risk'] as num?)?.toDouble() ?? 25.0,
      longevityModifier: (json['longevity_modifier'] as num?)?.toDouble() ?? 0.0,
      markersAnalyzed: (json['markers_analyzed'] as num?)?.toInt() ?? 0,
      optimalMarkers: (json['optimal_markers'] as num?)?.toInt() ?? 0,
      suboptimalMarkers: (json['suboptimal_markers'] as num?)?.toInt() ?? 0,
      deficientMarkers: (json['deficient_markers'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      elevatedMarkers: (json['elevated_markers'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      priorityActions: (json['priority_actions'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      supplementationRecommendations: (json['supplementation_recommendations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      dietaryRecommendations: (json['dietary_recommendations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      markerAnalyses: (json['marker_analyses'] as List<dynamic>?)
              ?.map((e) => BiomarkerMarker.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  bool get hasCriticalMarkers =>
      deficientMarkers.isNotEmpty || elevatedMarkers.isNotEmpty;

  String get longevityModifierLabel {
    final sign = longevityModifier >= 0 ? '+' : '';
    return '$sign${longevityModifier.toStringAsFixed(1)} ans';
  }
}

@immutable
class LabResultCreate {
  final String markerName;
  final double value;
  final String unit;
  final String labDate;
  final String source;

  const LabResultCreate({
    required this.markerName,
    required this.value,
    required this.unit,
    required this.labDate,
    this.source = 'manual',
  });

  Map<String, dynamic> toJson() => {
        'marker_name': markerName,
        'value': value,
        'unit': unit,
        'lab_date': labDate,
        'source': source,
      };
}
