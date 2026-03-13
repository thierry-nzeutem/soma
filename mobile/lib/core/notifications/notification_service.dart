/// NotificationService — Wrapper flutter_local_notifications pour SOMA.
///
/// Responsabilités :
///   - Initialisation des canaux Android + permissions iOS
///   - Affichage de notifications immédiates (show)
///   - Notifications planifiées à heure fixe (scheduleDaily)
///   - Annulation par ID ou par catégorie
///   - Persistance des préférences (SharedPreferences)
///
/// Architecture : singleton + provider Riverpod.
/// Sur simulateur/web : dégradation silencieuse (pas d'exception).
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

import 'notification_models.dart';

/// Clé SharedPreferences pour les préférences de notification.
const _kPreferencesKey = 'soma_notification_preferences';

/// Provider global du service de notification.
final notificationServiceProvider = Provider<NotificationService>(
  (ref) => NotificationService.instance,
);

/// Provider des préférences de notification (mutable via notifier).
final notificationPreferencesProvider =
    StateNotifierProvider<NotificationPreferencesNotifier,
        List<NotificationPreference>>(
  (ref) => NotificationPreferencesNotifier(),
);

class NotificationPreferencesNotifier
    extends StateNotifier<List<NotificationPreference>> {
  NotificationPreferencesNotifier() : super(NotificationPreference.defaults()) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_kPreferencesKey);
    if (raw != null) {
      try {
        final list = jsonDecode(raw) as List<dynamic>;
        state = list
            .map((e) => NotificationPreference.fromJson(
                e as Map<String, dynamic>))
            .toList();
      } catch (_) {
        state = NotificationPreference.defaults();
      }
    }
  }

  Future<void> update(NotificationPreference pref) async {
    state = [
      for (final p in state)
        if (p.category == pref.category) pref else p,
    ];
    await _persist();
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _kPreferencesKey,
      jsonEncode(state.map((p) => p.toJson()).toList()),
    );
  }

  NotificationPreference? forCategory(NotificationCategory cat) {
    try {
      return state.firstWhere((p) => p.category == cat);
    } catch (_) {
      return null;
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────

/// Service principal de notifications locales.
class NotificationService {
  NotificationService._();
  static final instance = NotificationService._();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  // ── Initialisation ─────────────────────────────────────────────────────────

  Future<void> initialize() async {
    if (_initialized) return;
    try {
      tz.initializeTimeZones();

      const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
      const iosInit = DarwinInitializationSettings(
        requestAlertPermission: true,
        requestBadgePermission: true,
        requestSoundPermission: true,
      );
      const initSettings = InitializationSettings(
        android: androidInit,
        iOS: iosInit,
      );

      await _plugin.initialize(
        initSettings,
        onDidReceiveNotificationResponse: _onNotificationTap,
      );

      _initialized = true;
      debugPrint('[Notifications] service initialisé');
    } catch (e) {
      debugPrint('[Notifications] erreur init (simulateur?) : $e');
    }
  }

  void _onNotificationTap(NotificationResponse response) {
    // Navigation gérée par l'app via deep link si besoin (payload = route).
    debugPrint('[Notifications] tap: ${response.payload}');
  }

  // ── API publique ───────────────────────────────────────────────────────────

  /// Affiche une notification immédiate.
  Future<void> show({
    required int id,
    required String title,
    required String body,
    String? payload,
    String channelId = NotificationChannels.dailyId,
    String channelName = NotificationChannels.dailyName,
    Importance importance = Importance.defaultImportance,
    Priority priority = Priority.defaultPriority,
  }) async {
    if (!_initialized) return;
    try {
      final details = NotificationDetails(
        android: AndroidNotificationDetails(
          channelId,
          channelName,
          importance: importance,
          priority: priority,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      );
      await _plugin.show(id, title, body, details, payload: payload);
    } catch (e) {
      debugPrint('[Notifications] show error: $e');
    }
  }

  /// Planifie une notification quotidienne à [hour]:[minute].
  Future<void> scheduleDaily({
    required int id,
    required String title,
    required String body,
    required int hour,
    required int minute,
    String? payload,
    String channelId = NotificationChannels.dailyId,
    String channelName = NotificationChannels.dailyName,
  }) async {
    if (!_initialized) return;
    try {
      final now = tz.TZDateTime.now(tz.local);
      var scheduled = tz.TZDateTime(
        tz.local,
        now.year,
        now.month,
        now.day,
        hour,
        minute,
      );
      if (scheduled.isBefore(now)) {
        scheduled = scheduled.add(const Duration(days: 1));
      }

      final details = NotificationDetails(
        android: AndroidNotificationDetails(
          channelId,
          channelName,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      );

      await _plugin.zonedSchedule(
        id,
        title,
        body,
        scheduled,
        details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        matchDateTimeComponents: DateTimeComponents.time,
        payload: payload,
      );
      debugPrint('[Notifications] planifié $id à $hour:$minute');
    } catch (e) {
      debugPrint('[Notifications] scheduleDaily error: $e');
    }
  }

  /// Annule une notification par ID.
  Future<void> cancel(int id) async {
    if (!_initialized) return;
    try {
      await _plugin.cancel(id);
    } catch (e) {
      debugPrint('[Notifications] cancel error: $e');
    }
  }

  /// Annule toutes les notifications planifiées.
  Future<void> cancelAll() async {
    if (!_initialized) return;
    try {
      await _plugin.cancelAll();
    } catch (e) {
      debugPrint('[Notifications] cancelAll error: $e');
    }
  }

  /// Demande les permissions (iOS principalement).
  Future<bool> requestPermissions() async {
    if (!_initialized) return false;
    try {
      final ios = _plugin.resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin>();
      final result = await ios?.requestPermissions(
        alert: true,
        badge: true,
        sound: true,
      );
      return result ?? true;
    } catch (_) {
      return false;
    }
  }

  /// Vérifie si les notifications sont autorisées.
  Future<bool> arePermissionsGranted() async {
    try {
      final ios = _plugin.resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin>();
      if (ios != null) {
        final settings = await ios.checkPermissions();
        return settings?.isEnabled ?? false;
      }
      return true; // Android — vérification simplifiée
    } catch (_) {
      return false;
    }
  }
}
