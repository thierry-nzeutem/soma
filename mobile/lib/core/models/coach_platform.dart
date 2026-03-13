/// SOMA LOT 17 — Coach Platform models.
///
/// Maps to endpoints in /api/v1/coach-platform/*
library;

import 'package:flutter/foundation.dart';

// ── AthleteAlert ──────────────────────────────────────────────────────────────

@immutable
class AthleteAlert {
  final String id;
  final String athleteId;
  final String alertType;
  final String severity; // critical | warning | info
  final String message;
  final String generatedAt;
  final bool isAcknowledged;
  final double? metricValue;
  final double? thresholdValue;

  const AthleteAlert({
    required this.id,
    required this.athleteId,
    required this.alertType,
    required this.severity,
    required this.message,
    required this.generatedAt,
    required this.isAcknowledged,
    this.metricValue,
    this.thresholdValue,
  });

  factory AthleteAlert.fromJson(Map<String, dynamic> json) {
    return AthleteAlert(
      id: json['id'] as String? ?? '',
      athleteId: json['athlete_id'] as String? ?? '',
      alertType: json['alert_type'] as String? ?? '',
      severity: json['severity'] as String? ?? 'info',
      message: json['message'] as String? ?? '',
      generatedAt: json['generated_at'] as String? ?? '',
      isAcknowledged: json['is_acknowledged'] as bool? ?? false,
      metricValue: (json['metric_value'] as num?)?.toDouble(),
      thresholdValue: (json['threshold_value'] as num?)?.toDouble(),
    );
  }

  /// Human-readable severity label (French).
  String get severityLabel => switch (severity) {
        'critical' => 'Critique',
        'warning' => 'Avertissement',
        'info' => 'Information',
        _ => severity,
      };

  /// Severity color for UI rendering.
  String get severityColor => switch (severity) {
        'critical' => '#FF3B30',
        'warning' => '#FF9500',
        'info' => '#34C759',
        _ => '#8E8E93',
      };

  /// Severity icon (emoji).
  String get severityIcon => switch (severity) {
        'critical' => '🔴',
        'warning' => '🟠',
        'info' => '🟢',
        _ => '⚪',
      };

  Map<String, dynamic> toJson() => {
        'id': id,
        'athlete_id': athleteId,
        'alert_type': alertType,
        'severity': severity,
        'message': message,
        'generated_at': generatedAt,
        'is_acknowledged': isAcknowledged,
        if (metricValue != null) 'metric_value': metricValue,
        if (thresholdValue != null) 'threshold_value': thresholdValue,
      };
}

// ── AthleteDashboardSummary ───────────────────────────────────────────────────

@immutable
class AthleteDashboardSummary {
  final String athleteId;
  final String athleteName;
  final String snapshotDate;
  final double? readinessScore;
  final double? fatigueScore;
  final double? injuryRiskScore;
  final double? biologicalAgeDelta;
  final double? movementHealthScore;
  final double? nutritionCompliance;
  final double? sleepQuality;
  final double? trainingLoadThisWeek;
  final double? acwr;
  final int? daysSinceLastSession;
  final List<String> activeAlerts;
  final String riskLevel; // green | yellow | orange | red

  const AthleteDashboardSummary({
    required this.athleteId,
    required this.athleteName,
    required this.snapshotDate,
    this.readinessScore,
    this.fatigueScore,
    this.injuryRiskScore,
    this.biologicalAgeDelta,
    this.movementHealthScore,
    this.nutritionCompliance,
    this.sleepQuality,
    this.trainingLoadThisWeek,
    this.acwr,
    this.daysSinceLastSession,
    required this.activeAlerts,
    required this.riskLevel,
  });

