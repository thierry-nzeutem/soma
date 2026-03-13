/// Modèle Insight SOMA — LOT 5.
library;

class Insight {
  final String id;
  final String category;
  final String severity;
  final String title;
  final String message;
  final String? action;
  final bool isRead;
  final bool isDismissed;
  final String detectedAt;
  final String? expiresAt;

  const Insight({
    required this.id,
    required this.category,
    required this.severity,
    required this.title,
    required this.message,
    this.action,
    required this.isRead,
    required this.isDismissed,
    required this.detectedAt,
    this.expiresAt,
  });

  factory Insight.fromJson(Map<String, dynamic> json) {
    return Insight(
      id: json['id'] as String,
      category: json['category'] as String? ?? 'general',
      severity: json['severity'] as String? ?? 'info',
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
      action: json['action'] as String?,
      isRead: json['is_read'] as bool? ?? false,
      isDismissed: json['is_dismissed'] as bool? ?? false,
      detectedAt: json['detected_at'] as String? ?? '',
      expiresAt: json['expires_at'] as String?,
    );
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────

  bool get isWarning => severity == 'warning';
  bool get isCritical => severity == 'critical';
  bool get isActive => !isRead && !isDismissed;

  String get categoryLabel {
    switch (category) {
      case 'nutrition':
        return 'Nutrition';
      case 'sleep':
        return 'Sommeil';
      case 'activity':
        return 'Activité';
      case 'recovery':
        return 'Récupération';
      case 'training':
        return 'Entraînement';
      case 'hydration':
        return 'Hydratation';
      case 'weight':
        return 'Poids';
      default:
        return category;
    }
  }
}

class InsightList {
  final List<Insight> insights;
  final int totalCount;
  final int unreadCount;

  const InsightList({
    required this.insights,
    required this.totalCount,
    required this.unreadCount,
  });

  factory InsightList.fromJson(Map<String, dynamic> json) {
    final list = (json['insights'] as List<dynamic>? ?? [])
        .map((e) => Insight.fromJson(e as Map<String, dynamic>))
        .toList();
    return InsightList(
      insights: list,
      totalCount: json['total_count'] as int? ?? list.length,
      unreadCount: json['unread_count'] as int? ?? 0,
    );
  }
}
