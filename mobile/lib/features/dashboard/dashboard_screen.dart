/// Écran Dashboard — vue métriques journalières SOMA.
///
/// Consomme GET /api/v1/metrics/daily via [dashboardProvider].
/// Affiche : poids, calories, protéines, hydratation, pas, sommeil,
///           score de récupération, HRV.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/daily_metrics.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/metric_card.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'dashboard_notifier.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final state = ref.watch(dashboardProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Dashboard',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(dashboardProvider.notifier).refresh(),
            tooltip: 'Actualiser',
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => _ErrorWidget(
          message: err.toString(),
          onRetry: () => ref.read(dashboardProvider.notifier).refresh(),
        ),
        data: (metrics) => RefreshIndicator(
          color: colors.accent,
          backgroundColor: colors.surface,
          onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
          child: _MetricsGrid(metrics: metrics),
        ),
      ),
    );
  }
}

// ── Grid de métriques ────────────────────────────────────────────────────────

class _MetricsGrid extends StatelessWidget {
  final DailyMetrics metrics;

  const _MetricsGrid({required this.metrics});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return CustomScrollView(
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.all(16),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              // Date
              _DateHeader(date: metrics.metricsDate),
              const SizedBox(height: 16),

              // ── LOT 18 : CTAs Briefing + Quick Journal ─────────────────
              _BriefingCTA(),
              const SizedBox(height: 10),
              _QuickJournalCTA(),
              const SizedBox(height: 16),

              // Score récupération (pleine largeur)
              if (metrics.readinessScore != null)
                MetricCard(
                  label: 'Score de Récupération',
                  value: metrics.readinessScore!.toStringAsFixed(0),
                  unit: '/ 100',
                  icon: Icons.favorite_rounded,
                  accentColor: _readinessColor(context, metrics.readinessScore!),
                  progressFraction: metrics.readinessScore! / 100,
                  subtitle: metrics.readinessLevel?.toUpperCase(),
                ),
              const SizedBox(height: 12),

              // Grille 2 colonnes
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.15,
                children: [
                  // Poids
                  MetricCard(
                    label: 'Poids',
                    value: metrics.weightKg?.toStringAsFixed(1) ?? '—',
                    unit: 'kg',
                    icon: Icons.monitor_weight_outlined,
                    accentColor: colors.info,
                  ),
                  // Calories
                  MetricCard(
                    label: 'Calories',
                    value: metrics.caloriesConsumed?.toStringAsFixed(0) ?? '—',
                    unit: 'kcal',
                    icon: Icons.local_fire_department_rounded,
                    accentColor: colors.danger,
                    progressFraction: metrics.caloriePct != null
                        ? (metrics.caloriePct! / 100).clamp(0, 1.5)
                        : null,
                    subtitle: metrics.caloriesTarget != null
                        ? 'objectif : ${metrics.caloriesTarget!.toStringAsFixed(0)} kcal'
                        : null,
                  ),
                  // Protéines
                  MetricCard(
                    label: 'Protéines',
                    value: metrics.proteinG?.toStringAsFixed(0) ?? '—',
                    unit: 'g',
                    icon: Icons.fitness_center_rounded,
                    accentColor: const Color(0xFFFFB347),
                    progressFraction: metrics.proteinPct != null
                        ? (metrics.proteinPct! / 100).clamp(0, 1.5)
                        : null,
                  ),
                  // Hydratation
                  MetricCard(
                    label: 'Hydratation',
                    value: metrics.hydrationMl != null
                        ? (metrics.hydrationMl! / 1000).toStringAsFixed(1)
                        : '—',
                    unit: 'L',
                    icon: Icons.water_drop_rounded,
                    accentColor: colors.info,
                    progressFraction: metrics.hydrationPct != null
                        ? (metrics.hydrationPct! / 100).clamp(0, 1)
                        : null,
                  ),
                  // Pas
                  MetricCard(
                    label: 'Pas',
                    value: metrics.steps != null
                        ? _formatSteps(metrics.steps!)
                        : '—',
                    icon: Icons.directions_walk_rounded,
                    accentColor: colors.accent,
                    progressFraction:
                        metrics.steps != null ? metrics.steps! / 10000 : null,
                    subtitle: 'objectif : 10 000',
                  ),
                  // Sommeil
                  MetricCard(
                    label: 'Sommeil',
                    value: metrics.sleepHours?.toStringAsFixed(1) ?? '—',
                    unit: 'h',
                    icon: Icons.bedtime_rounded,
                    accentColor: const Color(0xFF9B72CF),
                    progressFraction: metrics.sleepHours != null
                        ? (metrics.sleepHours! / 8).clamp(0, 1)
                        : null,
                    subtitle: metrics.sleepQualityLabel,
                  ),
                  // HRV
                  MetricCard(
                    label: 'HRV',
                    value: metrics.hrvMs?.toStringAsFixed(0) ?? '—',
                    unit: 'ms',
                    icon: Icons.monitor_heart_outlined,
                    accentColor: colors.accent,
                  ),
                  // Séances
                  MetricCard(
                    label: 'Séances',
                    value: metrics.workoutCount?.toString() ?? '0',
                    icon: Icons.sports_gymnastics_rounded,
                    accentColor: const Color(0xFFFFB347),
                    subtitle: metrics.totalTonnageKg != null
                        ? '${metrics.totalTonnageKg!.toStringAsFixed(0)} kg tonnage'
                        : null,
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Complétude des données
              _DataCompleteness(pct: metrics.dataCompletenessPct),
              const SizedBox(height: 20),

              // ── Accès rapide LOT 17 ──────────────────────────────────────
              _QuickAccessRow(),
              const SizedBox(height: 16),
            ]),
          ),
        ),
      ],
    );
  }

  static Color _readinessColor(BuildContext context, double score) {
    final colors = context.somaColors;
    if (score >= 70) return colors.accent;
    if (score >= 50) return const Color(0xFFFFB347);
    return colors.danger;
  }

  static String _formatSteps(int steps) {
    if (steps >= 1000) {
      return '${(steps / 1000).toStringAsFixed(1)}k';
    }
    return steps.toString();
  }
}

