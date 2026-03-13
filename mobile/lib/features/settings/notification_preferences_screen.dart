/// Écran Préférences Notifications — SOMA LOT 12.
///
/// Permet de configurer finement les catégories de notification.
/// Les alertes sécurité (safety) ne peuvent pas être désactivées.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/notifications/notification_models.dart';
import '../../core/notifications/notification_service.dart';
import '../../core/notifications/notification_scheduler.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';

class NotificationPreferencesScreen extends ConsumerStatefulWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  ConsumerState<NotificationPreferencesScreen> createState() =>
      _NotificationPreferencesScreenState();
}

class _NotificationPreferencesScreenState
    extends ConsumerState<NotificationPreferencesScreen> {
  bool _permissionsGranted = false;

  @override
  void initState() {
    super.initState();
    _checkPermissions();
  }

  Future<void> _checkPermissions() async {
    final granted = await NotificationService.instance.arePermissionsGranted();
    if (mounted) setState(() => _permissionsGranted = granted);
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final prefs = ref.watch(notificationPreferencesProvider);
    final notifier = ref.read(notificationPreferencesProvider.notifier);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Notifications'),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // ── Permission banner ─────────────────────────────────────────────
          if (!_permissionsGranted) ...[
            _PermissionBanner(onRequest: _requestPermissions),
            const SizedBox(height: 16),
          ],

          // ── Catégories ────────────────────────────────────────────────────
          _SectionTitle('Catégories'),
          const SizedBox(height: 8),

          ...prefs.map((pref) => _NotificationCategoryTile(
                pref: pref,
                onChanged: (enabled) async {
                  if (!pref.category.canDisable && !enabled) return;
                  await notifier.update(pref.copyWith(enabled: enabled));
                  // Re-planifier si nécessaire.
                  await ref.read(notificationSchedulerProvider).rescheduleAll();
                },
                onScheduleChanged: (hour, minute) async {
                  await notifier.update(
                    pref.copyWith(scheduledHour: hour, scheduledMinute: minute),
                  );
                  await ref.read(notificationSchedulerProvider).rescheduleAll();
                },
              )),

          const SizedBox(height: 24),

          // ── Actions rapides ───────────────────────────────────────────────
          _SectionTitle('Actions'),
          _ActionTile(
            icon: Icons.notifications_active_outlined,
            label: 'Envoyer une notification test',
            onTap: () => _sendTest(),
          ),
          _ActionTile(
            icon: Icons.refresh_rounded,
            label: 'Re-planifier toutes les notifications',
            onTap: () => _rescheduleAll(),
          ),
          _ActionTile(
            icon: Icons.notifications_off_outlined,
            label: 'Tout désactiver',
            onTap: () => _disableAll(prefs, notifier),
            isDanger: true,
          ),
        ],
      ),
    );
  }

  Future<void> _requestPermissions() async {
    await NotificationService.instance.requestPermissions();
    await _checkPermissions();
  }

  Future<void> _sendTest() async {
    await NotificationService.instance.show(
      id: 9999,
      title: '🔔 Test SOMA',
      body: 'Les notifications fonctionnent correctement.',
    );
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Notification de test envoyée')),
      );
    }
  }

  Future<void> _rescheduleAll() async {
    await ref.read(notificationSchedulerProvider).rescheduleAll();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Notifications re-planifiées')),
      );
    }
  }

  Future<void> _disableAll(
    List<NotificationPreference> prefs,
    NotificationPreferencesNotifier notifier,
  ) async {
    for (final pref in prefs) {
      if (pref.category.canDisable) {
        await notifier.update(pref.copyWith(enabled: false));
      }
    }
    await NotificationService.instance.cancelAll();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Toutes les notifications désactivées')),
      );
    }
  }
}

// ── Widgets ───────────────────────────────────────────────────────────────────

class _PermissionBanner extends StatelessWidget {
  const _PermissionBanner({required this.onRequest});
  final VoidCallback onRequest;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.warning.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.warning.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber_rounded,
                  color: colors.warning, size: 18),
              const SizedBox(width: 8),
              Text(
                'Notifications désactivées',
                style: TextStyle(
                  color: colors.warning,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Activez les notifications dans les réglages système pour recevoir les alertes SOMA.',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: onRequest,
              style: OutlinedButton.styleFrom(
                foregroundColor: colors.warning,
                side: BorderSide(color: colors.warning),
              ),
              child: const Text('Autoriser les notifications'),
            ),
          ),
        ],
      ),
    );
  }
}

class _NotificationCategoryTile extends StatelessWidget {
  const _NotificationCategoryTile({
    required this.pref,
    required this.onChanged,
    required this.onScheduleChanged,
  });

  final NotificationPreference pref;
  final void Function(bool) onChanged;
  final void Function(int hour, int minute) onScheduleChanged;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final hasSchedule =
        pref.scheduledHour != null && pref.scheduledMinute != null;
    final canEdit = pref.category.canDisable;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          pref.category.displayName,
                          style: TextStyle(
                            color: colors.text,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        if (!canEdit) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: colors.accent.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              'Requis',
                              style: TextStyle(
                                color: colors.accent,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      pref.category.description,
                      style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              Switch(
                value: pref.enabled,
                onChanged: canEdit ? onChanged : null,
                activeColor: colors.accent,
              ),
            ],
          ),
          // Sélecteur d'heure si applicable et activé.
          if (pref.enabled && hasSchedule) ...[
            Divider(color: colors.border, height: 16),
            GestureDetector(
              onTap: () => _pickTime(context),
              child: Row(
                children: [
                  Icon(Icons.schedule_rounded,
                      size: 16, color: colors.textMuted),
                  const SizedBox(width: 8),
                  Text(
                    'Heure : ${pref.scheduledHour!.toString().padLeft(2, '0')}:${pref.scheduledMinute!.toString().padLeft(2, '0')}',
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 13,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Modifier',
                    style: TextStyle(
                      color: colors.accent,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _pickTime(BuildContext context) async {
    final colors = context.somaColors;
    final initial = TimeOfDay(
      hour: pref.scheduledHour ?? 8,
      minute: pref.scheduledMinute ?? 0,
    );
    final picked = await showTimePicker(
      context: context,
      initialTime: initial,
      builder: (context, child) => Theme(
        data: ThemeData.dark().copyWith(
          colorScheme: ColorScheme.dark(
            primary: colors.accent,
            surface: colors.surfaceVariant,
          ),
        ),
        child: child!,
      ),
    );
    if (picked != null) {
      onScheduleChanged(picked.hour, picked.minute);
    }
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.label);
  final String label;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          color: colors.textMuted,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.icon,
    required this.label,
    required this.onTap,
    this.isDanger = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool isDanger;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = isDanger ? colors.danger : colors.textMuted;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: colors.border),
            ),
            child: Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 14),
                Text(
                  label,
                  style: TextStyle(color: color, fontSize: 14),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
