/// Modeles Heart Rate Analytics -- SOMA.
///
/// Correspond aux endpoints :
///   GET /api/v1/heart-rate/analytics?date=YYYY-MM-DD
///   GET /api/v1/heart-rate/timeline?date=YYYY-MM-DD
library;

/// Un point de la timeline 24h de frequence cardiaque.
class HRTimelinePoint {
  final int hour;
  final double? avgBpm;
  final double? minBpm;
  final double? maxBpm;

  const HRTimelinePoint({
    required this.hour,
    this.avgBpm,
    this.minBpm,
    this.maxBpm,
  });

  factory HRTimelinePoint.fromJson(Map<String, dynamic> json) {
    return HRTimelinePoint(
      hour: json['hour'] as int? ?? 0,
      avgBpm: (json['avg_bpm'] as num?)?.toDouble(),
      minBpm: (json['min_bpm'] as num?)?.toDouble(),
      maxBpm: (json['max_bpm'] as num?)?.toDouble(),
    );
  }
}

/// Un evenement cardiaque notable (haute ou basse frequence).
class HREvent {
  final String type;
  final double value;
  final String recordedAt;
  final String? source;

  const HREvent({
    required this.type,
    required this.value,
    required this.recordedAt,
    this.source,
  });

  factory HREvent.fromJson(Map<String, dynamic> json) {
    return HREvent(
      type: json['type'] as String? ?? '',
      value: (json['value'] as num? ?? 0).toDouble(),
      recordedAt: json['recorded_at'] as String? ?? '',
      source: json['source'] as String?,
    );
  }
}

/// Donnees analytiques completes de frequence cardiaque pour une journee.
class HRAnalytics {
  final String date;
  final double? avgAwakeBpm;
  final double? avgSleepBpm;
  final double? restingHrBpm;
  final double? maxBpm;
  final double? minBpm;
  final List<HREvent> highRestingEvents;
  final List<HREvent> lowRestingEvents;

  const HRAnalytics({
    required this.date,
    this.avgAwakeBpm,
    this.avgSleepBpm,
    this.restingHrBpm,
    this.maxBpm,
    this.minBpm,
    required this.highRestingEvents,
    required this.lowRestingEvents,
  });

  factory HRAnalytics.fromJson(Map<String, dynamic> json) {
    return HRAnalytics(
      date: json['date'] as String? ?? '',
      avgAwakeBpm: (json['avg_awake_bpm'] as num?)?.toDouble(),
      avgSleepBpm: (json['avg_sleep_bpm'] as num?)?.toDouble(),
      restingHrBpm: (json['resting_hr_bpm'] as num?)?.toDouble(),
      maxBpm: (json['max_bpm'] as num?)?.toDouble(),
      minBpm: (json['min_bpm'] as num?)?.toDouble(),
      highRestingEvents: (json['high_resting_events'] as List<dynamic>? ?? [])
          .map((e) => HREvent.fromJson(e as Map<String, dynamic>))
          .toList(),
      lowRestingEvents: (json['low_resting_events'] as List<dynamic>? ?? [])
          .map((e) => HREvent.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  List<HREvent> get allEvents => [...highRestingEvents, ...lowRestingEvents];
  bool get hasEvents => highRestingEvents.isNotEmpty || lowRestingEvents.isNotEmpty;
}

/// Timeline 24h de frequence cardiaque.
class HRTimeline {
  final String date;
  final List<HRTimelinePoint> points;
  final double? avgAwakeBpm;
  final double? avgSleepBpm;

  const HRTimeline({
    required this.date,
    required this.points,
    this.avgAwakeBpm,
    this.avgSleepBpm,
  });

  factory HRTimeline.fromJson(Map<String, dynamic> json) {
    return HRTimeline(
      date: json['date'] as String? ?? '',
      points: (json['points'] as List<dynamic>? ?? [])
          .map((e) => HRTimelinePoint.fromJson(e as Map<String, dynamic>))
          .toList(),
      avgAwakeBpm: (json['avg_awake_bpm'] as num?)?.toDouble(),
      avgSleepBpm: (json['avg_sleep_bpm'] as num?)?.toDouble(),
    );
  }

  /// Retourne un point pour chaque heure 0-23. Null si aucun point pour cette heure.
  List<HRTimelinePoint?> get hourlyPoints {
    final map = <int, HRTimelinePoint>{};
    for (final p in points) {
      map[p.hour] = p;
    }
    return List.generate(24, (i) => map[i]);
  }
}