  factory AthleteDashboardSummary.fromJson(Map<String, dynamic> json) {
    return AthleteDashboardSummary(
      athleteId: json['athlete_id'] as String? ?? '',
      athleteName: json['athlete_name'] as String? ?? '',
      snapshotDate: json['snapshot_date'] as String? ?? '',
      readinessScore: (json['readiness_score'] as num?)?.toDouble(),
      fatigueScore: (json['fatigue_score'] as num?)?.toDouble(),
      injuryRiskScore: (json['injury_risk_score'] as num?)?.toDouble(),
      biologicalAgeDelta: (json['biological_age_delta'] as num?)?.toDouble(),
      movementHealthScore: (json['movement_health_score'] as num?)?.toDouble(),
      nutritionCompliance: (json['nutrition_compliance'] as num?)?.toDouble(),
      sleepQuality: (json['sleep_quality'] as num?)?.toDouble(),
      trainingLoadThisWeek:
          (json['training_load_this_week'] as num?)?.toDouble(),
      acwr: (json['acwr'] as num?)?.toDouble(),
      daysSinceLastSession: (json['days_since_last_session'] as num?)?.toInt(),
      activeAlerts: (json['active_alerts'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      riskLevel: json['risk_level'] as String? ?? 'green',
    );
  }

  bool get isAtRisk => riskLevel == 'orange' || riskLevel == 'red';
  bool get hasAlerts => activeAlerts.isNotEmpty;

  /// Risk level as French label with emoji.
  String get riskLevelLabel => switch (riskLevel) {
        'green' => '🟢 Vert',
        'yellow' => '🟡 Jaune',
        'orange' => '🟠 Orange',
        'red' => '🔴 Rouge',
        _ => riskLevel,
      };

  Map<String, dynamic> toJson() => {
        'athlete_id': athleteId,
        'athlete_name': athleteName,
        'snapshot_date': snapshotDate,
        if (readinessScore != null) 'readiness_score': readinessScore,
        if (fatigueScore != null) 'fatigue_score': fatigueScore,
        if (injuryRiskScore != null) 'injury_risk_score': injuryRiskScore,
        if (biologicalAgeDelta != null)
          'biological_age_delta': biologicalAgeDelta,
        if (movementHealthScore != null)
          'movement_health_score': movementHealthScore,
        if (nutritionCompliance != null)
          'nutrition_compliance': nutritionCompliance,
        if (sleepQuality != null) 'sleep_quality': sleepQuality,
        if (trainingLoadThisWeek != null)
          'training_load_this_week': trainingLoadThisWeek,
        if (acwr != null) 'acwr': acwr,
        if (daysSinceLastSession != null)
          'days_since_last_session': daysSinceLastSession,
        'active_alerts': activeAlerts,
        'risk_level': riskLevel,
      };
}

// ── CoachAthletesOverview ─────────────────────────────────────────────────────

@immutable
class CoachAthletesOverview {
  final String coachId;
  final int totalAthletes;
  final int athletesAtRisk;
  final List<AthleteDashboardSummary> athletesSummary;

  const CoachAthletesOverview({
    required this.coachId,
    required this.totalAthletes,
    required this.athletesAtRisk,
    required this.athletesSummary,
  });

  factory CoachAthletesOverview.fromJson(Map<String, dynamic> json) {
    return CoachAthletesOverview(
      coachId: json['coach_id'] as String? ?? '',
      totalAthletes: (json['total_athletes'] as num?)?.toInt() ?? 0,
      athletesAtRisk: (json['athletes_at_risk'] as num?)?.toInt() ?? 0,
      athletesSummary: (json['athletes_summary'] as List<dynamic>?)
              ?.map((e) =>
                  AthleteDashboardSummary.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() => {
        'coach_id': coachId,
        'total_athletes': totalAthletes,
        'athletes_at_risk': athletesAtRisk,
        'athletes_summary':
            athletesSummary.map((a) => a.toJson()).toList(),
      };
}

// ── CoachProfile ──────────────────────────────────────────────────────────────

@immutable
class CoachProfile {
  final String id;
  final String userId;
  final String name;
  final List<String> specializations;
  final String? certification;
  final String? bio;
  final int maxAthletes;
  final bool isActive;
  final int athleteCount;

  const CoachProfile({
    required this.id,
    required this.userId,
    required this.name,
    required this.specializations,
    this.certification,
    this.bio,
    required this.maxAthletes,
    required this.isActive,
    required this.athleteCount,
  });

  factory CoachProfile.fromJson(Map<String, dynamic> json) {
    return CoachProfile(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      specializations: (json['specializations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      certification: json['certification'] as String?,
      bio: json['bio'] as String?,
      maxAthletes: (json['max_athletes'] as num?)?.toInt() ?? 50,
      isActive: json['is_active'] as bool? ?? true,
      athleteCount: (json['athlete_count'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'name': name,
        'specializations': specializations,
        if (certification != null) 'certification': certification,
        if (bio != null) 'bio': bio,
        'max_athletes': maxAthletes,
        'is_active': isActive,
        'athlete_count': athleteCount,
      };
}

// ── CoachProfileCreate ────────────────────────────────────────────────────────

@immutable
class CoachProfileCreate {
  final String name;
  final List<String> specializations;
  final String? certification;
  final String? bio;
  final int maxAthletes;

  const CoachProfileCreate({
    required this.name,
    this.specializations = const [],
    this.certification,
    this.bio,
    this.maxAthletes = 50,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'specializations': specializations,
        if (certification != null) 'certification': certification,
        if (bio != null) 'bio': bio,
        'max_athletes': maxAthletes,
      };
}

// ── AthleteProfile ────────────────────────────────────────────────────────────

@immutable
class AthleteProfile {
  final String id;
  final String userId;
  final String displayName;
  final String? sport;
  final String? goal;
  final String? dateOfBirth;
  final String? notes;
  final bool isActive;

  const AthleteProfile({
    required this.id,
    required this.userId,
    required this.displayName,
    this.sport,
    this.goal,
    this.dateOfBirth,
    this.notes,
    required this.isActive,
  });

  factory AthleteProfile.fromJson(Map<String, dynamic> json) {
    return AthleteProfile(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      displayName: json['display_name'] as String? ?? '',
      sport: json['sport'] as String?,
      goal: json['goal'] as String?,
      dateOfBirth: json['date_of_birth'] as String?,
      notes: json['notes'] as String?,
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'display_name': displayName,
        if (sport != null) 'sport': sport,
        if (goal != null) 'goal': goal,
        if (dateOfBirth != null) 'date_of_birth': dateOfBirth,
        if (notes != null) 'notes': notes,
        'is_active': isActive,
      };
}

// ── AthleteCreate ─────────────────────────────────────────────────────────────

@immutable
class AthleteCreate {
  final String userId;
  final String displayName;
  final String? sport;
  final String? goal;
  final String? dateOfBirth;
  final String? notes;

  const AthleteCreate({
    required this.userId,
    required this.displayName,
    this.sport,
    this.goal,
    this.dateOfBirth,
    this.notes,
  });

  Map<String, dynamic> toJson() => {
        'user_id': userId,
        'display_name': displayName,
        if (sport != null) 'sport': sport,
        if (goal != null) 'goal': goal,
        if (dateOfBirth != null) 'date_of_birth': dateOfBirth,
        if (notes != null) 'notes': notes,
      };
}

// ── TrainingProgram ───────────────────────────────────────────────────────────

@immutable
class TrainingProgram {
  final String id;
  final String coachId;
  final String name;
  final String? description;
  final int durationWeeks;
  final String sportFocus;
  final String difficulty;
  final bool isTemplate;
  final List<Map<String, dynamic>> weeks;

  const TrainingProgram({
    required this.id,
    required this.coachId,
    required this.name,
    this.description,
    required this.durationWeeks,
    required this.sportFocus,
    required this.difficulty,
    required this.isTemplate,
    required this.weeks,
  });

  factory TrainingProgram.fromJson(Map<String, dynamic> json) {
    return TrainingProgram(
      id: json['id'] as String? ?? '',
      coachId: json['coach_id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      durationWeeks: (json['duration_weeks'] as num?)?.toInt() ?? 4,
      sportFocus: json['sport_focus'] as String? ?? '',
      difficulty: json['difficulty'] as String? ?? 'medium',
      isTemplate: json['is_template'] as bool? ?? false,
      weeks: (json['weeks'] as List<dynamic>?)
              ?.cast<Map<String, dynamic>>()
              .toList() ??
          [],
    );
  }

  String get difficultyLabel => switch (difficulty) {
        'easy' => 'Facile',
        'medium' => 'Moyen',
        'hard' => 'Difficile',
        'elite' => 'Élite',
        _ => difficulty,
      };

  Map<String, dynamic> toJson() => {
        'id': id,
        'coach_id': coachId,
        'name': name,
        if (description != null) 'description': description,
        'duration_weeks': durationWeeks,
        'sport_focus': sportFocus,
        'difficulty': difficulty,
        'is_template': isTemplate,
        'weeks': weeks,
      };
}

// ── AthleteNote ───────────────────────────────────────────────────────────────

@immutable
class AthleteNote {
  final String id;
  final String coachId;
  final String athleteId;
  final String noteDate;
  final String content;
  final String category; // general | nutrition | recovery | performance | injury | mental
  final bool isPrivate;

  const AthleteNote({
    required this.id,
    required this.coachId,
    required this.athleteId,
    required this.noteDate,
    required this.content,
    required this.category,
    required this.isPrivate,
  });

  factory AthleteNote.fromJson(Map<String, dynamic> json) {
    return AthleteNote(
      id: json['id'] as String? ?? '',
      coachId: json['coach_id'] as String? ?? '',
      athleteId: json['athlete_id'] as String? ?? '',
      noteDate: json['note_date'] as String? ?? '',
      content: json['content'] as String? ?? '',
      category: json['category'] as String? ?? 'general',
      isPrivate: json['is_private'] as bool? ?? true,
    );
  }

  String get categoryLabel => switch (category) {
        'general' => 'Général',
        'nutrition' => 'Nutrition',
        'recovery' => 'Récupération',
        'performance' => 'Performance',
        'injury' => 'Blessure',
        'mental' => 'Mental',
        _ => category,
      };

  Map<String, dynamic> toJson() => {
        'id': id,
        'coach_id': coachId,
        'athlete_id': athleteId,
        'note_date': noteDate,
        'content': content,
        'category': category,
        'is_private': isPrivate,
      };
}

// ── AthleteNoteCreate ─────────────────────────────────────────────────────────

@immutable
class AthleteNoteCreate {
  final String athleteId;
  final String content;
  final String category;
  final bool isPrivate;

  const AthleteNoteCreate({
    required this.athleteId,
    required this.content,
    this.category = 'general',
    this.isPrivate = true,
  });

  Map<String, dynamic> toJson() => {
        'athlete_id': athleteId,
        'content': content,
        'category': category,
        'is_private': isPrivate,
      };
}
