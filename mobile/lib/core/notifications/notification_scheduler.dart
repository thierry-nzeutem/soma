/// NotificationScheduler — Planification intelligente des notifications SOMA.
///
/// Logique de scheduling :
///   - daily      : 7h30 briefing matinal (configurable)
///   - hydration  : 15h00 rappel hydratation (configurable)
///   - sleep      : 22h00 rappel coucher (fixe)
///   - recovery   : immédiat si alerte détectée (risque > 70)
///   - safety     : immédiat si risque blessure critique (> 80)
///
/// Ce service est appelé à l'initialisation et quand les préférences changent.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'notification_models.dart';
import 'notification_service.dart';

/// Provider du scheduler.
final notificationSchedulerProvider = Provider<NotificationScheduler>((ref) {
  final service = ref.watch(notificationServiceProvider);
  final prefs = ref.watch(notificationPreferencesProvider);
  return NotificationScheduler(service: service, preferences: prefs);
});

class NotificationScheduler {
  final NotificationService service;
  final List<NotificationPreference> preferences;

  const NotificationScheduler({
    required this.service,
    required this.preferences,
  });

  NotificationPreference? _pref(NotificationCategory cat) {
    try {
      return preferences.firstWhere((p) => p.category == cat);
    } catch (_) {
      return null;
    }
  }

  // ── Scheduling global ──────────────────────────────────────────────────────

  /// Re-planifie toutes les notifications selon les préférences actuelles.
  Future<void> rescheduleAll() async {
    await service.cancelAll();
    await scheduleMorningBriefing();
    await scheduleHydrationReminder();
    await scheduleSleepReminder();
    debugPrint('[Scheduler] toutes les notifications re-planifiées');
  }

  // ── Daily briefing ─────────────────────────────────────────────────────────

  Future<void> scheduleMorningBriefing() async {
    final pref = _pref(NotificationCategory.daily);
    if (pref == null || !pref.enabled) {
      await service.cancel(NotificationIds.morningBriefing);
      return;
    }
    final hour = pref.scheduledHour ?? 7;
    final minute = pref.scheduledMinute ?? 30;
    await service.scheduleDaily(
      id: NotificationIds.morningBriefing,
      title: '☀️ Bonjour, voici votre briefing SOMA',
      body: 'Vos métriques de santé et recommandations du jour sont prêtes.',
      hour: hour,
      minute: minute,
      payload: '/briefing', // LOT 18 — ouvre MorningBriefingScreen
      channelId: NotificationChannels.dailyId,
      channelName: NotificationChannels.dailyName,
    );
  }

  // ── Hydration reminder ─────────────────────────────────────────────────────

  Future<void> scheduleHydrationReminder() async {
    final pref = _pref(NotificationCategory.hydration);
    if (pref == null || !pref.enabled) {
      await service.cancel(NotificationIds.hydrationReminder);
      return;
    }
    final hour = pref.scheduledHour ?? 15;
    final minute = pref.scheduledMinute ?? 0;
    await service.scheduleDaily(
      id: NotificationIds.hydrationReminder,
      title: '💧 Rappel hydratation',
      body: 'Pensez à boire de l\'eau pour atteindre votre objectif du jour.',
      hour: hour,
      minute: minute,
      payload: '/journal/hydration',
      channelId: NotificationChannels.hydrationId,
      channelName: NotificationChannels.hydrationName,
    );
  }

  // ── Sleep reminder ─────────────────────────────────────────────────────────

  Future<void> scheduleSleepReminder() async {
    final pref = _pref(NotificationCategory.recovery);
    if (pref == null || !pref.enabled) {
      await service.cancel(NotificationIds.sleepReminder);
      return;
    }
    await service.scheduleDaily(
      id: NotificationIds.sleepReminder,
      title: '🌙 Il est temps de se préparer au sommeil',
      body: 'Un bon sommeil optimise votre récupération et votre performance.',
      hour: 22,
      minute: 0,
      payload: '/journal/sleep',
      channelId: NotificationChannels.recoveryId,
      channelName: NotificationChannels.recoveryName,
    );
  }

  // ── Notifications immédiates ───────────────────────────────────────────────

  /// Alerte récupération (si score readiness < 40).
  Future<void> sendRecoveryAlert({required double readinessScore}) async {
    final pref = _pref(NotificationCategory.recovery);
    if (pref == null || !pref.enabled) return;
    if (readinessScore >= 40) return;

    await service.show(
      id: NotificationIds.recoveryAlert,
      title: '⚠️ Récupération insuffisante',
      body:
          'Votre score de readiness est à ${readinessScore.toStringAsFixed(0)}/100. '
          'Priorisez le repos aujourd\'hui.',
      payload: '/health-plan',
      channelId: NotificationChannels.recoveryId,
      channelName: NotificationChannels.recoveryName,
      importance: Importance.high,
      priority: Priority.high,
    );
  }

  /// Alerte sécurité — risque blessure critique (toujours active).
  Future<void> sendSafetyAlert({
    required String title,
    required String body,
  }) async {
    await service.show(
      id: NotificationIds.safetyAlert,
      title: title,
      body: body,
      payload: '/health-plan',
      channelId: NotificationChannels.safetyId,
      channelName: NotificationChannels.safetyName,
      importance: Importance.max,
      priority: Priority.max,
    );
  }

  /// Notification nouveau message coach IA.
  Future<void> sendCoachMessage({required String preview}) async {
    final pref = _pref(NotificationCategory.coach);
    if (pref == null || !pref.enabled) return;
    await service.show(
      id: NotificationIds.coachMessage,
      title: '🤖 Votre coach IA a répondu',
      body: preview,
      payload: '/coach',
      channelId: NotificationChannels.dailyId,
      channelName: NotificationChannels.dailyName,
    );
  }

  /// Notification sync terminée (après reconnexion).
  Future<void> sendSyncComplete({required int syncedCount}) async {
    if (syncedCount == 0) return;
    await service.show(
      id: NotificationIds.syncComplete,
      title: '✅ Synchronisation terminée',
      body: '$syncedCount action${syncedCount > 1 ? 's' : ''} synchronisée${syncedCount > 1 ? 's' : ''}.',
      channelId: NotificationChannels.dailyId,
      channelName: NotificationChannels.dailyName,
    );
  }
}
