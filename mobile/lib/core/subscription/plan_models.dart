// Plan codes and feature codes matching the backend exactly.
// ASCII-only strings to match backend FeatureCode enum values.

class PlanCode {
  static const String free = 'free';
  static const String ai = 'ai';
  static const String performance = 'performance';

  static String displayName(String code) {
    switch (code) {
      case ai:
        return 'SOMA AI';
      case performance:
        return 'SOMA Performance';
      default:
        return 'SOMA Free';
    }
  }

  static int rank(String code) {
    switch (code) {
      case ai:
        return 2;
      case performance:
        return 3;
      default:
        return 1;
    }
  }
}

class FeatureCode {
  // Free tier
  static const String basicDashboard = 'basic_dashboard';
  static const String basicHealthMetrics = 'basic_health_metrics';
  static const String localAiTips = 'local_ai_tips';

  // AI tier
  static const String aiCoach = 'ai_coach';
  static const String dailyBriefing = 'daily_briefing';
  static const String advancedInsights = 'advanced_insights';
  static const String pdfReports = 'pdf_reports';
  static const String anomalyDetection = 'anomaly_detection';
  static const String biologicalAge = 'biological_age';

  // Performance tier
  static const String readinessScore = 'readiness_score';
  static const String injuryPrediction = 'injury_prediction';
  static const String biomechanicsVision = 'biomechanics_vision';
  static const String advancedVo2max = 'advanced_vo2max';
  static const String trainingLoad = 'training_load';

  /// Returns the minimum plan required to access a feature.
  static String requiredPlan(String featureCode) {
    const performanceFeatures = {
      readinessScore,
      injuryPrediction,
      biomechanicsVision,
      advancedVo2max,
      trainingLoad,
    };
    const aiFeatures = {
      aiCoach,
      dailyBriefing,
      advancedInsights,
      pdfReports,
      anomalyDetection,
      biologicalAge,
    };
    if (performanceFeatures.contains(featureCode)) {
      return PlanCode.performance;
    }
    if (aiFeatures.contains(featureCode)) {
      return PlanCode.ai;
    }
    return PlanCode.free;
  }
}

class EntitlementsData {
  final String planCode;
  final String planStatus;
  final List<String> features;
  final bool isTrial;
  final bool isExpired;

  const EntitlementsData({
    required this.planCode,
    required this.planStatus,
    required this.features,
    this.isTrial = false,
    this.isExpired = false,
  });

  bool hasFeature(String featureCode) => features.contains(featureCode);

  bool get isFree => planCode == PlanCode.free;
  bool get isAi => planCode == PlanCode.ai || planCode == PlanCode.performance;
  bool get isPerformance => planCode == PlanCode.performance;

  String get planDisplayName => PlanCode.displayName(planCode);

  factory EntitlementsData.fromJson(Map<String, dynamic> json) {
    return EntitlementsData(
      planCode: json['plan_code'] as String? ?? PlanCode.free,
      planStatus: json['plan_status'] as String? ?? 'active',
      features: List<String>.from(json['features'] as List? ?? []),
      isTrial: json['is_trial'] as bool? ?? false,
      isExpired: json['is_expired'] as bool? ?? false,
    );
  }

  /// Default free entitlements for unauthenticated or error state.
  factory EntitlementsData.free() {
    return const EntitlementsData(
      planCode: PlanCode.free,
      planStatus: 'active',
      features: [
        FeatureCode.basicDashboard,
        FeatureCode.basicHealthMetrics,
        FeatureCode.localAiTips,
      ],
    );
  }
}
