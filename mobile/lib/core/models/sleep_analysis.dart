/// Modeles d'analyse du sommeil — BATCH 6.
///
/// Classes Dart correspondant aux schemas Pydantic backend :
/// `SleepArchitectureResponse`, `SleepConsistencyResponse`,
/// `SleepProblemResponse`, `SleepAnalysisResponse`.
library;

// ── Architecture ────────────────────────────────────────────────────────────

class SleepArchitecture {
  final double deepPct;
  final double remPct;
  final double lightPct;
  final double awakePct;
  final int architectureScore;
  final String architectureQuality;
  final List<String> areasToImprove;

  const SleepArchitecture({
    required this.deepPct,
    required this.remPct,
    required this.lightPct,
    required this.awakePct,
    required this.architectureScore,
    required this.architectureQuality,
    required this.areasToImprove,
  });

  factory SleepArchitecture.fromJson(Map<String, dynamic> json) =>
      SleepArchitecture(
        deepPct: (json['deep_pct'] as num?)?.toDouble() ?? 0,
        remPct: (json['rem_pct'] as num?)?.toDouble() ?? 0,
        lightPct: (json['light_pct'] as num?)?.toDouble() ?? 0,
        awakePct: (json['awake_pct'] as num?)?.toDouble() ?? 0,
        architectureScore: (json['architecture_score'] as num?)?.toInt() ?? 0,
        architectureQuality:
            json['architecture_quality'] as String? ?? 'unknown',
        areasToImprove: (json['areas_to_improve'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );

  String get qualityLabel {
    switch (architectureQuality) {
      case 'excellent':
        return 'Excellent';
      case 'good':
        return 'Bon';
      case 'fair':
        return 'Correct';
      case 'poor':
        return 'Faible';
      case 'estimated_good':
        return 'Bon (estimé)';
      case 'estimated_fair':
        return 'Correct (estimé)';
      case 'estimated_poor':
        return 'Faible (estimé)';
      default:
        return 'Inconnu';
    }
  }
}

// ── Consistency ─────────────────────────────────────────────────────────────

class SleepConsistency {
  final double? avgBedtimeHour;
  final double? avgWakeHour;
  final double bedtimeVarianceMin;
  final double wakeVarianceMin;
  final int consistencyScore;
  final String consistencyLabel;
  final int sessionsAnalyzed;

  const SleepConsistency({
    this.avgBedtimeHour,
    this.avgWakeHour,
    required this.bedtimeVarianceMin,
    required this.wakeVarianceMin,
    required this.consistencyScore,
    required this.consistencyLabel,
    required this.sessionsAnalyzed,
  });

  factory SleepConsistency.fromJson(Map<String, dynamic> json) =>
      SleepConsistency(
        avgBedtimeHour: (json['avg_bedtime_hour'] as num?)?.toDouble(),
        avgWakeHour: (json['avg_wake_hour'] as num?)?.toDouble(),
        bedtimeVarianceMin:
            (json['bedtime_variance_min'] as num?)?.toDouble() ?? 0,
        wakeVarianceMin:
            (json['wake_variance_min'] as num?)?.toDouble() ?? 0,
        consistencyScore:
            (json['consistency_score'] as num?)?.toInt() ?? 0,
        consistencyLabel:
            json['consistency_label'] as String? ?? 'insufficient_data',
        sessionsAnalyzed:
            (json['sessions_analyzed'] as num?)?.toInt() ?? 0,
      );

  String get label {
    switch (consistencyLabel) {
      case 'excellent':
        return 'Excellent';
      case 'good':
        return 'Bon';
      case 'moderate':
        return 'Modéré';
      case 'poor':
        return 'Faible';
      case 'insufficient_data':
        return 'Données insuffisantes';
      default:
        return consistencyLabel;
    }
  }

  /// Formats an hour value (e.g. 23.5) as "23h30".
  String formatHour(double? h) {
    if (h == null) return '—';
    final hour = h.floor() % 24;
    final min = ((h - h.floor()) * 60).round();
    return '${hour}h${min.toString().padLeft(2, '0')}';
  }
}

// ── Problem ─────────────────────────────────────────────────────────────────

class SleepProblem {
  final String problemType;
  final String severity;
  final String description;
  final String recommendation;
  final int evidenceDays;

  const SleepProblem({
    required this.problemType,
    required this.severity,
    required this.description,
    required this.recommendation,
    required this.evidenceDays,
  });

  factory SleepProblem.fromJson(Map<String, dynamic> json) => SleepProblem(
        problemType: json['problem_type'] as String? ?? '',
        severity: json['severity'] as String? ?? 'low',
        description: json['description'] as String? ?? '',
        recommendation: json['recommendation'] as String? ?? '',
        evidenceDays: (json['evidence_days'] as num?)?.toInt() ?? 0,
      );

  String get typeLabel {
    switch (problemType) {
      case 'chronic_insufficient':
        return 'Sommeil insuffisant';
      case 'quality_degradation':
        return 'Qualité en baisse';
      case 'late_bedtime':
        return 'Coucher tardif';
      case 'fragmented_sleep':
        return 'Sommeil fragmenté';
      case 'insufficient_deep_sleep':
        return 'Sommeil profond insuffisant';
      default:
        return problemType;
    }
  }

  String get severityLabel {
    switch (severity) {
      case 'high':
        return 'Élevé';
      case 'moderate':
        return 'Modéré';
      case 'low':
        return 'Faible';
      default:
        return severity;
    }
  }
}

// ── Aggregate ───────────────────────────────────────────────────────────────

class SleepAnalysisResult {
  final SleepArchitecture? architecture;
  final SleepConsistency? consistency;
  final List<SleepProblem> problems;

  const SleepAnalysisResult({
    this.architecture,
    this.consistency,
    required this.problems,
  });

  factory SleepAnalysisResult.fromJson(Map<String, dynamic> json) =>
      SleepAnalysisResult(
        architecture: json['architecture'] != null
            ? SleepArchitecture.fromJson(
                json['architecture'] as Map<String, dynamic>)
            : null,
        consistency: json['consistency'] != null
            ? SleepConsistency.fromJson(
                json['consistency'] as Map<String, dynamic>)
            : null,
        problems: (json['problems'] as List<dynamic>?)
                ?.map((e) =>
                    SleepProblem.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
      );

  bool get hasData => architecture != null || consistency != null;
}
