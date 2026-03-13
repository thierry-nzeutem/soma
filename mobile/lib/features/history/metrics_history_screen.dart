/// Ecran Historique Metriques — graphiques fl_chart (LOT 6).
///
/// Selecteur de periode (7 / 30 / 90 jours).
/// Graphiques ligne : poids, calories, proteines, hydratation, HRV.
library;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/daily_metrics.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'history_notifier.dart';

class MetricsHistoryScreen extends ConsumerWidget {
  const MetricsHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(historyProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Historique',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(historyProvider.notifier).refresh(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Selecteur de periode
          _PeriodSelector(
            selected: state.period,
            onChanged: (p) =>
                ref.read(historyProvider.notifier).setPeriod(p),
          ),
          // Corps
          Expanded(
            child: state.data.when(
              loading: () => Center(
                child:
                    CircularProgressIndicator(color: colors.accent),
              ),
              error: (err, _) => Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.cloud_off_rounded,
                        size: 48, color: colors.textMuted),
                    const SizedBox(height: 12),
                    Text(
                      'Erreur : $err',
                      style: TextStyle(color: colors.textSecondary),
                    ),
                  ],
                ),
              ),
              data: (history) => history.isEmpty
                  ? const _EmptyState()
                  : _HistoryCharts(history: history),
            ),
          ),
        ],
      ),
    );
  }
}

// -- Selecteur -----------------------------------------------------------------

class _PeriodSelector extends StatelessWidget {
  final HistoryPeriod selected;
  final ValueChanged<HistoryPeriod> onChanged;

  const _PeriodSelector(
      {required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: HistoryPeriod.values.map((p) {
          final isSelected = p == selected;
          return Expanded(
            child: GestureDetector(
              onTap: () => onChanged(p),
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 4),
                padding: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  color: isSelected
                      ? colors.accent.withOpacity(0.12)
                      : colors.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isSelected
                        ? colors.accent
                        : const Color(0xFF2A2A2A),
                  ),
                ),
                child: Center(
                  child: Text(
                    p.label,
                    style: TextStyle(
                      color: isSelected
                          ? colors.accent
                          : colors.textSecondary,
                      fontSize: 13,
                      fontWeight: isSelected
                          ? FontWeight.w600
                          : FontWeight.normal,
                    ),
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// -- Graphiques ----------------------------------------------------------------

class _HistoryCharts extends StatelessWidget {
  final List<DailyMetrics> history;

  const _HistoryCharts({required this.history});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final sorted = [...history]
      ..sort((a, b) => a.metricsDate.compareTo(b.metricsDate));

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      children: [
        _LineChartCard(
          title: 'Poids',
          unit: 'kg',
          color: colors.info,
          dataPoints: sorted
              .map((m) => FlSpot(
                    sorted.indexOf(m).toDouble(),
                    m.weightKg ?? 0,
                  ))
              .where((s) => s.y > 0)
              .toList(),
          labels: sorted.map((m) => m.metricsDate.substring(5)).toList(),
        ),
        const SizedBox(height: 16),
        _LineChartCard(
          title: 'Calories consommees',
          unit: 'kcal',
          color: const Color(0xFFFF6B6B),
          dataPoints: sorted
              .map((m) => FlSpot(
                    sorted.indexOf(m).toDouble(),
                    m.caloriesConsumed ?? 0,
                  ))
              .where((s) => s.y > 0)
              .toList(),
          labels: sorted.map((m) => m.metricsDate.substring(5)).toList(),
        ),
        const SizedBox(height: 16),
        _LineChartCard(
          title: 'Proteines',
          unit: 'g',
          color: const Color(0xFFFFB347),
          dataPoints: sorted
              .map((m) => FlSpot(
                    sorted.indexOf(m).toDouble(),
                    m.proteinG ?? 0,
                  ))
              .where((s) => s.y > 0)
              .toList(),
          labels: sorted.map((m) => m.metricsDate.substring(5)).toList(),
        ),
        const SizedBox(height: 16),
        _LineChartCard(
          title: 'Hydratation',
          unit: 'L',
          color: colors.info,
          dataPoints: sorted
              .map((m) => FlSpot(
                    sorted.indexOf(m).toDouble(),
                    m.hydrationMl != null ? m.hydrationMl! / 1000 : 0,
                  ))
              .where((s) => s.y > 0)
              .toList(),
          labels: sorted.map((m) => m.metricsDate.substring(5)).toList(),
        ),
        const SizedBox(height: 16),
        _LineChartCard(
          title: 'HRV',
          unit: 'ms',
          color: colors.accent,
          dataPoints: sorted
              .map((m) => FlSpot(
                    sorted.indexOf(m).toDouble(),
                    m.hrvMs ?? 0,
                  ))
              .where((s) => s.y > 0)
              .toList(),
          labels: sorted.map((m) => m.metricsDate.substring(5)).toList(),
        ),
      ],
    );
  }
}

class _LineChartCard extends StatelessWidget {
  final String title;
  final String unit;
  final Color color;
  final List<FlSpot> dataPoints;
  final List<String> labels;

  const _LineChartCard({
    required this.title,
    required this.unit,
    required this.color,
    required this.dataPoints,
    required this.labels,
  });

  @override
  Widget build(BuildContext context) {
    if (dataPoints.isEmpty) return const SizedBox.shrink();

    final colors = context.somaColors;
    final minY = dataPoints.map((s) => s.y).reduce((a, b) => a < b ? a : b);
    final maxY = dataPoints.map((s) => s.y).reduce((a, b) => a > b ? a : b);
    final padding = (maxY - minY) * 0.15;

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
          Row(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  color: colors.text,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              Text(
                unit,
                style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 120,
            child: LineChart(
              LineChartData(
                minY: (minY - padding).clamp(0, double.infinity),
                maxY: maxY + padding,
                lineBarsData: [
                  LineChartBarData(
                    spots: dataPoints,
                    isCurved: true,
                    color: color,
                    barWidth: 2,
                    dotData: const FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      color: color.withOpacity(0.08),
                    ),
                  ),
                ],
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (_) => FlLine(
                    color: colors.border,
                    strokeWidth: 1,
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: (dataPoints.length / 4).ceilToDouble(),
                      getTitlesWidget: (value, _) {
                        final idx = value.toInt();
                        if (idx < 0 || idx >= labels.length) {
                          return const SizedBox.shrink();
                        }
                        return Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(
                            labels[idx],
                            style: TextStyle(
                              color: colors.textMuted,
                              fontSize: 9,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipItems: (spots) => spots
                        .map((s) => LineTooltipItem(
                              '${s.y.toStringAsFixed(1)} $unit',
                              TextStyle(
                                color: color,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ))
                        .toList(),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// -- Empty ----------------------------------------------------------------------

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.show_chart_rounded, size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Aucune donnee pour cette periode',
              style: TextStyle(color: colors.textSecondary, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
