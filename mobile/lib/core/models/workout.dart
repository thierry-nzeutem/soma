/// Modèles Workout — SOMA LOT 6.
///
/// ExerciseLibrary, WorkoutSet, ExerciseEntry, WorkoutSession.
library;

// ── Bibliothèque d'exercices ──────────────────────────────────────────────────

class ExerciseLibrary {
  final String id;
  final String name;
  final String? nameFr;
  final String category;
  final String? subcategory;
  final List<String> muscleGroups;
  final List<String> equipmentNeeded;
  final String difficultyLevel;
  final String? description;

  const ExerciseLibrary({
    required this.id,
    required this.name,
    this.nameFr,
    required this.category,
    this.subcategory,
    required this.muscleGroups,
    required this.equipmentNeeded,
    required this.difficultyLevel,
    this.description,
  });

  factory ExerciseLibrary.fromJson(Map<String, dynamic> json) =>
      ExerciseLibrary(
        id: json['id'] as String,
        name: json['name'] as String,
        nameFr: json['name_fr'] as String?,
        category: json['category'] as String? ?? 'other',
        subcategory: json['subcategory'] as String?,
        muscleGroups:
            (json['muscle_groups'] as List<dynamic>? ?? []).cast<String>(),
        equipmentNeeded:
            (json['equipment_needed'] as List<dynamic>? ?? []).cast<String>(),
        difficultyLevel:
            json['difficulty_level'] as String? ?? 'intermediate',
        description: json['description'] as String?,
      );

  String get displayName => nameFr ?? name;

  String get categoryLabel {
    switch (category) {
      case 'strength':
        return 'Force';
      case 'cardio':
        return 'Cardio';
      case 'hiit':
        return 'HIIT';
      case 'yoga':
        return 'Yoga';
      case 'mobility':
        return 'Mobilité';
      case 'core':
        return 'Gainage';
      default:
        return category;
    }
  }
}

// ── Série ─────────────────────────────────────────────────────────────────────

class WorkoutSet {
  final String id;
  final int setNumber;
  final String setType; // warmup|working|dropset|amrap|failure
  final int? repsTarget;
  final int? repsActual;
  final double? weightKg;
  final int? durationSeconds;
  final double? rpeSet;
  final bool isPr;
  final bool isDeleted;

  const WorkoutSet({
    required this.id,
    required this.setNumber,
    required this.setType,
    this.repsTarget,
    this.repsActual,
    this.weightKg,
    this.durationSeconds,
    this.rpeSet,
    this.isPr = false,
    this.isDeleted = false,
  });

  factory WorkoutSet.fromJson(Map<String, dynamic> json) => WorkoutSet(
        id: json['id'] as String,
        setNumber: json['set_number'] as int,
        setType: json['set_type'] as String? ?? 'working',
        repsTarget: json['reps_target'] as int?,
        repsActual: json['reps_actual'] as int?,
        weightKg: (json['weight_kg'] as num?)?.toDouble(),
        durationSeconds: json['duration_seconds'] as int?,
        rpeSet: (json['rpe_set'] as num?)?.toDouble(),
        isPr: json['is_pr'] as bool? ?? false,
        isDeleted: json['is_deleted'] as bool? ?? false,
      );

  String get display {
    final reps = repsActual ?? repsTarget;
    final weight = weightKg != null
        ? ' × ${weightKg!.toStringAsFixed(weightKg! == weightKg!.roundToDouble() ? 0 : 1)} kg'
        : '';
    if (reps != null) return '$reps reps$weight';
    if (durationSeconds != null) return '${durationSeconds}s$weight';
    return 'Set $setNumber';
  }
}

// ── Exercice dans une séance ──────────────────────────────────────────────────

class ExerciseEntry {
  final String id;
  final String exerciseId;
  final String exerciseName;
  final int exerciseOrder;
  final List<WorkoutSet> sets;
  final double tonnage;
  final int totalSets;
  final int totalReps;

  const ExerciseEntry({
    required this.id,
    required this.exerciseId,
    required this.exerciseName,
    required this.exerciseOrder,
    required this.sets,
    required this.tonnage,
    required this.totalSets,
    required this.totalReps,
  });

  factory ExerciseEntry.fromJson(Map<String, dynamic> json) {
    final setsRaw = json['sets'] as List<dynamic>? ?? [];
    return ExerciseEntry(
      id: json['id'] as String,
      exerciseId: json['exercise_id'] as String,
      exerciseName:
          json['exercise_name'] as String? ?? json['exercise_id'] as String,
      exerciseOrder: json['exercise_order'] as int? ?? 0,
      sets: setsRaw
          .map((s) => WorkoutSet.fromJson(s as Map<String, dynamic>))
          .where((s) => !s.isDeleted)
          .toList(),
      tonnage: (json['tonnage'] as num?)?.toDouble() ?? 0,
      totalSets: json['total_sets'] as int? ?? 0,
      totalReps: json['total_reps'] as int? ?? 0,
    );
  }
}

// ── Séance ────────────────────────────────────────────────────────────────────

class WorkoutSession {
  final String id;
  final String sessionType;
  final String location;
  final String status;
  final String startedAt;
  final String? endedAt;
  final int? durationMinutes;
  final int? rpeScore;
  final String? notes;
  final double? totalTonnageKg;
  final int? totalSets;
  final int? totalReps;
  final double? trainingLoad;
  final List<ExerciseEntry> exercises;

  const WorkoutSession({
    required this.id,
    required this.sessionType,
    required this.location,
    required this.status,
    required this.startedAt,
    this.endedAt,
    this.durationMinutes,
    this.rpeScore,
    this.notes,
    this.totalTonnageKg,
    this.totalSets,
    this.totalReps,
    this.trainingLoad,
    this.exercises = const [],
  });

  factory WorkoutSession.fromJson(Map<String, dynamic> json) {
    final exercisesRaw = json['exercises'] as List<dynamic>? ?? [];
    return WorkoutSession(
      id: json['id'] as String,
      sessionType: json['session_type'] as String,
      location: json['location'] as String? ?? 'gym',
      status: json['status'] as String? ?? 'planned',
      startedAt: json['started_at'] as String,
      endedAt: json['ended_at'] as String?,
      durationMinutes: json['duration_minutes'] as int?,
      rpeScore: json['rpe_score'] as int?,
      notes: json['notes'] as String?,
      totalTonnageKg: (json['total_tonnage_kg'] as num?)?.toDouble(),
      totalSets: json['total_sets'] as int?,
      totalReps: json['total_reps'] as int?,
      trainingLoad: (json['training_load'] as num?)?.toDouble(),
      exercises: exercisesRaw
          .map((e) => ExerciseEntry.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  String get typeLabel {
    switch (sessionType) {
      case 'strength':
        return 'Force';
      case 'cardio':
        return 'Cardio';
      case 'hiit':
        return 'HIIT';
      case 'yoga':
        return 'Yoga';
      case 'mobility':
        return 'Mobilité';
      case 'sport':
        return 'Sport';
      default:
        return 'Autre';
    }
  }

  String get statusLabel {
    switch (status) {
      case 'planned':
        return 'Planifiée';
      case 'in_progress':
        return 'En cours';
      case 'completed':
        return 'Terminée';
      case 'cancelled':
        return 'Annulée';
      default:
        return status;
    }
  }

  String get locationLabel {
    switch (location) {
      case 'gym':
        return 'Salle';
      case 'home':
        return 'Maison';
      case 'outdoor':
        return 'Extérieur';
      default:
        return 'Autre';
    }
  }

  bool get isCompleted => status == 'completed';
  bool get isInProgress => status == 'in_progress';
}
