/// Écran Paramètres — LOT 12 : Control Center avec cache, sync, notifications.
/// BATCH 3 : Ajout section Apparence (thème clair/sombre/système) + migration couleurs.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_constants.dart';
import '../../core/offline/connectivity_service.dart';
import '../../core/sync/sync_manager.dart';
import '../../core/l10n/locale_provider.dart';
import '../../core/theme/theme_extensions.dart';
import '../../core/theme/theme_provider.dart';
import '../../features/auth/auth_notifier.dart';
import '../../shared/widgets/soma_app_bar.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(isOnlineProvider);
    final syncStatus = ref.watch(syncStatusProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Paramètres'),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (!isOnline) ...[
            _OfflineStatusBanner(),
            const SizedBox(height: 16),
          ],
          _SectionTitle('Application'),
          _SettingsTile(
            icon: Icons.info_outline_rounded,
            label: 'Version',
            value: '1.3.0 · LOT 12',
          ),
          _SettingsTile(
            icon: Icons.cloud_outlined,
            label: 'Serveur',
            value: ApiConstants.baseUrl,
          ),
          const SizedBox(height: 24),
          _SectionTitle('Apparence'),
          _ThemeModeSelector(),
          const SizedBox(height: 16),
          _LanguageSelector(),
          const SizedBox(height: 24),
          _SectionTitle('Compte'),
          _SettingsActionTile(
            icon: Icons.person_outline_rounded,
            label: 'Mon profil',
            onTap: () => context.push('/profile/edit'),
          ),
          const SizedBox(height: 24),
          _SectionTitle('Fiabilité & Données'),
          _SettingsActionTile(
            icon: Icons.notifications_outlined,
            label: 'Préférences notifications',
            onTap: () => context.push('/settings/notifications'),
          ),
          _SettingsActionTile(
            icon: Icons.storage_rounded,
            label: 'Cache & Synchronisation',
            trailing: syncStatus.pendingCount > 0
                ? _SyncBadge(count: syncStatus.pendingCount)
                : null,
            onTap: () => context.push('/settings/cache'),
          ),
          const SizedBox(height: 24),
          _SectionTitle('Session'),
          Material(
            color: colors.surface,
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              onTap: () => _confirmLogout(context, ref),
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: colors.danger.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.logout_rounded, color: colors.danger, size: 20),
                    const SizedBox(width: 14),
                    Text('Déconnexion',
                      style: TextStyle(color: colors.danger, fontSize: 15, fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 40),
          Center(
            child: Text(
              'SOMA — Personal Health Intelligence',
              style: TextStyle(color: colors.textMuted.withOpacity(0.5), fontSize: 11, letterSpacing: 0.5),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
    final colors = context.somaColors;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: colors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text('Déconnexion', style: TextStyle(color: colors.text)),
        content: Text('Voulez-vous vraiment vous déconnecter ?',
            style: TextStyle(color: colors.textMuted)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text('Annuler', style: TextStyle(color: colors.textSecondary)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(
                backgroundColor: colors.danger, foregroundColor: Colors.white),
            child: const Text('Déconnecter'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await ref.read(authProvider.notifier).logout();
      if (context.mounted) context.go('/login');
    }
  }
}

// ── Language Selector ──────────────────────────────────────────────────────

class _LanguageSelector extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentLocale = ref.watch(localeProvider);
    final colors = context.somaColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        children: [
          _LanguageOption(
            flag: '🇫🇷',
            label: 'Français',
            locale: const Locale('fr'),
            currentLocale: currentLocale,
            isFirst: true,
            onTap: () => ref.read(localeProvider.notifier).setLocale(const Locale('fr')),
          ),
          Divider(height: 1, color: colors.border),
          _LanguageOption(
            flag: '🇬🇧',
            label: 'English',
            locale: const Locale('en'),
            currentLocale: currentLocale,
            isLast: true,
            onTap: () => ref.read(localeProvider.notifier).setLocale(const Locale('en')),
          ),
        ],
      ),
    );
  }
}

class _LanguageOption extends StatelessWidget {
  final String flag;
  final String label;
  final Locale locale;
  final Locale currentLocale;
  final VoidCallback onTap;
  final bool isFirst;
  final bool isLast;

