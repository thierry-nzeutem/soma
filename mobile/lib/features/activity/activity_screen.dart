/// SOMA — Activity Screen.
///
/// Affiche les statistiques d'activite du jour et de la semaine.
/// Consomme activityDayProvider et activityPeriodProvider.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/activity_analytics.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'activity_notifier.dart';

// ── Constantes ────────────────────────────────────────────────────────────────

const _kStepGoal = 10000.0;

// ── Screen ────────────────────────────────────────────────────────────────────

class ActivityScreen extends ConsumerWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dayState = ref.watch(activityDayProvider);
    final periodState = ref.watch(activityPeriodProvider('week'));
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Activit\u00e9',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () {
              ref.invalidate(activityDayProvider);
              ref.invalidate(activityPeriodProvider('week'));
            },
          ),
        ],
      ),
      body: dayState.when(
          loading: () =>
              Center(child: CircularProgressIndicator(color: colors.accent)),
          error: (err, _) => _ActivityError(
            message: err.toString(),
            onRetry: () => ref.invalidate(activityDayProvider),
          ),
          data: (day) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // KPI row
              _KpiRow(day: day),
              const SizedBox(height: 16),

              // Step goal progress
              _StepGoalCard(day: day),
              const SizedBox(height: 16),

              // Hourly steps chart
              _HourlyStepsCard(day: day),
              const SizedBox(height: 16),

              // Heart rate row
              _HeartRateRow(day: day),
              const SizedBox(height: 16),

              // Period summary
              periodState.when(
                loading: () => Padding(
                  padding: const EdgeInsets.all(16),
                  child: Center(child: CircularProgressIndicator(color: colors.accent)),
                ),
                error: (err, _) => const SizedBox.shrink(),
                data: (period) => _PeriodSummaryCard(period: period),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
    );
  }
}

// ── KPI Row ───────────────────────────────────────────────────────────────────

class _KpiRow extends StatelessWidget {
  final ActivityDayResponse day;

  const _KpiRow({required this.day});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Activit\u00e9 du jour",
          style: TextStyle(
            color: colors.text,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          day.date,
          style: TextStyle(color: colors.textMuted, fontSize: 12),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _KpiCard(
                label: 'Pas',
                value: day.totalSteps != null
                    ? _formatSteps(day.totalSteps!)
                    : '--',
                icon: Icons.directions_walk,
                color: const Color(0xFF00E5A0),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _KpiCard(
                label: 'Distance',
                value: day.distanceKm != null
                    ? '${day.distanceKm!.toStringAsFixed(2)} km'
                    : '--',
                icon: Icons.straighten,
                color: colors.info,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: _KpiCard(
                label: 'Cal. actives',
                value: day.activeCaloriesKcal != null
                    ? '${day.activeCaloriesKcal!.toStringAsFixed(0)} kcal'
                    : '--',
                icon: Icons.local_fire_department,
                color: const Color(0xFFFF9500),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _KpiCard(
                label: 'Cal. totales',
                value: day.totalCaloriesKcal != null
                    ? '${day.totalCaloriesKcal!.toStringAsFixed(0)} kcal'
                    : '--',
                icon: Icons.bolt,
                color: const Color(0xFFFF6B35),
              ),
            ),
          ],
        ),
      ],
    );
  }

  static String _formatSteps(double steps) {
    if (steps >= 1000) {
      return '${(steps / 1000).toStringAsFixed(1)}k';
    }
    return steps.toStringAsFixed(0);
  }
}

class _KpiCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _KpiCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withAlpha(30),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 11,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Step Goal Card ────────────────────────────────────────────────────────────

class _StepGoalCard extends StatelessWidget {
  final ActivityDayResponse day;

