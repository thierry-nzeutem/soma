/// Ecran Insights SOMA — 4eme onglet (LOT 5).
///
/// Liste filtree des insights sante.
/// Supporte : mark as read, dismiss, filtre par severite.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/insight.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'insights_notifier.dart';

class InsightsScreen extends ConsumerStatefulWidget {
  const InsightsScreen({super.key});

  @override
  ConsumerState<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends ConsumerState<InsightsScreen> {
  String _filter = 'all'; // all | unread | warning | critical

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(insightsProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Insights',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(insightsProvider.notifier).refresh(),
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => _InsightsError(
          message: err.toString(),
          onRetry: () => ref.read(insightsProvider.notifier).refresh(),
        ),
        data: (list) => RefreshIndicator(
          color: colors.accent,
          backgroundColor: colors.surface,
          onRefresh: () => ref.read(insightsProvider.notifier).refresh(),
          child: _InsightsContent(
            list: list,
            filter: _filter,
            onFilterChanged: (f) => setState(() => _filter = f),
          ),
        ),
      ),
    );
  }
}

// -- Contenu -------------------------------------------------------------------

class _InsightsContent extends ConsumerWidget {
  final InsightList list;
  final String filter;
  final ValueChanged<String> onFilterChanged;

  const _InsightsContent({
    required this.list,
    required this.filter,
    required this.onFilterChanged,
  });

  List<Insight> _filtered() {
    switch (filter) {
      case 'unread':
        return list.insights.where((i) => !i.isRead && !i.isDismissed).toList();
      case 'warning':
        return list.insights.where((i) => i.severity == 'warning').toList();
      case 'critical':
        return list.insights.where((i) => i.severity == 'critical').toList();
      default:
        return list.insights.where((i) => !i.isDismissed).toList();
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtered = _filtered();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // En-tete
        _InsightsHeader(
          totalCount: list.totalCount,
          unreadCount: list.unreadCount,
        ),
        const SizedBox(height: 16),

        // Filtres
        _FilterChips(
          selected: filter,
          onChanged: onFilterChanged,
          unreadCount: list.unreadCount,
        ),
        const SizedBox(height: 16),

        // Liste
        if (filtered.isEmpty)
          const _EmptyState()
        else
          ...filtered.map(
            (insight) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _InsightCard(
                insight: insight,
                onRead: () =>
                    ref.read(insightsProvider.notifier).markAsRead(insight.id),
                onDismiss: () =>
                    ref.read(insightsProvider.notifier).dismiss(insight.id),
              ),
            ),
          ),
        const SizedBox(height: 16),
      ],
    );
  }
}

// -- Header --------------------------------------------------------------------

class _InsightsHeader extends StatelessWidget {
  final int totalCount;
  final int unreadCount;

  const _InsightsHeader({
    required this.totalCount,
    required this.unreadCount,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Row(
      children: [
        Icon(Icons.lightbulb_outline_rounded,
            size: 18, color: colors.accent),
        const SizedBox(width: 8),
        Text(
          '$unreadCount non lu${unreadCount > 1 ? 's' : ''}',
          style: TextStyle(
            color: colors.accent,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const Spacer(),
        Text(
          '$totalCount total',
          style: TextStyle(color: colors.textMuted, fontSize: 12),
        ),
      ],
    );
  }
}

// -- Filtres -------------------------------------------------------------------

class _FilterChips extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;
  final int unreadCount;

  const _FilterChips({
    required this.selected,
    required this.onChanged,
    required this.unreadCount,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _Chip(label: 'Tous', value: 'all', selected: selected, onTap: onChanged),
          const SizedBox(width: 8),
          _Chip(
            label: 'Non lus${unreadCount > 0 ? ' ($unreadCount)' : ''}',
            value: 'unread',
            selected: selected,
            onTap: onChanged,
          ),
          const SizedBox(width: 8),
          _Chip(label: 'Attention', value: 'warning', selected: selected, onTap: onChanged),
          const SizedBox(width: 8),
          _Chip(label: 'Critique', value: 'critical', selected: selected, onTap: onChanged),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final String value;
  final String selected;
  final ValueChanged<String> onTap;

  const _Chip({
    required this.label,
    required this.value,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final isSelected = selected == value;

    return GestureDetector(
      onTap: () => onTap(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected
              ? colors.accent.withAlpha(25)
              : colors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected
                ? colors.accent
                : colors.border,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? colors.accent : colors.textMuted,
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

// -- Carte Insight -------------------------------------------------------------

class _InsightCard extends StatelessWidget {
  final Insight insight;
  final VoidCallback onRead;
  final VoidCallback onDismiss;

  const _InsightCard({
    required this.insight,
    required this.onRead,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final severityColor = _severityColor(insight.severity, colors);
    final isUnread = !insight.isRead;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isUnread
              ? severityColor.withAlpha(76)
              : colors.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Badge severite
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: severityColor.withAlpha(25),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  insight.severity.toUpperCase(),
                  style: TextStyle(
                    color: severityColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                insight.categoryLabel,
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: 11,
                ),
              ),
              const Spacer(),
              // Indicateur non lu
              if (isUnread)
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: severityColor,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            insight.title,
            style: TextStyle(
              color: colors.text,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            insight.message,
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 13,
              height: 1.4,
            ),
          ),
          if (insight.action != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.arrow_forward_rounded,
                    size: 14, color: colors.accent),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    insight.action!,
                    style: TextStyle(
                      color: colors.accent,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              if (!insight.isRead)
                _ActionButton(
                  label: 'Lu',
                  icon: Icons.check_rounded,
                  color: colors.accent,
                  onTap: onRead,
                ),
              if (!insight.isRead) const SizedBox(width: 8),
              _ActionButton(
                label: 'Ignorer',
                icon: Icons.close_rounded,
                color: colors.textMuted,
                onTap: onDismiss,
              ),
            ],
          ),
        ],
      ),
    );
  }

  static Color _severityColor(String severity, dynamic colors) {
    switch (severity) {
      case 'critical':
        return colors.danger;
      case 'warning':
        return const Color(0xFFFFB347);
      default:
        return colors.accent;
    }
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ActionButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: color.withAlpha(25),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withAlpha(76)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// -- Etat vide -----------------------------------------------------------------

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 48),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.lightbulb_outline_rounded,
              size: 48, color: colors.textMuted),
          const SizedBox(height: 16),
          Text(
            'Aucun insight pour le moment',
            style: TextStyle(color: colors.text, fontSize: 16),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Continuez a enregistrer vos donnees\npour obtenir des recommandations personnalisees.',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

// -- Erreur --------------------------------------------------------------------

class _InsightsError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _InsightsError({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.lightbulb_outline_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Impossible de charger les insights',
              style: TextStyle(color: colors.text, fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