  const _LanguageOption({
    required this.flag,
    required this.label,
    required this.locale,
    required this.currentLocale,
    required this.onTap,
    this.isFirst = false,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    final selected = locale == currentLocale;
    final colors = context.somaColors;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.vertical(
          top: isFirst ? const Radius.circular(12) : Radius.zero,
          bottom: isLast ? const Radius.circular(12) : Radius.zero,
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Text(flag, style: const TextStyle(fontSize: 18)),
              const SizedBox(width: 12),
              Expanded(
                child: Text(label,
                    style: TextStyle(
                        color: selected ? colors.accent : colors.text,
                        fontSize: 14,
                        fontWeight: selected ? FontWeight.w600 : FontWeight.w400)),
              ),
              if (selected)
                Icon(Icons.check_circle_rounded, color: colors.accent, size: 20)
              else
                Icon(Icons.circle_outlined, color: colors.textMuted.withOpacity(0.4), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Theme Mode Selector ────────────────────────────────────────────────────

class _ThemeModeSelector extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentMode = ref.watch(themePreferenceProvider);
    final colors = context.somaColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        children: [
          _ThemeModeOption(
            icon: Icons.brightness_high_rounded,
            label: 'Clair',
            subtitle: 'Interface lumineuse',
            mode: SomaThemeMode.light,
            currentMode: currentMode,
            isFirst: true,
            onTap: () => ref.read(themePreferenceProvider.notifier).setTheme(SomaThemeMode.light),
          ),
          Divider(height: 1, color: colors.border),
          _ThemeModeOption(
            icon: Icons.brightness_4_rounded,
            label: 'Sombre',
            subtitle: 'Interface sombre',
            mode: SomaThemeMode.dark,
            currentMode: currentMode,
            onTap: () => ref.read(themePreferenceProvider.notifier).setTheme(SomaThemeMode.dark),
          ),
          Divider(height: 1, color: colors.border),
          _ThemeModeOption(
            icon: Icons.brightness_auto_rounded,
            label: 'Système',
            subtitle: 'Suit le thème de l\'appareil',
            mode: SomaThemeMode.system,
            currentMode: currentMode,
            isLast: true,
            onTap: () => ref.read(themePreferenceProvider.notifier).setTheme(SomaThemeMode.system),
          ),
        ],
      ),
    );
  }
}

class _ThemeModeOption extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final SomaThemeMode mode;
  final SomaThemeMode currentMode;
  final VoidCallback onTap;
  final bool isFirst;
  final bool isLast;

  const _ThemeModeOption({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.mode,
    required this.currentMode,
    required this.onTap,
    this.isFirst = false,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    final selected = mode == currentMode;
    final colors = context.somaColors;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.vertical(
          top: isFirst ? const Radius.circular(12) : Radius.zero,
          bottom: isLast ? const Radius.circular(12) : Radius.zero,
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Icon(icon, color: selected ? colors.accent : colors.textMuted, size: 20),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label,
                        style: TextStyle(
                            color: selected ? colors.accent : colors.text,
                            fontSize: 14,
                            fontWeight: selected ? FontWeight.w600 : FontWeight.w400)),
                    Text(subtitle,
                        style: TextStyle(color: colors.textMuted, fontSize: 11)),
                  ],
                ),
              ),
              if (selected)
                Icon(Icons.check_circle_rounded, color: colors.accent, size: 20)
              else
                Icon(Icons.circle_outlined, color: colors.textMuted.withOpacity(0.4), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Helper Widgets ─────────────────────────────────────────────────────────

class _OfflineStatusBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: colors.warning.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.warning.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.wifi_off_rounded, color: colors.warning, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text('Hors connexion — modifications en attente de sync',
                style: TextStyle(color: colors.warning, fontSize: 12)),
          ),
        ],
      ),
    );
  }
}

class _SyncBadge extends StatelessWidget {
  const _SyncBadge({required this.count});
  final int count;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: colors.warning.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text('$count en attente',
          style: TextStyle(color: colors.warning, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String label;
  const _SectionTitle(this.label);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(label.toUpperCase(),
          style: TextStyle(color: context.somaColors.textMuted, fontSize: 11,
              fontWeight: FontWeight.w700, letterSpacing: 1.2)),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _SettingsTile({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Icon(icon, color: colors.textMuted, size: 20),
          const SizedBox(width: 14),
          Expanded(child: Text(label, style: TextStyle(color: colors.text, fontSize: 14))),
          Flexible(child: Text(value,
              style: TextStyle(color: colors.textSecondary, fontSize: 13),
              overflow: TextOverflow.ellipsis)),
        ],
      ),
    );
  }
}

class _SettingsActionTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Widget? trailing;

  const _SettingsActionTile({required this.icon, required this.label, required this.onTap, this.trailing});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: colors.border),
            ),
            child: Row(
              children: [
                Icon(icon, color: colors.textMuted, size: 20),
                const SizedBox(width: 14),
                Expanded(child: Text(label, style: TextStyle(color: colors.text, fontSize: 14))),
                if (trailing != null) ...[trailing!, const SizedBox(width: 8)],
                Icon(Icons.chevron_right_rounded, color: colors.textMuted, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