  const _StepGoalCard({required this.day});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final steps = day.totalSteps ?? 0;
    final progress = (steps / _kStepGoal).clamp(0.0, 1.0);
    final pct = (progress * 100).toStringAsFixed(0);
    final achieved = steps >= _kStepGoal;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: achieved
              ? colors.accent.withAlpha(80)
              : colors.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                achieved
                    ? Icons.check_circle
                    : Icons.directions_walk_outlined,
                color: achieved ? colors.accent : colors.textMuted,
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                'Objectif de pas',
                style: TextStyle(
                  color: colors.text,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              Text(
                '$pct%',
                style: TextStyle(
                  color: achieved ? colors.accent : colors.textSecondary,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: colors.border,
              valueColor: AlwaysStoppedAnimation<Color>(
                achieved ? colors.accent : colors.info,
              ),
              minHeight: 10,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                '${steps.toStringAsFixed(0)} pas',
                style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 12,
                ),
              ),
              const Spacer(),
              Text(
                'Objectif: ${_kStepGoal.toStringAsFixed(0)}',
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Hourly Steps Card ─────────────────────────────────────────────────────────

class _HourlyStepsCard extends StatelessWidget {
  final ActivityDayResponse day;

  const _HourlyStepsCard({required this.day});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final maxSteps = day.maxHourlySteps;

    // Build 24-slot map
    final stepMap = <int, double>{};
    for (final h in day.hourlySteps) {
      stepMap[h.hour] = h.steps;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Pas par heure',
            style: TextStyle(
              color: colors.text,
              fontSize: 15,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 60,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(24, (hour) {
                final steps = stepMap[hour] ?? 0.0;
                final ratio = (steps / maxSteps).clamp(0.0, 1.0);
                final barH = 50.0 * ratio + 2.0;
                final hasSteps = steps > 0;

                return Expanded(
                  child: Container(
                    height: barH,
                    margin: const EdgeInsets.symmetric(horizontal: 1),
                    decoration: BoxDecoration(
                      color: hasSteps
                          ? colors.accent.withAlpha(200)
                          : colors.border,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Text('0h',
                  style: TextStyle(
                      color: colors.textMuted, fontSize: 10)),
              const Spacer(),
              Text('12h',
                  style: TextStyle(
                      color: colors.textMuted, fontSize: 10)),
              const Spacer(),
              Text('23h',
                  style: TextStyle(
                      color: colors.textMuted, fontSize: 10)),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Heart Rate Row ────────────────────────────────────────────────────────────

class _HeartRateRow extends StatelessWidget {
  final ActivityDayResponse day;

  const _HeartRateRow({required this.day});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    final avgHr = day.avgHeartRateBpm;
    final restHr = day.restingHeartRateBpm;

    if (avgHr == null && restHr == null) return const SizedBox.shrink();

    return Row(
      children: [
        if (avgHr != null)
          Expanded(
            child: _HrCard(
              label: 'FC moyenne',
              value: '${avgHr.toStringAsFixed(0)} bpm',
              icon: Icons.favorite,
              color: colors.danger,
            ),
          ),
        if (avgHr != null && restHr != null)
          const SizedBox(width: 10),
        if (restHr != null)
          Expanded(
            child: _HrCard(
              label: 'FC repos',
              value: '${restHr.toStringAsFixed(0)} bpm',
              icon: Icons.bedtime_outlined,
              color: const Color(0xFFAA80FF),
            ),
          ),
      ],
    );
  }
}

class _HrCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _HrCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withAlpha(30),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 11,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Period Summary Card ───────────────────────────────────────────────────────

class _PeriodSummaryCard extends StatelessWidget {
  final ActivityPeriodResponse period;

  const _PeriodSummaryCard({required this.period});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Cette semaine',
            style: TextStyle(
              color: colors.text,
              fontSize: 15,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _PeriodStat(
                  label: 'Pas/jour',
                  value: period.avgDailySteps != null
                      ? _formatSteps(period.avgDailySteps!)
                      : '--',
                  color: colors.accent,
                ),
              ),
              Expanded(
                child: _PeriodStat(
                  label: 'Pas totaux',
                  value: period.totalSteps != null
                      ? _formatSteps(period.totalSteps!)
                      : '--',
                  color: colors.info,
                ),
              ),
              Expanded(
                child: _PeriodStat(
                  label: 'Jours objectif',
                  value: period.goalDaysCount != null
                      ? '${period.goalDaysCount}d'
                      : '--',
                  color: const Color(0xFF34C759),
                ),
              ),
            ],
          ),
          if (period.totalDistanceKm != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                Icon(Icons.route_outlined,
                    size: 14, color: colors.textMuted),
                const SizedBox(width: 6),
                Text(
                  'Distance totale\u00a0: ${period.totalDistanceKm!.toStringAsFixed(1)} km',
                  style: TextStyle(
                    color: colors.textSecondary,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ],
          // Mini bar chart for entries
          if (period.entries.isNotEmpty) ...[
            const SizedBox(height: 12),
            _PeriodEntriesChart(entries: period.entries),
          ],
        ],
      ),
    );
  }

  static String _formatSteps(double steps) {
    if (steps >= 1000) {
      return '${(steps / 1000).toStringAsFixed(1)}k';
    }
    return steps.toStringAsFixed(0);
  }
}

class _PeriodStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _PeriodStat({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(color: colors.textMuted, fontSize: 10),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _PeriodEntriesChart extends StatelessWidget {
  final List<ActivityPeriodEntry> entries;

  const _PeriodEntriesChart({required this.entries});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    double maxSteps = 1;
    for (final e in entries) {
      if ((e.steps ?? 0) > maxSteps) maxSteps = e.steps!;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Pas quotidiens',
          style: TextStyle(color: colors.textMuted, fontSize: 11),
        ),
        const SizedBox(height: 6),
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: entries.map((e) {
            final steps = e.steps ?? 0;
            final ratio = (steps / maxSteps).clamp(0.0, 1.0);
            final barH = 40.0 * ratio + 4.0;
            final goalReached = steps >= _kStepGoal;

            return Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Container(
                    height: barH,
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    decoration: BoxDecoration(
                      color: goalReached
                          ? colors.accent.withAlpha(200)
                          : colors.info.withAlpha(140),
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    e.date.length >= 5 ? e.date.substring(5) : e.date,
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 8,
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ],
    );
  }
}

// ── Error View ────────────────────────────────────────────────────────────────

class _ActivityError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ActivityError({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.directions_walk_outlined,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Donn\u00e9es d\u2019activit\u00e9 non disponibles',
              style: TextStyle(color: colors.text, fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('R\u00e9essayer'),
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
