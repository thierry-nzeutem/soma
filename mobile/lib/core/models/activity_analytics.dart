/// SOMA — Activity Analytics models.
///
/// Maps to:
///   GET /api/v1/activity/day
///   GET /api/v1/activity/period
library;

// Pure Dart — no Flutter import.

class HourlySteps {
  final int hour;
  final double steps;

  const HourlySteps({required this.hour, required this.steps});

  factory HourlySteps.fromJson(Map<String, dynamic> json) {
    return HourlySteps(
      hour: (json['hour'] as num?)?.toInt() ?? 0,
      steps: (json['steps'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ActivityDayResponse {
  final String date;
  final double? totalSteps;
  final double? distanceKm;
  final double? activeCaloriesKcal;
  final double? bmrKcal;
  final double? totalCaloriesKcal;
  final double? avgHeartRateBpm;
  final double? restingHeartRateBpm;
  final List<HourlySteps> hourlySteps;

  const ActivityDayResponse({
    required this.date,
    this.totalSteps,
    this.distanceKm,
    this.activeCaloriesKcal,
    this.bmrKcal,
    this.totalCaloriesKcal,
    this.avgHeartRateBpm,
    this.restingHeartRateBpm,
    this.hourlySteps = const [],
  });

  factory ActivityDayResponse.fromJson(Map<String, dynamic> json) {
    return ActivityDayResponse(
      date: json['date'] as String? ?? '',
      totalSteps: (json['total_steps'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      activeCaloriesKcal: (json['active_calories_kcal'] as num?)?.toDouble(),
      bmrKcal: (json['bmr_kcal'] as num?)?.toDouble(),
      totalCaloriesKcal: (json['total_calories_kcal'] as num?)?.toDouble(),
      avgHeartRateBpm: (json['avg_heart_rate_bpm'] as num?)?.toDouble(),
      restingHeartRateBpm: (json['resting_heart_rate_bpm'] as num?)?.toDouble(),
      hourlySteps: (json['hourly_steps'] as List<dynamic>? ?? [])
          .map((e) => HourlySteps.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  double get maxHourlySteps {
    if (hourlySteps.isEmpty) return 1.0;
    double max = 0;
    for (final h in hourlySteps) {
      if (h.steps > max) max = h.steps;
    }
    return max > 0 ? max : 1.0;
  }
}

class ActivityPeriodEntry {
  final String date;
  final double? steps;
  final double? distanceKm;
  final double? activeCaloriesKcal;

  const ActivityPeriodEntry({
    required this.date,
    this.steps,
    this.distanceKm,
    this.activeCaloriesKcal,
  });

  factory ActivityPeriodEntry.fromJson(Map<String, dynamic> json) {
    return ActivityPeriodEntry(
      date: json['date'] as String? ?? '',
      steps: (json['steps'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      activeCaloriesKcal: (json['active_calories_kcal'] as num?)?.toDouble(),
    );
  }
}

class ActivityPeriodResponse {
  final String period;
  final double? totalSteps;
  final double? avgDailySteps;
  final double? totalDistanceKm;
  final int? goalDaysCount;
  final List<ActivityPeriodEntry> entries;

  const ActivityPeriodResponse({
    required this.period,
    this.totalSteps,
    this.avgDailySteps,
    this.totalDistanceKm,
    this.goalDaysCount,
    this.entries = const [],
  });

  factory ActivityPeriodResponse.fromJson(Map<String, dynamic> json) {
    return ActivityPeriodResponse(
      period: json['period'] as String? ?? '',
      totalSteps: (json['total_steps'] as num?)?.toDouble(),
      avgDailySteps: (json['avg_daily_steps'] as num?)?.toDouble(),
      totalDistanceKm: (json['total_distance_km'] as num?)?.toDouble(),
      goalDaysCount: (json['goal_days_count'] as num?)?.toInt(),
      entries: (json['entries'] as List<dynamic>? ?? [])
          .map((e) => ActivityPeriodEntry.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
