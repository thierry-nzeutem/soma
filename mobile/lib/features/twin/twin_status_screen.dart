/// TwinStatusScreen — Jumeau Numérique SOMA LOT 11.
///
/// Affiche le statut global + 12 composantes physiologiques + recommandations.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/digital_twin.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/glycogen_gauge.dart';
import '../../shared/widgets/twin_component_card.dart';
import 'twin_notifier.dart';

class TwinStatusScreen extends ConsumerWidget {
  const TwinStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final twinAsync = ref.watch(twinProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Jumeau Numérique'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () => Navigator.pushNamed(context, '/twin/history'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(twinProvider.notifier).refresh(),
          ),
        ],
      ),
      body: twinAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(
          message: e.toString(),
          onRetry: () => ref.read(twinProvider.notifier).refresh(),
        ),
        data: (twin) {
          if (twin == null) {
            return const _EmptyView();
          }
          return _TwinBody(twin: twin);
        },
      ),
    );
  }
}

// ── Corps principal ───────────────────────────────────────────────────────────

class _TwinBody extends StatelessWidget {
  final DigitalTwinState twin;
  const _TwinBody({required this.twin});

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () async {},
      child: ListView(
        children: [
          // Bannière statut global
          _StatusBanner(twin: twin),
          const SizedBox(height: 8),

          // Gauge glycogène
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: GlycogenGauge(value: twin.glycogen.value),
          ),
          const SizedBox(height: 8),

          // Section : Énergie & Nutrition
          _SectionHeader(title: '🔋 Énergie & Nutrition'),
          TwinComponentCard(
              title: 'Bilan énergétique', component: twin.energyBalance),
          TwinComponentCard(
              title: 'Glycogène', component: twin.glycogen),
          TwinComponentCard(
              title: 'Disponibilité glucides',
              component: twin.carbAvailability),
          TwinComponentCard(
              title: 'Statut protéines', component: twin.proteinStatus),
          TwinComponentCard(
              title: 'Hydratation', component: twin.hydration),

          // Section : Récupération
          _SectionHeader(title: '😴 Récupération & Fatigue'),
          TwinComponentCard(
              title: 'Fatigue', component: twin.fatigue),
          TwinComponentCard(
              title: 'Dette de sommeil', component: twin.sleepDebt),
          TwinComponentCard(
              title: 'Inflammation', component: twin.inflammation),
          TwinComponentCard(
              title: 'Capacité de récupération',
              component: twin.recoveryCapacity),

          // Section : Performance
          _SectionHeader(title: '⚡ Performance'),
          TwinComponentCard(
              title: 'Disponibilité à l\'entraînement',
              component: twin.trainingReadiness),
          TwinComponentCard(
              title: 'Charge de stress', component: twin.stressLoad),
          TwinComponentCard(
              title: 'Flexibilité métabolique',
              component: twin.metabolicFlexibility),

          // Risques
          if (twin.plateauRisk || twin.underRecoveryRisk) ...[
            _SectionHeader(title: '⚠️ Alertes'),
            if (twin.plateauRisk)
              _AlertTile(
                  icon: Icons.pause_circle,
                  message: 'Risque de plateau détecté',
                  color: const Color(0xFFF59E0B)),
            if (twin.underRecoveryRisk)
              _AlertTile(
                  icon: Icons.battery_alert,
                  message: 'Sous-récupération détectée',
                  color: const Color(0xFFEF4444)),
          ],

          // Recommandations
          if (twin.recommendations.isNotEmpty) ...[
            _SectionHeader(title: '💡 Recommandations'),
            ...twin.recommendations.map(
              (r) => Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('•  ',
                        style: TextStyle(color: Color(0xFF3B82F6))),
                    Expanded(
                      child: Text(r,
                          style: Theme.of(context).textTheme.bodySmall),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ── Bannière statut global ────────────────────────────────────────────────────

class _StatusBanner extends StatelessWidget {
  final DigitalTwinState twin;
  const _StatusBanner({required this.twin});

  Color get _statusColor {
    switch (twin.overallStatus) {
      case 'fresh':
        return const Color(0xFF22C55E);
      case 'good':
        return const Color(0xFF84CC16);
      case 'moderate':
        return const Color(0xFFF59E0B);
      case 'tired':
        return const Color(0xFFF97316);
      case 'critical':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF6B7280);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _statusColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _statusColor.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: _statusColor.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              _statusIcon(twin.overallStatus),
              color: _statusColor,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  twin.overallStatusLabel,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _statusColor,
                  ),
                ),
                if (twin.primaryConcern.isNotEmpty)
                  Text(
                    twin.primaryConcern,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.7),
                    ),
                  ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${(twin.globalConfidence * 100).toStringAsFixed(0)}%',
                style: theme.textTheme.titleSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.5),
                ),
              ),
              Text(
                'confiance',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.4),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  IconData _statusIcon(String status) {
    switch (status) {
      case 'fresh':
        return Icons.bolt;
      case 'good':
        return Icons.thumb_up;
      case 'moderate':
        return Icons.remove_circle_outline;
      case 'tired':
        return Icons.battery_3_bar;
      case 'critical':
        return Icons.warning_amber;
      default:
        return Icons.device_hub;
    }
  }
}

// ── Widgets helpers ───────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
            ),
      ),
    );
  }
}

class _AlertTile extends StatelessWidget {
  final IconData icon;
  final String message;
  final Color color;
  const _AlertTile(
      {required this.icon, required this.message, required this.color});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      color: color.withOpacity(0.08),
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(message,
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: color, fontWeight: FontWeight.w600)),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.error_outline, size: 48, color: context.somaColors.danger),
          const SizedBox(height: 12),
          const Text('Impossible de charger le jumeau numérique'),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: onRetry, child: const Text('Réessayer')),
        ],
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.device_hub, size: 64, color: context.somaColors.textMuted),
          SizedBox(height: 16),
          Text('Aucun snapshot disponible'),
          SizedBox(height: 8),
          Text(
            'Le jumeau numérique se calcule chaque matin.',
            style: TextStyle(color: context.somaColors.textSecondary),
          ),
        ],
      ),
    );
  }
}
