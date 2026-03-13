/// HRV Screen - Variabilite cardiaque et score de stress SOMA.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'hrv_notifier.dart';

Color _scoreColor(BuildContext ctx, int? score) {
  final c = ctx.somaColors;
  if (score == null) return c.textMuted;
  if (score >= 75) return c.success;
  if (score >= 50) return c.warning;
  return c.danger;
}

Color _stressColor(BuildContext ctx, String level) {
  final c = ctx.somaColors;
  switch (level) {
    case 'low': return c.success;
    case 'moderate': return c.warning;
    case 'high': return const Color(0xFFFF7043);
    case 'very_high': return c.danger;
    default: return c.textMuted;
  }
}

String _stressLabel(String level) {
  switch (level) {
    case 'low': return 'Low stress';
    case 'moderate': return 'Moderate stress';
    case 'high': return 'High stress';
    case 'very_high': return 'Very high stress';
    default: return 'Unknown';
  }
}

String _recoveryLabel(String indicator) {
  switch (indicator) {
    case 'optimal': return 'Optimal recovery';
    case 'good': return 'Good recovery';
    case 'fair': return 'Fair recovery';
    case 'poor': return 'Poor recovery';
    default: return 'Unknown';
  }
}

class HRVScreen extends ConsumerWidget {
  const HRVScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(hrvScoreProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'HRV & Stress',
        showBackButton: true,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.textSecondary),
            onPressed: () => ref.read(hrvScoreProvider.notifier).refresh(),
          ),
        ],
      ),
      body: async.when(
        loading: () => Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.error_outline, color: colors.danger, size: 40),
            const SizedBox(height: 12),
            Text('Could not load HRV data', style: TextStyle(color: colors.textMuted)),
            const SizedBox(height: 16),
            TextButton(onPressed: () => ref.read(hrvScoreProvider.notifier).refresh(), child: const Text('Retry')),
          ]),
        ),
        data: (hrv) => hrv == null || !hrv.hasData ? _EmptyView(colors: colors) : _HRVBody(hrv: hrv),
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  final dynamic colors;
  const _EmptyView({required this.colors});
  @override
  Widget build(BuildContext context) {
    final c = context.somaColors;
    return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.monitor_heart_outlined, size: 56, color: c.textMuted),
      const SizedBox(height: 16),
      Text('No HRV data', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: c.textSecondary)),
      const SizedBox(height: 8),
      Text('Connect a compatible wearable\nto measure HRV automatically', textAlign: TextAlign.center, style: TextStyle(color: c.textMuted, fontSize: 14)),
    ]));
  }
}

