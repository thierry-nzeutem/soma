/// HeartRateScreen -- Analytiques de frequence cardiaque SOMA.
///
/// Affiche :
///   - Date du jour
///   - KPI cards : FC repos, moy eveil, moy sommeil, max, min
///   - Graphe 24h en barres (normalisation 40-180 bpm)
///   - Evenements notables (chips haute/basse FC)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/heart_rate_analytics.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'heart_rate_notifier.dart';

// -- Couleurs HR ---------------------------------------------------------------

const _kHrRed = Color(0xFFFF3B30);
const _kAwakeColor = Color(0xFFFF6B6B);
const _kSleepColor = Color(0xFF6B7FFF);
const _kRestingColor = Color(0xFF9B72CF);

Color _zoneColor(double bpm) {
  if (bpm < 60) return const Color(0xFF6B7FFF);
  if (bpm <= 100) return const Color(0xFF00E5A0);
  return const Color(0xFFFF9500);
}

String _todayLabel() {
  final now = DateTime.now();
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];
  return '${months[now.month - 1]} ${now.day}, ${now.year}';
}

// -- Screen --------------------------------------------------------------------

class HeartRateScreen extends ConsumerWidget {
  const HeartRateScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(hrAnalyticsProvider);
    final timelineAsync = ref.watch(hrTimelineProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Heart Rate',
        showBackButton: true,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.textSecondary),
            tooltip: 'Refresh',
            onPressed: () {
              ref.read(hrAnalyticsProvider.notifier).refresh();
              ref.read(hrTimelineProvider.notifier).refresh();
            },
          ),
        ],
      ),
      body: analyticsAsync.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (e, _) => _ErrorView(
          message: 'Could not load heart rate data',
          onRetry: () {
            ref.read(hrAnalyticsProvider.notifier).refresh();
            ref.read(hrTimelineProvider.notifier).refresh();
          },
        ),
        data: (analytics) {
          if (analytics == null) return const _EmptyView();
          return _HeartRateBody(
            analytics: analytics,
            timelineAsync: timelineAsync,
          );
        },
      ),
    );
  }
}

// -- Corps principal -----------------------------------------------------------

class _HeartRateBody extends StatelessWidget {
  final HRAnalytics analytics;
  final AsyncValue<HRTimeline?> timelineAsync;

