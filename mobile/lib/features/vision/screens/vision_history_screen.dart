/// Écran historique des sessions Computer Vision (LOT 8).
///
/// Affiche la liste des sessions passées avec filtres exercice + période,
/// graphique de progression qualité et navigation vers le détail.
library;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/theme_extensions.dart';
import '../../../shared/widgets/soma_app_bar.dart';
import '../models/exercise_frame.dart';
import '../models/vision_session.dart';
import '../providers/vision_history_notifier.dart';

// ── Screen ────────────────────────────────────────────────────────────────────

class VisionHistoryScreen extends ConsumerWidget {
  const VisionHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final state = ref.watch(visionHistoryProvider);
    final notifier = ref.read(visionHistoryProvider.notifier);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Historique Vision',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.text),
            tooltip: 'Rafraîchir',
            onPressed: () => notifier.refresh(),
          ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Sélecteur période ─────────────────────────────────────────
          _PeriodSelector(
            selected: state.period,
            onChanged: notifier.setPeriod,
          ),

          // ── Filtre exercice ───────────────────────────────────────────
          _ExerciseFilterChips(
            selected: state.exerciseFilter,
            onChanged: notifier.setExerciseFilter,
          ),

          // ── Contenu ───────────────────────────────────────────────────
          Expanded(
            child: state.data.when(
              loading: () => LinearProgressIndicator(
                color: colors.accent,
                backgroundColor: colors.border,
              ),
              error: (e, _) => _ErrorHistoryView(message: e.toString()),
              data: (sessions) => sessions.isEmpty
                  ? const _EmptyHistoryView()
                  : _SessionList(
                      sessions: sessions,
                      exerciseFilter: state.exerciseFilter,
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Sélecteur période ─────────────────────────────────────────────────────────

class _PeriodSelector extends StatelessWidget {
  final VisionHistoryPeriod selected;
  final void Function(VisionHistoryPeriod) onChanged;

  const _PeriodSelector({
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      child: Row(
        children: VisionHistoryPeriod.values.map((p) {
          final isSelected = p == selected;
          final isLast = p == VisionHistoryPeriod.values.last;
          return Expanded(
            child: GestureDetector(
              onTap: () => onChanged(p),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: EdgeInsets.only(right: isLast ? 0 : 8),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: isSelected
                      ? colors.accent.withOpacity(0.15)
                      : colors.surface,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isSelected
                        ? colors.accent
                        : colors.border,
                  ),
                ),
                child: Text(
                  p.label,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: isSelected
                        ? colors.accent
                        : colors.textMuted,
                    fontWeight:
                        isSelected ? FontWeight.w700 : FontWeight.w400,
                    fontSize: 13,
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

// ── Filtre exercice (chips horizontales) ──────────────────────────────────────

class _ExerciseFilterChips extends StatelessWidget {
  final SupportedExercise? selected;
  final void Function(SupportedExercise?) onChanged;

  const _ExerciseFilterChips({
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 56,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        children: [
          // Chip "Tous"
          _FilterChip(
            label: 'Tous',
            isSelected: selected == null,
            onTap: () => onChanged(null),
          ),
          const SizedBox(width: 8),
          ...SupportedExercise.values.map(
            (e) => Padding(
              padding: const EdgeInsets.only(right: 8),
              child: _FilterChip(
                label: e.nameFr,
                isSelected: selected == e,
                onTap: () => onChanged(e),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14),
        decoration: BoxDecoration(
          color: isSelected
              ? colors.accent.withOpacity(0.15)
              : colors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected
                ? colors.accent
                : colors.border,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isSelected
                  ? colors.accent
                  : colors.textMuted,
              fontWeight:
                  isSelected ? FontWeight.w600 : FontWeight.w400,
              fontSize: 12,
            ),
          ),
        ),
      ),
    );
  }
}

// ── Liste des sessions ────────────────────────────────────────────────────────

class _SessionList extends StatelessWidget {
  final List<VisionSession> sessions;
  final SupportedExercise? exerciseFilter;

  const _SessionList({
    required this.sessions,
    required this.exerciseFilter,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return CustomScrollView(
      slivers: [
        // ── Graphique progression ─────────────────────────────────────
        if (sessions.length >= 3)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              child: _ProgressionChart(
                sessions: sessions,
                exerciseFilter: exerciseFilter,
              ),
            ),
          ),

        // ── En-tête liste ─────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Sessions',
                  style: TextStyle(
                    color: colors.text,
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                  ),
                ),
                Text(
                  '${sessions.length} session${sessions.length > 1 ? 's' : ''}',
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ),

        // ── Cartes sessions ───────────────────────────────────────────
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
          sliver: SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _VisionSessionCard(session: sessions[index]),
              ),
              childCount: sessions.length,
            ),
          ),
        ),
      ],
    );
  }
}

// ── Graphique progression ─────────────────────────────────────────────────────

class _ProgressionChart extends StatelessWidget {
  final List<VisionSession> sessions;
  final SupportedExercise? exerciseFilter;

  const _ProgressionChart({
    required this.sessions,
    required this.exerciseFilter,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    // Tri du plus ancien au plus récent pour le graphique
    final sorted = [...sessions]
      ..sort((a, b) => a.startedAt.compareTo(b.startedAt));

    final spots = sorted.asMap().entries.map((e) {
      return FlSpot(e.key.toDouble(), e.value.quality.overallScore);
    }).toList();

    // maxY : max des scores + marge, plafonné à 100
    final maxScore =
        spots.map((s) => s.y).reduce((a, b) => a > b ? a : b);
    final maxY = (maxScore + 10).clamp(10.0, 100.0);

    final label = exerciseFilter?.nameFr ?? 'Tous';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Progression qualité · $label',
            style: TextStyle(
              color: colors.text,
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 130,
            child: LineChart(
              LineChartData(
                minY: 0,
                maxY: maxY,
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (_) => FlLine(
                    color: colors.border,
                    strokeWidth: 1,
                  ),
                ),
                borderData: FlBorderData(show: false),
                titlesData: const FlTitlesData(
                  rightTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  topTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  leftTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                ),
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    tooltipRoundedRadius: 8,
                    getTooltipItems: (touchedSpots) =>
                        touchedSpots.map((s) {
                      return LineTooltipItem(
                        '${s.y.round()}',
                        TextStyle(
                          color: colors.accent,
                          fontWeight: FontWeight.w700,
                          fontSize: 12,
                        ),
                      );
                    }).toList(),
                  ),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    color: colors.accent,
                    barWidth: 2,
                    isStrokeCapRound: true,
                    dotData: const FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      color:
                          colors.accent.withOpacity(0.08),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Carte session ─────────────────────────────────────────────────────────────

class _VisionSessionCard extends StatelessWidget {
  final VisionSession session;

  const _VisionSessionCard({required this.session});

  static IconData _iconFor(SupportedExercise e) => switch (e) {
        SupportedExercise.squat => Icons.accessibility_new_rounded,
        SupportedExercise.pushUp => Icons.fitness_center_rounded,
        SupportedExercise.plank => Icons.horizontal_rule_rounded,
        SupportedExercise.jumpingJack => Icons.sports_gymnastics_rounded,
        SupportedExercise.lunge => Icons.directions_walk_rounded,
        SupportedExercise.sitUp => Icons.self_improvement_rounded,
      };

  static Color _scoreColor(double score) {
    if (score >= 80) return const Color(0xFF00E5A0);
    if (score >= 60) return const Color(0xFFFFB347);
    return const Color(0xFFFF6B6B);
  }

  static String _formatDate(DateTime dt) {
    final d = dt.day.toString().padLeft(2, '0');
    final m = dt.month.toString().padLeft(2, '0');
    return '$d/$m/${dt.year}';
  }

  static String _scoreLabel(double score) {
    if (score >= 80) return 'Excellent';
    if (score >= 65) return 'Bon';
    if (score >= 50) return 'Correct';
    if (score >= 35) return 'À améliorer';
    return 'Insuffisant';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final q = session.quality;
    final hasScore = q.hasEnoughData;
    final scoreColor = _scoreColor(q.overallScore);

    return GestureDetector(
      onTap: () => context.push('/vision/history/detail', extra: session),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: colors.border),
        ),
        child: Column(
          children: [
            // ── Ligne 1 : exercice | date | score ──────────────────────
            Row(
              children: [
                // Icône exercice
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: colors.accent.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    _iconFor(session.exercise),
                    color: colors.accent,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),

                // Nom exercice
                Expanded(
                  child: Text(
                    session.exercise.nameFr,
                    style: TextStyle(
                      color: colors.text,
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                    ),
                  ),
                ),

                // Date
                Text(
                  _formatDate(session.startedAt),
                  style: TextStyle(
                    color: colors.textMuted,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(width: 10),

                // Badge score global
                if (hasScore)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: scoreColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '${q.overallScore.round()}',
                      style: TextStyle(
                        color: scoreColor,
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                  )
                else
                  Text(
                    '—',
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 13),
                  ),
              ],
            ),

            const SizedBox(height: 10),
            Divider(color: colors.border, height: 1),
            const SizedBox(height: 10),

            // ── Ligne 2 : stats compactes ──────────────────────────────
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _MiniStat(
                  label: session.exercise.isTimerBased
                      ? 'Temps tenu'
                      : 'Répétitions',
                  value: session.exercise.isTimerBased
                      ? session.durationLabel
                      : '${session.repCount}',
                  icon: session.exercise.isTimerBased
                      ? Icons.timer_outlined
                      : Icons.repeat_rounded,
                ),
                const _VertDivider(),
                _MiniStat(
                  label: 'Durée totale',
                  value: session.durationLabel,
                  icon: Icons.schedule_rounded,
                ),
                if (hasScore) ...[
                  const _VertDivider(),
                  _MiniStat(
                    label: 'Qualité',
                    value: _scoreLabel(q.overallScore),
                    icon: Icons.star_rounded,
                    valueColor: scoreColor,
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color? valueColor;

  const _MiniStat({
    required this.label,
    required this.value,
    required this.icon,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Column(
      children: [
        Icon(icon, size: 14, color: colors.textMuted),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: valueColor ?? colors.text,
            fontWeight: FontWeight.w700,
            fontSize: 13,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
              color: colors.textMuted, fontSize: 10),
        ),
      ],
    );
  }
}

class _VertDivider extends StatelessWidget {
  const _VertDivider();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      width: 1,
      height: 32,
      color: colors.border,
    );
  }
}

// ── Vue vide ──────────────────────────────────────────────────────────────────

class _EmptyHistoryView extends StatelessWidget {
  const _EmptyHistoryView();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: colors.border,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.videocam_off_rounded,
                color: colors.textMuted,
                size: 32,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Aucune session',
              style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Vos sessions Computer Vision\napparaîtront ici après chaque entraînement.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: colors.textMuted,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Vue erreur ────────────────────────────────────────────────────────────────

class _ErrorHistoryView extends StatelessWidget {
  final String message;

  const _ErrorHistoryView({required this.message});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline_rounded,
              color: colors.danger,
              size: 40,
            ),
            const SizedBox(height: 16),
            Text(
              'Erreur de chargement',
              style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(
                color: colors.textMuted,
                fontSize: 12,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
