/// Modèles Hydratation — SOMA LOT 6.
library;

class HydrationLog {
  final String id;
  final int volumeMl;
  final String loggedAt;
  final String beverageType;
  final String? notes;

  const HydrationLog({
    required this.id,
    required this.volumeMl,
    required this.loggedAt,
    required this.beverageType,
    this.notes,
  });

  factory HydrationLog.fromJson(Map<String, dynamic> json) => HydrationLog(
        id: json['id'] as String,
        volumeMl: json['volume_ml'] as int,
        loggedAt: json['logged_at'] as String,
        beverageType: json['beverage_type'] as String? ?? 'water',
        notes: json['notes'] as String?,
      );

  String get beverageLabel {
    switch (beverageType) {
      case 'water':
        return 'Eau';
      case 'coffee':
        return 'Café';
      case 'tea':
        return 'Thé';
      case 'juice':
        return 'Jus';
      default:
        return 'Autre';
    }
  }

  String get beverageEmoji {
    switch (beverageType) {
      case 'coffee':
        return '☕';
      case 'tea':
        return '🍵';
      case 'juice':
        return '🥤';
      default:
        return '💧';
    }
  }
}

class HydrationSummary {
  final String date;
  final int totalMl;
  final int targetMl;
  final double pct;
  final List<HydrationLog> entries;

  const HydrationSummary({
    required this.date,
    required this.totalMl,
    required this.targetMl,
    required this.pct,
    required this.entries,
  });

  factory HydrationSummary.fromJson(Map<String, dynamic> json) {
    final entries = json['entries'] as List<dynamic>? ?? [];
    return HydrationSummary(
      date: json['date'] as String? ?? '',
      totalMl: json['total_ml'] as int? ?? 0,
      targetMl: json['target_ml'] as int? ?? 2500,
      pct: (json['pct'] as num?)?.toDouble() ?? 0,
      entries: entries
          .map((e) => HydrationLog.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  double get progress => (totalMl / targetMl).clamp(0.0, 1.0);
  double get remainingMl => (targetMl - totalMl).clamp(0, targetMl).toDouble();
}