  const _HeartRateBody({
    required this.analytics,
    required this.timelineAsync,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return RefreshIndicator(
      color: colors.accent,
      backgroundColor: colors.surface,
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        children: [
          // Date
          Text(
            _todayLabel(),
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),

          // KPI top row: resting + awake
          Row(
            children: [
              Expanded(
                child: _KpiCard(
                  label: 'Resting HR',
                  value: analytics.restingHrBpm != null
                      ? analytics.restingHrBpm!.toStringAsFixed(0)
                      : '--',
                  unit: 'bpm',
                  icon: Icons.favorite_rounded,
                  color: _kHrRed,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _KpiCard(
                  label: 'Avg Awake',
                  value: analytics.avgAwakeBpm != null
                      ? analytics.avgAwakeBpm!.toStringAsFixed(0)
                      : '--',
                  unit: 'bpm',
                  icon: Icons.wb_sunny_rounded,
                  color: _kAwakeColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // KPI second row: sleep + max + min
          Row(
            children: [
              Expanded(
                child: _KpiCard(
                  label: 'Avg Sleep',
                  value: analytics.avgSleepBpm != null
                      ? analytics.avgSleepBpm!.toStringAsFixed(0)
                      : '--',
                  unit: 'bpm',
                  icon: Icons.bedtime_rounded,
                  color: _kSleepColor,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _KpiCard(
                  label: 'Max',
                  value: analytics.maxBpm != null
                      ? analytics.maxBpm!.toStringAsFixed(0)
                      : '--',
                  unit: 'bpm',
                  icon: Icons.arrow_upward_rounded,
                  color: _kHrRed,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _KpiCard(
                  label: 'Min',
                  value: analytics.minBpm != null
                      ? analytics.minBpm!.toStringAsFixed(0)
                      : '--',
                  unit: 'bpm',
                  icon: Icons.arrow_downward_rounded,
                  color: _kRestingColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Timeline 24h
          const _SectionHeader(title: '24h Timeline'),
          const SizedBox(height: 10),
          timelineAsync.when(
            loading: () => SizedBox(
              height: 120,
              child: Center(
                child: CircularProgressIndicator(
                  color: colors.accent,
                  strokeWidth: 2,
                ),
              ),
            ),
            error: (_, __) => SizedBox(
              height: 60,
              child: Center(
                child: Text(
                  'Timeline unavailable',
                  style: TextStyle(color: colors.textMuted, fontSize: 13),
                ),
              ),
            ),
            data: (timeline) => _TimelineChart(timeline: timeline),
          ),
          const SizedBox(height: 8),
          _ZoneLegend(),
          const SizedBox(height: 24),

          // Evenements notables
          if (analytics.hasEvents) ...[
            const _SectionHeader(title: 'Notable Events'),
            const SizedBox(height: 10),
            if (analytics.highRestingEvents.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  'High resting HR',
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: analytics.highRestingEvents
                    .map((e) => _EventChip(event: e, isHigh: true))
                    .toList(),
              ),
              const SizedBox(height: 12),
            ],
            if (analytics.lowRestingEvents.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  'Low resting HR',
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: analytics.lowRestingEvents
                    .map((e) => _EventChip(event: e, isHigh: false))
                    .toList(),
              ),
            ],
            const SizedBox(height: 16),
          ],

          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// -- KPI Card ------------------------------------------------------------------

class _KpiCard extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  final IconData icon;
  final Color color;

  const _KpiCard({
    required this.label,
    required this.value,
    required this.unit,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: TextStyle(
                  color: value == '--' ? colors.textMuted : color,
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.5,
                ),
              ),
              if (value != '--') ...[
                const SizedBox(width: 2),
                Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text(
                    unit,
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 10,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

// -- Timeline 24h bar chart -----------------------------------------------------

class _TimelineChart extends StatelessWidget {
  final HRTimeline? timeline;
  const _TimelineChart({this.timeline});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    if (timeline == null || timeline!.points.isEmpty) {
      return Container(
        height: 120,
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: colors.border),
        ),
        child: Center(
          child: Text(
            'No data available',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
        ),
      );
    }

    // Build a map from hour -> point for quick lookup (only non-null hours shown)
    final hourlyPoints = timeline!.hourlyPoints;

    const double minBpmRange = 40.0;
    const double maxBpmRange = 180.0;
    const double chartHeight = 100.0;

    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      padding: const EdgeInsets.fromLTRB(8, 12, 8, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: chartHeight,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(24, (hour) {
                final point = hourlyPoints[hour];
                final bpm = point?.avgBpm;

                if (bpm == null) {
                  // Empty slot - tiny baseline
                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 1),
                      child: Align(
                        alignment: Alignment.bottomCenter,
                        child: Container(
                          height: 4,
                          decoration: BoxDecoration(
                            color: colors.surfaceVariant,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                    ),
                  );
                }

                final normalized =
                    ((bpm - minBpmRange) / (maxBpmRange - minBpmRange))
                        .clamp(0.04, 1.0);
                final barHeight = normalized * chartHeight;
                final barColor = _zoneColor(bpm);

                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 1),
                    child: Align(
                      alignment: Alignment.bottomCenter,
                      child: Container(
                        height: barHeight,
                        decoration: BoxDecoration(
                          color: barColor,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 6),
          // Labels for key hours
          Row(
            children: List.generate(24, (hour) {
              final show = hour == 0 ||
                  hour == 6 ||
                  hour == 12 ||
                  hour == 18 ||
                  hour == 23;
              return Expanded(
                child: show
                    ? Text(
                        '$hour',
                        style: TextStyle(
                          color: colors.textMuted,
                          fontSize: 9,
                        ),
                        textAlign: TextAlign.center,
                      )
                    : const SizedBox.shrink(),
              );
            }),
          ),
        ],
      ),
    );
  }
}

// -- Zone legend ---------------------------------------------------------------

class _ZoneLegend extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final zones = [
      (color: const Color(0xFF6B7FFF), label: '< 60 bpm'),
      (color: const Color(0xFF00E5A0), label: '60-100 bpm'),
      (color: const Color(0xFFFF9500), label: '> 100 bpm'),
    ];
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: zones.map((z) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: z.color,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 4),
              Text(
                z.label,
                style: TextStyle(color: colors.textMuted, fontSize: 11),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

// -- Event chip ----------------------------------------------------------------

class _EventChip extends StatelessWidget {
  final HREvent event;
  final bool isHigh;
  const _EventChip({required this.event, required this.isHigh});

  @override
  Widget build(BuildContext context) {
    final chipColor = isHigh ? _kHrRed : _kSleepColor;

    String timeLabel;
    try {
      final dt = DateTime.parse(event.recordedAt);
      final hh = dt.hour.toString().padLeft(2, '0');
      final mm = dt.minute.toString().padLeft(2, '0');
      timeLabel = '$hh:$mm';
    } catch (_) {
      timeLabel = event.recordedAt.isNotEmpty ? event.recordedAt : '--';
    }

    return Chip(
      backgroundColor: chipColor.withOpacity(0.12),
      side: BorderSide(color: chipColor.withOpacity(0.35)),
      avatar: Icon(
        isHigh ? Icons.arrow_upward_rounded : Icons.arrow_downward_rounded,
        color: chipColor,
        size: 14,
      ),
      label: Text(
        '${event.value.toStringAsFixed(0)} bpm  $timeLabel',
        style: TextStyle(
          color: chipColor,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

// -- Section header ------------------------------------------------------------

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title, super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Text(
      title,
      style: TextStyle(
        color: colors.text,
        fontSize: 16,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}

// -- Utility views -------------------------------------------------------------

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, size: 56, color: colors.danger),
            const SizedBox(height: 16),
            Text(
              message,
              style: TextStyle(color: colors.textSecondary, fontSize: 15),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _kHrRed,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.favorite_border_rounded, size: 64, color: colors.textMuted),
          const SizedBox(height: 16),
          Text(
            'No heart rate data available',
            style: TextStyle(color: colors.textSecondary, fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            'Connect a sensor to start tracking.',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