class _HRVBody extends StatelessWidget {
  final HRVScore hrv;
  const _HRVBody({required this.hrv});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final scoreColor = _scoreColor(context, hrv.hrvScore);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        // HRV Score hero
        Container(
          padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 16),
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: colors.border),
          ),
          child: Column(children: [
            Container(
              width: 110, height: 110,
              decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: scoreColor, width: 5)),
              child: Center(child: Text(
                hrv.hrvScore != null ? '${hrv.hrvScore}' : '--',
                style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: scoreColor),
              )),
            ),
            const SizedBox(height: 12),
            Text('HRV Score', style: TextStyle(color: colors.textSecondary, fontSize: 14)),
            const SizedBox(height: 16),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              _StatusChip(label: _stressLabel(hrv.stressLevel), color: _stressColor(context, hrv.stressLevel)),
              const SizedBox(width: 10),
              _StatusChip(label: _recoveryLabel(hrv.recoveryIndicator), color: colors.info),
            ]),
          ]),
        ),
        const SizedBox(height: 16),
        // Metric cards row
        Row(children: [
          Expanded(child: _MetricCard(label: 'Avg HRV', value: hrv.avgHrvMs != null ? '${hrv.avgHrvMs!.toStringAsFixed(0)} ms' : '--', icon: Icons.monitor_heart_rounded, color: colors.accent)),
          const SizedBox(width: 10),
          Expanded(child: _MetricCard(label: 'Resting HRV', value: hrv.restingHrvMs != null ? '${hrv.restingHrvMs!.toStringAsFixed(0)} ms' : '--', icon: Icons.favorite_rounded, color: colors.info)),
          const SizedBox(width: 10),
          Expanded(child: _TrendCard(trend7d: hrv.trend7d, colors: colors)),
        ]),
        const SizedBox(height: 16),
        // 7-day history chart
        if (hrv.history.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: colors.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: colors.border)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('7-day HRV trend', style: TextStyle(fontWeight: FontWeight.w600, color: colors.textSecondary, fontSize: 13)),
              const SizedBox(height: 16),
              SizedBox(height: 80, child: _HRVBarChart(points: hrv.history, colors: colors)),
            ]),
          ),
          const SizedBox(height: 16),
        ],
        // Baseline
        if (hrv.baseline7dMs != null)
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: colors.surface, borderRadius: BorderRadius.circular(10), border: Border.all(color: colors.border)),
            child: Row(children: [
              Icon(Icons.bar_chart_rounded, color: colors.textMuted, size: 18),
              const SizedBox(width: 8),
              Text('7-day baseline: ', style: TextStyle(color: colors.textMuted, fontSize: 13)),
              Text('${hrv.baseline7dMs!.toStringAsFixed(0)} ms', style: TextStyle(color: colors.textSecondary, fontWeight: FontWeight.w600, fontSize: 13)),
            ]),
          ),
        if (hrv.baseline7dMs != null) const SizedBox(height: 16),
        // Recommendation
        if (hrv.recommendation != null)
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: colors.info.withAlpha(20),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: colors.info.withAlpha(60)),
            ),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(Icons.lightbulb_outline_rounded, color: colors.info, size: 18),
              const SizedBox(width: 10),
              Expanded(child: Text(hrv.recommendation!, style: TextStyle(color: colors.textSecondary, fontSize: 13, height: 1.5))),
            ]),
          ),
        const SizedBox(height: 24),
      ]),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final Color color;
  const _StatusChip({required this.label, required this.color});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: color.withAlpha(30), borderRadius: BorderRadius.circular(20), border: Border.all(color: color.withAlpha(80))),
      child: Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _MetricCard({required this.label, required this.value, required this.icon, required this.color});
  @override
  Widget build(BuildContext context) {
    final c = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: c.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: c.border)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: color, size: 18),
        const SizedBox(height: 6),
        Text(value, style: TextStyle(color: c.textSecondary, fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(color: c.textMuted, fontSize: 11)),
      ]),
    );
  }
}

class _TrendCard extends StatelessWidget {
  final double? trend7d;
  final dynamic colors;
  const _TrendCard({required this.trend7d, required this.colors});
  @override
  Widget build(BuildContext context) {
    final c = context.somaColors;
    final isUp = trend7d != null && trend7d! > 0;
    final isDown = trend7d != null && trend7d! < 0;
    final trendColor = trend7d == null ? c.textMuted : (isUp ? c.success : c.danger);
    final icon = isUp ? Icons.trending_up_rounded : (isDown ? Icons.trending_down_rounded : Icons.trending_flat_rounded);
    final label = trend7d != null ? '${trend7d! > 0 ? '+' : ''}${trend7d!.toStringAsFixed(1)}%' : '--';
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: c.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: c.border)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: trendColor, size: 18),
        const SizedBox(height: 6),
        Text(label, style: TextStyle(color: trendColor, fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 2),
        Text('vs 7d avg', style: TextStyle(color: c.textMuted, fontSize: 11)),
      ]),
    );
  }
}

class _HRVBarChart extends StatelessWidget {
  final List<HRVDayPoint> points;
  final dynamic colors;
  const _HRVBarChart({required this.points, required this.colors});

  @override
  Widget build(BuildContext context) {
    final c = context.somaColors;
    final values = points.map((p) => p.avgHrvMs ?? 0.0).toList();
    final maxVal = values.isEmpty ? 1.0 : values.reduce((a, b) => a > b ? a : b).clamp(1.0, double.infinity);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: List.generate(points.length, (i) {
        final p = points[i];
        final val = p.avgHrvMs ?? 0.0;
        final ratio = val / maxVal;
        Color barColor;
        if (val >= 60) {
          barColor = c.success;
        } else if (val >= 40) {
          barColor = c.warning;
        } else {
          barColor = c.danger;
        }

        return Expanded(child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 2),
          child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
            Container(
              height: (ratio * 60).clamp(4, 60),
              decoration: BoxDecoration(color: barColor, borderRadius: BorderRadius.circular(3)),
            ),
            const SizedBox(height: 4),
            Text(p.date.substring(8), style: TextStyle(color: c.textMuted, fontSize: 9)),
          ]),
        ));
      }),
    );
  }
}
