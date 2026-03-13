/// Écran Gestion du Cache — SOMA LOT 12.
///
/// Affiche :
///   - Taille estimée du cache
///   - Nombre d'entrées actives
///   - Actions de purge sélective ou globale
///   - Statut de la file de synchronisation
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cache/local_cache.dart';
import '../../core/sync/sync_manager.dart';
import '../../core/sync/sync_queue.dart';
import '../../core/offline/connectivity_service.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';

class CacheManagementScreen extends ConsumerStatefulWidget {
  const CacheManagementScreen({super.key});

  @override
  ConsumerState<CacheManagementScreen> createState() =>
      _CacheManagementScreenState();
}

class _CacheManagementScreenState
    extends ConsumerState<CacheManagementScreen> {
  int _cacheEntries = 0;
  int _cacheSizeKb = 0;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _refreshStats();
  }

  Future<void> _refreshStats() async {
    final cache = ref.read(localCacheProvider);
    final entries = await cache.activeEntryCount();
    final sizeBytes = await cache.estimatedSizeBytes();
    if (mounted) {
      setState(() {
        _cacheEntries = entries;
        _cacheSizeKb = (sizeBytes / 1024).round();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final syncStatus = ref.watch(syncStatusProvider);
    final isOnline = ref.watch(isOnlineProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Cache & Synchronisation'),
      body: RefreshIndicator(
        onRefresh: _refreshStats,
        color: colors.accent,
        backgroundColor: colors.surface,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // ── Statut connexion ──────────────────────────────────────────────
            _StatusCard(
              icon: isOnline
                  ? Icons.wifi_rounded
                  : Icons.wifi_off_rounded,
              label: isOnline ? 'En ligne' : 'Hors connexion',
              color: isOnline
                  ? colors.accent
                  : colors.warning,
            ),

            const SizedBox(height: 16),

            // ── Cache ─────────────────────────────────────────────────────────
            _SectionTitle('Cache local'),
            _MetricCard(
              label: 'Entrées actives',
              value: '$_cacheEntries',
              icon: Icons.folder_outlined,
            ),
            _MetricCard(
              label: 'Taille estimée',
              value: '~${_cacheSizeKb} Ko',
              icon: Icons.storage_rounded,
            ),

            const SizedBox(height: 12),

            _ActionButton(
              icon: Icons.delete_sweep_outlined,
              label: 'Purger les entrées expirées',
              onTap: _purgeExpired,
              loading: _loading,
            ),
            _ActionButton(
              icon: Icons.delete_forever_rounded,
              label: 'Vider tout le cache',
              onTap: _purgeAll,
              loading: _loading,
              isDanger: true,
            ),

            const SizedBox(height: 24),

            // ── File de sync ──────────────────────────────────────────────────
            _SectionTitle('File de synchronisation'),
            _MetricCard(
              label: 'Actions en attente',
              value: '${syncStatus.pendingCount}',
              icon: Icons.pending_actions_rounded,
              valueColor: syncStatus.pendingCount > 0
                  ? colors.warning
                  : colors.accent,
            ),
            if (syncStatus.lastSyncAt != null)
              _MetricCard(
                label: 'Dernière sync',
                value: _formatTime(syncStatus.lastSyncAt!),
                icon: Icons.sync_rounded,
              ),
            if (syncStatus.lastError != null)
              _MetricCard(
                label: 'Dernière erreur',
                value: syncStatus.lastError!,
                icon: Icons.error_outline_rounded,
                valueColor: colors.danger,
              ),

            const SizedBox(height: 12),

            _ActionButton(
              icon: Icons.sync_rounded,
              label: 'Synchroniser maintenant',
              onTap: isOnline ? _syncNow : null,
              loading: syncStatus.isSyncing,
            ),
            _ActionButton(
              icon: Icons.delete_outline_rounded,
              label: 'Vider la file de sync',
              onTap: _clearSyncQueue,
              loading: _loading,
            ),

            const SizedBox(height: 24),

            // Info
            Center(
              child: Text(
                'Le cache est purgé automatiquement à l\'expiration des TTL.',
                style: TextStyle(color: colors.textMuted, fontSize: 11),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _purgeExpired() async {
    setState(() => _loading = true);
    final cache = ref.read(localCacheProvider);
    await cache.purgeExpired();
    await _refreshStats();
    setState(() => _loading = false);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Entrées expirées supprimées')),
      );
    }
  }

  Future<void> _purgeAll() async {
    final colors = context.somaColors;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: colors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          'Vider le cache',
          style: TextStyle(color: colors.text),
        ),
        content: Text(
          'Toutes les données en cache seront supprimées. '
          'La prochaine ouverture demandera une connexion réseau.',
          style: TextStyle(color: colors.textMuted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text('Annuler',
                style: TextStyle(color: colors.textSecondary)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: colors.danger,
              foregroundColor: Colors.white,
            ),
            child: const Text('Vider'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => _loading = true);
      final cache = ref.read(localCacheProvider);
      await cache.purgeAll();
      await _refreshStats();
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Cache vidé')),
        );
      }
    }
  }

  Future<void> _syncNow() async {
    final manager = ref.read(syncManagerProvider);
    final statusNotifier = ref.read(syncStatusProvider.notifier);
    await manager.processPending(statusNotifier);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Synchronisation lancée')),
      );
    }
  }

  Future<void> _clearSyncQueue() async {
    final queue = ref.read(syncQueueProvider);
    await queue.purgeAll();
    ref.read(syncStatusProvider.notifier).refreshCount();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('File de sync vidée')),
      );
    }
  }

  String _formatTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inSeconds < 60) return 'Il y a ${diff.inSeconds}s';
    if (diff.inMinutes < 60) return 'Il y a ${diff.inMinutes}min';
    if (diff.inHours < 24) return 'Il y a ${diff.inHours}h';
    return 'Il y a ${diff.inDays}j';
  }
}

// ── Widgets ───────────────────────────────────────────────────────────────────

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

class _StatusCard extends StatelessWidget {
  const _StatusCard({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 12),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    this.valueColor,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color? valueColor;

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
          Expanded(
            child: Text(
              label,
              style: TextStyle(color: colors.textSecondary, fontSize: 14),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              color: valueColor ?? colors.text,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.loading = false,
    this.isDanger = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final bool loading;
  final bool isDanger;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final color = isDanger ? colors.danger : colors.accent;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: OutlinedButton.icon(
        onPressed: loading ? null : onTap,
        icon: loading
            ? SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: color,
                ),
              )
            : Icon(icon, size: 18),
        label: Text(label),
        style: OutlinedButton.styleFrom(
          foregroundColor: color,
          side: BorderSide(color: color.withOpacity(0.4)),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          alignment: Alignment.centerLeft,
        ),
      ),
    );
  }
}
