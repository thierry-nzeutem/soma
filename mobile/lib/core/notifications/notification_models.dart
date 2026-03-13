/// Modèles pour les notifications intelligentes SOMA.
///
/// Catégories :
///   - daily      : briefing matinal, résumé soir
///   - hydration  : rappel hydratation
///   - activity   : rappel entraînement
///   - recovery   : alerte surmenage / récupération
///   - coach      : nouveau message coach IA
///   - safety     : alertes critiques (risque blessure élevé)
library;

/// Catégorie de notification — détermine l'icône, le canal et la priorité.
enum NotificationCategory {
  daily,
  hydration,
  activity,
  recovery,
  coach,
  safety;

  String get displayName => switch (this) {
        daily => 'Briefing quotidien',
        hydration => 'Hydratation',
        activity => 'Activité',
        recovery => 'Récupération',
        coach => 'Coach IA',
        safety => 'Alertes sécurité',
      };

  String get description => switch (this) {
        daily => 'Briefing matinal et résumé de santé',
        hydration => 'Rappels pour rester bien hydraté',
        activity => 'Rappels d\'entraînement',
        recovery => 'Alertes sur la récupération et le repos',
        coach => 'Notifications du coach IA',
        safety => 'Alertes critiques de sécurité (non désactivables)',
      };

  /// Les alertes sécurité ne peuvent pas être désactivées.
  bool get canDisable => this != NotificationCategory.safety;
}

/// Préférences de notification pour une catégorie donnée.
class NotificationPreference {
  final NotificationCategory category;
  final bool enabled;

  /// Heure de la notification quotidienne (null = heure par défaut).
  final int? scheduledHour;
  final int? scheduledMinute;

  const NotificationPreference({
    required this.category,
    required this.enabled,
    this.scheduledHour,
    this.scheduledMinute,
  });

  NotificationPreference copyWith({
    bool? enabled,
    int? scheduledHour,
    int? scheduledMinute,
  }) =>
      NotificationPreference(
        category: category,
        enabled: enabled ?? this.enabled,
        scheduledHour: scheduledHour ?? this.scheduledHour,
        scheduledMinute: scheduledMinute ?? this.scheduledMinute,
      );

  Map<String, dynamic> toJson() => {
        'category': category.name,
        'enabled': enabled,
        'scheduledHour': scheduledHour,
        'scheduledMinute': scheduledMinute,
      };

  factory NotificationPreference.fromJson(Map<String, dynamic> json) {
    final categoryName = json['category'] as String? ?? '';
    final category = NotificationCategory.values.firstWhere(
      (c) => c.name == categoryName,
      orElse: () => NotificationCategory.daily,
    );
    return NotificationPreference(
      category: category,
      enabled: json['enabled'] as bool? ?? true,
      scheduledHour: json['scheduledHour'] as int?,
      scheduledMinute: json['scheduledMinute'] as int?,
    );
  }

  /// Préférences par défaut pour toutes les catégories.
  static List<NotificationPreference> defaults() => [
        const NotificationPreference(
          category: NotificationCategory.daily,
          enabled: true,
          scheduledHour: 7,
          scheduledMinute: 30,
        ),
        const NotificationPreference(
          category: NotificationCategory.hydration,
          enabled: true,
          scheduledHour: 15,
          scheduledMinute: 0,
        ),
        const NotificationPreference(
          category: NotificationCategory.activity,
          enabled: false,
        ),
        const NotificationPreference(
          category: NotificationCategory.recovery,
          enabled: true,
        ),
        const NotificationPreference(
          category: NotificationCategory.coach,
          enabled: true,
        ),
        const NotificationPreference(
          category: NotificationCategory.safety,
          enabled: true, // toujours actif
        ),
      ];
}

/// IDs de notification (uniques par type).
class NotificationIds {
  NotificationIds._();
  static const morningBriefing = 1001;
  static const hydrationReminder = 1002;
  static const sleepReminder = 1003;
  static const activityReminder = 1004;
  static const recoveryAlert = 1005;
  static const coachMessage = 1006;
  static const safetyAlert = 1007;
  static const syncComplete = 1008;
}

/// Canaux Android (ignorés sur iOS — configuration Info.plist requise).
class NotificationChannels {
  NotificationChannels._();

  static const dailyId = 'soma_daily';
  static const dailyName = 'SOMA Briefing quotidien';
  static const dailyDesc = 'Briefing matinal et résumé de santé';

  static const hydrationId = 'soma_hydration';
  static const hydrationName = 'Hydratation';
  static const hydrationDesc = 'Rappels d\'hydratation';

  static const recoveryId = 'soma_recovery';
  static const recoveryName = 'Récupération & Activité';
  static const recoveryDesc = 'Alertes récupération et rappels activité';

  static const safetyId = 'soma_safety';
  static const safetyName = 'Alertes sécurité SOMA';
  static const safetyDesc = 'Alertes critiques — risque blessure, surmenage';
}
