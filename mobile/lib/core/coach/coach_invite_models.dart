/// Coach invitation and recommendation models.
library;

import 'package:flutter/foundation.dart';

// ── Invitation ────────────────────────────────────────────────────────────────

@immutable
class CoachInvitation {
  final String id;
  final String coachProfileId;
  final String inviteCode;
  final String inviteToken;
  final String inviteLink;
  final String? inviteeEmail;
  final String status; // pending | accepted | expired | cancelled
  final String? message;
  final DateTime expiresAt;
  final DateTime? acceptedAt;
  final DateTime createdAt;

  const CoachInvitation({
    required this.id,
    required this.coachProfileId,
    required this.inviteCode,
    required this.inviteToken,
    required this.inviteLink,
    this.inviteeEmail,
    required this.status,
    this.message,
    required this.expiresAt,
    this.acceptedAt,
    required this.createdAt,
  });

  factory CoachInvitation.fromJson(Map<String, dynamic> json) {
    return CoachInvitation(
      id: json['id'] as String,
      coachProfileId: json['coach_profile_id'] as String,
      inviteCode: json['invite_code'] as String,
      inviteToken: json['invite_token'] as String,
      inviteLink: json['invite_link'] as String,
      inviteeEmail: json['invitee_email'] as String?,
      status: json['status'] as String,
      message: json['message'] as String?,
      expiresAt: DateTime.parse(json['expires_at'] as String),
      acceptedAt: json['accepted_at'] != null
          ? DateTime.parse(json['accepted_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  bool get isPending => status == 'pending';
  bool get isExpired => status == 'expired' || expiresAt.isBefore(DateTime.now());
  bool get isAccepted => status == 'accepted';
}

// ── Recommendation ─────────────────────────────────────────────────────────

@immutable
class CoachRecommendation {
  final String id;
  final String coachId;
  final String athleteId;
  final String recType; // training|nutrition|recovery|medical|lifestyle|mental|general
  final String priority; // low|normal|high|urgent
  final String status; // pending|in_progress|completed|dismissed
  final String title;
  final String description;
  final DateTime? targetDate;
  final DateTime? completedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  const CoachRecommendation({
    required this.id,
    required this.coachId,
    required this.athleteId,
    required this.recType,
    required this.priority,
    required this.status,
    required this.title,
    required this.description,
    this.targetDate,
    this.completedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CoachRecommendation.fromJson(Map<String, dynamic> json) {
    return CoachRecommendation(
      id: json['id'] as String,
      coachId: json['coach_id'] as String,
      athleteId: json['athlete_id'] as String,
      recType: json['rec_type'] as String,
      priority: json['priority'] as String,
      status: json['status'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      targetDate: json['target_date'] != null
          ? DateTime.parse(json['target_date'] as String)
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  bool get isPending => status == 'pending';
  bool get isCompleted => status == 'completed';
  bool get isUrgent => priority == 'urgent';
}

// ── Link Status ────────────────────────────────────────────────────────────

@immutable
class LinkStatus {
  final String athleteId;
  final String coachId;
  final String status;
  final String? relationshipNotes;
  final DateTime? linkedAt;

  const LinkStatus({
    required this.athleteId,
    required this.coachId,
    required this.status,
    this.relationshipNotes,
    this.linkedAt,
  });

  factory LinkStatus.fromJson(Map<String, dynamic> json) {
    return LinkStatus(
      athleteId: json['athlete_id'] as String,
      coachId: json['coach_id'] as String,
      status: json['status'] as String,
      relationshipNotes: json['relationship_notes'] as String?,
      linkedAt: json['linked_at'] != null
          ? DateTime.parse(json['linked_at'] as String)
          : null,
    );
  }
}

// ── Full Athlete Profile ───────────────────────────────────────────────────

@immutable
class AthleteFullProfile {
  final String athleteProfileId;
  final String userId;
  final String displayName;
  final String? sport;
  final String? goal;
  final DateTime? dateOfBirth;
  final String? firstName;
  final int? age;
  final String? sex;
  final double? heightCm;
  final String? activityLevel;
  final String? fitnessLevel;
  final String linkStatus;
  final DateTime? linkedAt;
  final String? relationshipNotes;
  final int recentNotesCount;
  final int pendingRecommendationsCount;

  const AthleteFullProfile({
    required this.athleteProfileId,
    required this.userId,
    required this.displayName,
    this.sport,
    this.goal,
    this.dateOfBirth,
    this.firstName,
    this.age,
    this.sex,
    this.heightCm,
    this.activityLevel,
    this.fitnessLevel,
    required this.linkStatus,
    this.linkedAt,
    this.relationshipNotes,
    required this.recentNotesCount,
    required this.pendingRecommendationsCount,
  });

  factory AthleteFullProfile.fromJson(Map<String, dynamic> json) {
    return AthleteFullProfile(
      athleteProfileId: json['athlete_profile_id'] as String,
      userId: json['user_id'] as String,
      displayName: json['display_name'] as String,
      sport: json['sport'] as String?,
      goal: json['goal'] as String?,
      dateOfBirth: json['date_of_birth'] != null
          ? DateTime.parse(json['date_of_birth'] as String)
          : null,
      firstName: json['first_name'] as String?,
      age: json['age'] as int?,
      sex: json['sex'] as String?,
      heightCm: (json['height_cm'] as num?)?.toDouble(),
      activityLevel: json['activity_level'] as String?,
      fitnessLevel: json['fitness_level'] as String?,
      linkStatus: json['link_status'] as String,
      linkedAt: json['linked_at'] != null
          ? DateTime.parse(json['linked_at'] as String)
          : null,
      relationshipNotes: json['relationship_notes'] as String?,
      recentNotesCount: json['recent_notes_count'] as int,
      pendingRecommendationsCount: json['pending_recommendations_count'] as int,
    );
  }

  String get displayAge {
    if (age != null) return '$age ans';
    if (dateOfBirth != null) {
      final now = DateTime.now();
      final calculated = now.year - dateOfBirth!.year -
          (now.month < dateOfBirth!.month ||
                  (now.month == dateOfBirth!.month && now.day < dateOfBirth!.day)
              ? 1
              : 0);
      return '$calculated ans';
    }
    return '';
  }
}
