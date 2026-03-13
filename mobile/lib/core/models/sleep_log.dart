/// Modèles Sommeil — SOMA LOT 6.
library;

class SleepSession {
  final String id;
  final String startAt;
  final String endAt;
  final double? durationHours;
  final int? perceivedQuality; // 1-5
  final String? notes;

  const SleepSession({
    required this.id,
    required this.startAt,
    required this.endAt,
    this.durationHours,
    this.perceivedQuality,
    this.notes,
  });

  factory SleepSession.fromJson(Map<String, dynamic> json) => SleepSession(
        id: json['id'] as String,
        startAt: json['start_at'] as String,
        endAt: json['end_at'] as String,
        durationHours: (json['duration_hours'] as num?)?.toDouble(),
        perceivedQuality: json['perceived_quality'] as int?,
        notes: json['notes'] as String?,
      );

  String get qualityLabel {
    switch (perceivedQuality) {
      case 1:
        return 'Mauvaise';
      case 2:
        return 'Médiocre';
      case 3:
        return 'Correcte';
      case 4:
        return 'Bonne';
      case 5:
        return 'Excellente';
      default:
        return '—';
    }
  }

  String get durationLabel {
    if (durationHours == null) return '—';
    final h = durationHours!.floor();
    final m = ((durationHours! - h) * 60).round();
    return m > 0 ? '${h}h${m.toString().padLeft(2, '0')}' : '${h}h';
  }

  String get qualityEmoji {
    switch (perceivedQuality) {
      case 1:
        return '😴';
      case 2:
        return '😕';
      case 3:
        return '😐';
      case 4:
        return '😊';
      case 5:
        return '🌟';
      default:
        return '💤';
    }
  }
}
