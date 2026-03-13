/// SOMA — Body Composition Screen.
///
/// Affiche la composition corporelle et le poids avec selecteur de periode.
/// Consomme compositionTrendProvider(period) et weightTrendProvider.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/body_composition.dart';
import '../../core/theme/soma_colors.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/metric_card.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'body_composition_notifier.dart';

// ── Period config ─────────────────────────────────────────────────────────────

const _kPeriods = <(String, String)>[
  ('Semaine', 'week'),
  ('Mois', 'month'),
  ('Trimestre', 'quarter'),
  ('Semestre', 'semester'),
  ('Ann\u00e9e', 'year'),
];

// ── Screen ────────────────────────────────────────────────────────────────────

class BodyCompositionScreen extends ConsumerStatefulWidget {
  const BodyCompositionScreen({super.key});

  @override
  ConsumerState<BodyCompositionScreen> createState() =>
      _BodyCompositionScreenState();
}

class _BodyCompositionScreenState
    extends ConsumerState<BodyCompositionScreen> {
  int _periodIndex = 0;

  String get _period => _kPeriods[_periodIndex].$2;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final compositionAsync = ref.watch(compositionTrendProvider(_period));
    final weightAsync = ref.watch(weightTrendProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Composition corporelle',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () {
              ref.invalidate(compositionTrendProvider(_period));
              ref.invalidate(weightTrendProvider);
            },
            tooltip: 'Actualiser',
          ),
        ],
      ),
      body: Column(
        children: [
          _PeriodSelector(
            selectedIndex: _periodIndex,
            onSelected: (i) => setState(() => _periodIndex = i),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                weightAsync.when(
                  loading: () => _LoadingCard(color: colors.accent),
                  error: (e, _) => _ErrorCard(
                    message: e.toString(),
                    onRetry: () => ref.invalidate(weightTrendProvider),
                  ),
                  data: (weight) => _WeightSection(data: weight),
                ),
                const SizedBox(height: 20),
                compositionAsync.when(
                  loading: () => _LoadingCard(color: colors.accent),
                  error: (e, _) => _ErrorCard(
                    message: e.toString(),
                    onRetry: () =>
                        ref.invalidate(compositionTrendProvider(_period)),
                  ),
                  data: (comp) => _CompositionSection(data: comp),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Period Selector ───────────────────────────────────────────────────────────

class _PeriodSelector extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int> onSelected;

  const _PeriodSelector({
    required this.selectedIndex,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      color: colors.surface,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: List.generate(_kPeriods.length, (i) {
          final label = _kPeriods[i].$1;
          final isSelected = i == selectedIndex;

          return Expanded(
            child: GestureDetector(
              onTap: () => onSelected(i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: const EdgeInsets.symmetric(horizontal: 3),
                padding: const EdgeInsets.symmetric(vertical: 7),
                decoration: BoxDecoration(
                  color: isSelected
                      ? const Color(0xFF9B72CF)
                      : colors.background,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isSelected
                        ? const Color(0xFF9B72CF)
                        : colors.border,
                  ),
                ),
                child: Center(
                  child: Text(
                    label,
                    style: TextStyle(
                      color: isSelected ? Colors.white : colors.textMuted,
                      fontSize: 12,
                      fontWeight: isSelected
                          ? FontWeight.w600
                          : FontWeight.w400,
                    ),
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

// ── Weight Section ────────────────────────────────────────────────────────────

class _WeightSection extends StatelessWidget {
  final WeightTrendResponse data;

  const _WeightSection({required this.data});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final latest = data.latest;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(title: 'Poids', icon: Icons.monitor_weight_outlined),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 1.4,
          children: [
            MetricCard(
              label: 'Poids actuel',
              value: latest?.weightKg != null
                  ? latest!.weightKg!.toStringAsFixed(1)
                  : '--',
              unit: 'kg',
              icon: Icons.monitor_weight_outlined,
              accentColor: const Color(0xFF00E5A0),
            ),
            MetricCard(
              label: 'IMC',
              value: latest?.bmi != null
                  ? latest!.bmi!.toStringAsFixed(1)
                  : '--',
              icon: Icons.straighten,
              accentColor: _bmiColor(context, latest?.bmi),
            ),
            MetricCard(
              label: '\u00c2ge m\u00e9tabolique',
              value: latest?.metabolicAge?.toString() ?? '--',
              unit: 'ans',
              icon: Icons.timer_outlined,
              accentColor: const Color(0xFF9B72CF),
            ),
            MetricCard(
              label: 'Poids moyen',
              value: data.avgWeightKg != null
                  ? data.avgWeightKg!.toStringAsFixed(1)
                  : '--',
              unit: 'kg',
              icon: Icons.equalizer,
              accentColor: colors.info,
            ),
          ],
        ),
        if (data.points.length >= 2) ...[
          const SizedBox(height: 12),
          _WeightBarChart(points: data.points),
        ],
      ],
    );
  }

  Color _bmiColor(BuildContext context, double? bmi) {
    if (bmi == null) return context.somaColors.textMuted;
    if (bmi < 18.5) return context.somaColors.info;
    if (bmi < 25) return context.somaColors.success;
    if (bmi < 30) return context.somaColors.warning;
    return context.somaColors.danger;
  }
}

// ── Weight Bar Chart ──────────────────────────────────────────────────────────

class _WeightBarChart extends StatelessWidget {
  final List<WeightPoint> points;

  const _WeightBarChart({required this.points});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final recent = points.length > 7
        ? points.sublist(points.length - 7)
        : points;

    double minW = double.infinity;
    double maxW = 0;
    for (final p in recent) {
      if (p.weightKg != null) {
        if (p.weightKg! < minW) minW = p.weightKg!;
        if (p.weightKg! > maxW) maxW = p.weightKg!;
      }
    }
    if (minW == double.infinity) minW = 0;
    final range = (maxW - minW).clamp(0.5, double.infinity);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Derni\u00e8res ${recent.length} mesures',
            style: TextStyle(color: colors.textMuted, fontSize: 12),
          ),
          const SizedBox(height: 10),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: recent.map((p) {
              final w = p.weightKg;
              final ratio = w != null
                  ? ((w - minW) / range).clamp(0.1, 1.0)
                  : 0.0;
              final barH = 40.0 * ratio + 8.0;

              return Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Container(
                      height: barH,
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      decoration: BoxDecoration(
                        color: colors.accent.withAlpha(180),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      w != null ? w.toStringAsFixed(0) : '--',
                      style: TextStyle(
                        color: colors.textMuted,
                        fontSize: 9,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

// ── Composition Section ───────────────────────────────────────────────────────

class _CompositionSection extends StatelessWidget {
  final CompositionTrendResponse data;

  const _CompositionSection({required this.data});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final allPoints = data.points;
    final recent = allPoints.length > 5
        ? allPoints.sublist(allPoints.length - 5)
        : allPoints;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(title: 'Segmentation corporelle', icon: Icons.pie_chart_outline),
        const SizedBox(height: 4),
        Text(
          'Moyennes de la p\u00e9riode',
          style: TextStyle(color: colors.textMuted, fontSize: 12),
        ),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 1.4,
          children: [
            MetricCard(
              label: 'Masse grasse',
              value: data.avgBodyFatPct != null
                  ? data.avgBodyFatPct!.toStringAsFixed(1) : '--',
              unit: '%',
              icon: Icons.bubble_chart_outlined,
              accentColor: const Color(0xFFFF9500),
              progressFraction: data.avgBodyFatPct != null
                  ? (data.avgBodyFatPct! / 40).clamp(0.0, 1.0) : null,
            ),
            MetricCard(
              label: 'Masse musculaire',
              value: data.avgMuscleMassPct != null
                  ? data.avgMuscleMassPct!.toStringAsFixed(1) : '--',
              unit: '%',
              icon: Icons.fitness_center,
              accentColor: const Color(0xFF00E5A0),
              progressFraction: data.avgMuscleMassPct != null
                  ? (data.avgMuscleMassPct! / 60).clamp(0.0, 1.0) : null,
            ),
            MetricCard(
              label: 'Hydratation',
              value: data.avgWaterPct != null
                  ? data.avgWaterPct!.toStringAsFixed(1) : '--',
              unit: '%',
              icon: Icons.water_drop_outlined,
              accentColor: const Color(0xFF00B4D8),
              progressFraction: data.avgWaterPct != null
                  ? (data.avgWaterPct! / 70).clamp(0.0, 1.0) : null,
            ),
            MetricCard(
              label: 'Graisse visc\u00e9rale',
              value: data.avgVisceralFatIndex != null
                  ? data.avgVisceralFatIndex!.toStringAsFixed(1) : '--',
              icon: Icons.warning_amber_outlined,
              accentColor: _visceralColor(colors, data.avgVisceralFatIndex),
            ),
            MetricCard(
              label: 'Masse osseuse',
              value: data.avgBoneMassKg != null
                  ? data.avgBoneMassKg!.toStringAsFixed(2) : '--',
              unit: 'kg',
              icon: Icons.crisis_alert,
              accentColor: const Color(0xFF9B72CF),
            ),
            MetricCard(
              label: '\u00c2ge m\u00e9tabolique',
              value: data.avgMetabolicAge?.toString() ?? '--',
              unit: 'ans',
              icon: Icons.timer_outlined,
              accentColor: const Color(0xFF9B72CF),
            ),
          ],
        ),
        if (recent.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(
            'Mesures r\u00e9centes (${recent.length})',
            style: TextStyle(
              color: colors.text, fontSize: 15, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 10),
          ...recent.map(
            (p) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _CompositionPointRow(point: p),
            ),
          ),
        ],
      ],
    );
  }

  Color _visceralColor(SomaColors colors, double? index) {
    if (index == null) return colors.textMuted;
    if (index <= 9) return colors.success;
    if (index <= 14) return colors.warning;
    return colors.danger;
  }
}

// ── Section Header ────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;
  const _SectionHeader({required this.title, required this.icon});
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(children: [
      Icon(icon, color: const Color(0xFF9B72CF), size: 18),
      const SizedBox(width: 8),
      Text(title, style: TextStyle(
        color: colors.text, fontSize: 16, fontWeight: FontWeight.w600)),
    ]);
  }
}

// ── Composition Point Row ─────────────────────────────────────────────────────

class _CompositionPointRow extends StatelessWidget {
  final CompositionPoint point;

  const _CompositionPointRow({required this.point});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            point.date,
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _MiniStat(
                label: 'Grasse',
                value: point.bodyFatPct,
                unit: '%',
                color: const Color(0xFFFF9500),
              ),
              _MiniStat(
                label: 'Muscle',
                value: point.muscleMassPct,
                unit: '%',
                color: const Color(0xFF00E5A0),
              ),
              _MiniStat(
                label: 'Eau',
                value: point.waterPct,
                unit: '%',
                color: colors.info,
              ),
              _MiniStat(
                label: 'Visc.',
                value: point.visceralFatIndex,
                unit: '',
                color: colors.warning,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  final String label;
  final double? value;
  final String unit;
  final Color color;

  const _MiniStat({
    required this.label,
    required this.value,
    required this.unit,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            style: TextStyle(color: colors.textMuted, fontSize: 10),
          ),
          const SizedBox(height: 2),
          Text(
            value != null
                ? '${value!.toStringAsFixed(1)}$unit'.trim()
                : '--',
            style: TextStyle(
              color: value != null ? color : colors.textMuted,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

class _LoadingCard extends StatelessWidget {
  final Color color;

  const _LoadingCard({required this.color});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: CircularProgressIndicator(color: color),
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorCard({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        children: [
          Icon(Icons.error_outline, color: colors.danger, size: 36),
          const SizedBox(height: 8),
          Text(
            message,
            style: TextStyle(color: colors.textSecondary, fontSize: 12),
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh, size: 16),
            label: const Text('R\u00e9essayer'),
            style: ElevatedButton.styleFrom(
              backgroundColor: colors.accent,
              foregroundColor: Colors.black,
            ),
          ),
        ],
      ),
    );
  }
}