// ── Widgets auxiliaires ───────────────────────────────────────────────────────

class _DateHeader extends StatelessWidget {
  final String date;

  const _DateHeader({required this.date});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: [
        Icon(Icons.calendar_today_rounded,
            size: 14, color: colors.textMuted),
        const SizedBox(width: 6),
        Text(
          date,
          style: TextStyle(
            color: colors.textMuted,
            fontSize: 13,
          ),
        ),
      ],
    );
  }
}

class _DataCompleteness extends StatelessWidget {
  final double pct;

  const _DataCompleteness({required this.pct});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Icon(Icons.analytics_outlined,
              size: 16, color: colors.textMuted),
          const SizedBox(width: 8),
          Text(
            'Complétude données',
            style: TextStyle(color: colors.textSecondary, fontSize: 12),
          ),
          const Spacer(),
          Text(
            '${pct.toStringAsFixed(0)}%',
            style: TextStyle(
              color: pct >= 70
                  ? colors.accent
                  : const Color(0xFFFFB347),
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Accès rapide Coach Platform + Biomarkers ──────────────────────────────────

class _QuickAccessRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: [
        Expanded(
          child: _QuickAccessCard(
            label: 'Coach',
            icon: Icons.sports_rounded,
            color: colors.accent,
            route: '/coach-platform',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _QuickAccessCard(
            label: 'Biomarqueurs',
            icon: Icons.biotech_rounded,
            color: colors.info,
            route: '/biomarkers',
          ),
        ),
      ],
    );
  }
}

class _QuickAccessCard extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final String route;

  const _QuickAccessCard({
    required this.label,
    required this.icon,
    required this.color,
    required this.route,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, route),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.25)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 8),
            Text(label,
                style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.w600,
                    fontSize: 14)),
          ],
        ),
      ),
    );
  }
}

// ── LOT 18 : CTAs Briefing & Quick Journal ────────────────────────────────────

/// Carte "Briefing du matin" — accès au briefing SOMA quotidien.
class _BriefingCTA extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: () => context.go('/briefing'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1A2A1A), Color(0xFF0D1A0D)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: colors.accent.withAlpha(60)),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: colors.accent.withAlpha(30),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                Icons.wb_sunny_rounded,
                color: colors.accent,
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Briefing du matin',
                    style: TextStyle(
                      color: colors.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Votre santé du jour en un coup d\'œil',
                    style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios_rounded,
              color: colors.accent,
              size: 16,
            ),
          ],
        ),
      ),
    );
  }
}

/// Carte "Journal rapide" — saisie express <10 secondes.
class _QuickJournalCTA extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: () => context.go('/quick-journal'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: colors.surfaceVariant,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: colors.border),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: const Color(0xFF0A84FF).withAlpha(25),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.bolt_rounded,
                color: Color(0xFF0A84FF),
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Journal rapide',
                    style: TextStyle(
                      color: colors.text,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Repas · Workout · Poids · Eau · Sommeil',
                    style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios_rounded,
              color: colors.textMuted,
              size: 14,
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorWidget extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorWidget({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Impossible de charger les métriques',
              style: TextStyle(color: colors.text, fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
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
