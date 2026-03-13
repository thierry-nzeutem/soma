/// Écran Insights Sommeil — BATCH 6.
///
/// Affiche l'analyse complète du sommeil :
/// - Architecture (répartition phases deep/REM/light/awake)
/// - Consistance (variance horaires coucher/réveil)
/// - Problèmes détectés avec recommandations
library;

import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/sleep_analysis.dart';
import '../../core/theme/theme_extensions.dart';
import '../../core/theme/soma_colors.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'sleep_analysis_notifier.dart';

class SleepInsightsScreen extends ConsumerWidget {
  const SleepInsightsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analysisAsync = ref.watch(sleepAnalysisProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Insights Sommeil'),
      body: analysisAsync.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.error_outline, color: colors.danger, size: 40),
                const SizedBox(height: 12),
                Text('Impossible de charger l\'analyse',
                    style: TextStyle(color: colors.text, fontSize: 16)),
                const SizedBox(height: 8),
                Text(err.toString(),
                    style: TextStyle(color: colors.textMuted, fontSize: 12),
                    textAlign: TextAlign.center),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () =>
                      ref.read(sleepAnalysisProvider.notifier).refresh(),
                  style: ElevatedButton.styleFrom(
                      backgroundColor: colors.accent,
                      foregroundColor: Colors.white),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          ),
        ),
        data: (analysis) {
          if (!analysis.hasData) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.bedtime_outlined,
                        color: colors.textMuted, size: 48),
                    const SizedBox(height: 16),
                    Text('Pas encore de données',
                        style: TextStyle(
                            color: colors.text,
                            fontSize: 16,
                            fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Text(
                        'Enregistrez quelques nuits de sommeil pour voir votre analyse.',
                        style:
                            TextStyle(color: colors.textMuted, fontSize: 13),
                        textAlign: TextAlign.center),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            color: colors.accent,
            onRefresh: () =>
                ref.read(sleepAnalysisProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                if (analysis.architecture != null) ...[
                  _ArchitectureCard(architecture: analysis.architecture!),
                  const SizedBox(height: 16),
                ],
                if (analysis.consistency != null) ...[
                  _ConsistencyCard(consistency: analysis.consistency!),
                  const SizedBox(height: 16),
                ],
                if (analysis.problems.isNotEmpty) ...[
                  _ProblemsSection(problems: analysis.problems),
                ],
                const SizedBox(height: 40),
              ],
            ),
          );
        },
      ),
    );
  }
}

// ── Architecture Card ─────────────────────────────────────────────────────────

class _ArchitectureCard extends StatelessWidget {
  final SleepArchitecture architecture;
  const _ArchitectureCard({required this.architecture});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Icon(Icons.pie_chart_rounded, color: colors.accent, size: 20),
              const SizedBox(width: 10),
              Text('Architecture',
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 16,
                      fontWeight: FontWeight.w600)),
              const Spacer(),
              _ScoreBadge(
                  score: architecture.architectureScore,
                  label: architecture.qualityLabel),
            ],
          ),
          const SizedBox(height: 20),

          // Mini pie chart + breakdown
          Row(
            children: [
              // Pie chart
              SizedBox(
                width: 100,
                height: 100,
                child: CustomPaint(
                  painter: _SleepPiePainter(
                    deep: architecture.deepPct,
                    rem: architecture.remPct,
                    light: architecture.lightPct,
                    awake: architecture.awakePct,
                    colors: colors,
                  ),
                ),
              ),
              const SizedBox(width: 20),
              // Legend
              Expanded(
                child: Column(
                  children: [
                    _PhaseRow(
                        label: 'Profond',
                        pct: architecture.deepPct,
                        color: const Color(0xFF6366F1)),
                    _PhaseRow(
                        label: 'Paradoxal (REM)',
                        pct: architecture.remPct,
                        color: const Color(0xFF8B5CF6)),
                    _PhaseRow(
                        label: 'Léger',
                        pct: architecture.lightPct,
                        color: colors.accent),
                    _PhaseRow(
                        label: 'Éveillé',
                        pct: architecture.awakePct,
                        color: colors.warning),
                  ],
                ),
              ),
            ],
          ),

          // Areas to improve
          if (architecture.areasToImprove.isNotEmpty) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: architecture.areasToImprove
                  .map((area) => Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: colors.warning.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                              color: colors.warning.withOpacity(0.3)),
                        ),
                        child: Text(_areaLabel(area),
                            style: TextStyle(
                                color: colors.warning, fontSize: 11)),
                      ))
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  String _areaLabel(String key) {
    switch (key) {
      case 'insufficient_deep_sleep':
        return 'Profond insuffisant';
      case 'insufficient_rem_sleep':
        return 'REM insuffisant';
      case 'excessive_wake_time':
        return 'Trop d\'éveil';
      case 'insufficient_duration':
        return 'Durée insuffisante';
      case 'sleep_stages_unknown':
        return 'Phases non disponibles';
      default:
        return key;
    }
  }
}

class _PhaseRow extends StatelessWidget {
  final String label;
  final double pct;
  final Color color;
  const _PhaseRow(
      {required this.label, required this.pct, required this.color});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration:
                BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(label,
                style: TextStyle(color: colors.textSecondary, fontSize: 12)),
          ),
          Text('${pct.toStringAsFixed(0)}%',
              style: TextStyle(
                  color: colors.text,
                  fontSize: 12,
                  fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

// ── Consistency Card ──────────────────────────────────────────────────────────

class _ConsistencyCard extends StatelessWidget {
  final SleepConsistency consistency;
  const _ConsistencyCard({required this.consistency});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Icon(Icons.schedule_rounded, color: colors.info, size: 20),
              const SizedBox(width: 10),
              Text('Régularité',
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 16,
                      fontWeight: FontWeight.w600)),
              const Spacer(),
              _ScoreBadge(
                  score: consistency.consistencyScore,
                  label: consistency.label),
            ],
          ),
          const SizedBox(height: 20),

          // Stats grid
          Row(
            children: [
              Expanded(
                child: _StatTile(
                  icon: Icons.bedtime_outlined,
                  label: 'Coucher moyen',
                  value: consistency.formatHour(consistency.avgBedtimeHour),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _StatTile(
                  icon: Icons.wb_sunny_outlined,
                  label: 'Réveil moyen',
                  value: consistency.formatHour(consistency.avgWakeHour),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _StatTile(
                  icon: Icons.swap_vert_rounded,
                  label: 'Variance coucher',
                  value: '±${consistency.bedtimeVarianceMin.toStringAsFixed(0)} min',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _StatTile(
                  icon: Icons.swap_vert_rounded,
                  label: 'Variance réveil',
                  value: '±${consistency.wakeVarianceMin.toStringAsFixed(0)} min',
                ),
              ),
            ],
          ),

          // Sessions analyzed
          const SizedBox(height: 12),
          Text('Basé sur ${consistency.sessionsAnalyzed} nuits',
              style: TextStyle(color: colors.textMuted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _StatTile(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: colors.textMuted, size: 14),
              const SizedBox(width: 6),
              Text(label,
                  style: TextStyle(color: colors.textMuted, fontSize: 10)),
            ],
          ),
          const SizedBox(height: 6),
          Text(value,
              style: TextStyle(
                  color: colors.text,
                  fontSize: 16,
                  fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

// ── Problems Section ──────────────────────────────────────────────────────────

class _ProblemsSection extends StatelessWidget {
  final List<SleepProblem> problems;
  const _ProblemsSection({required this.problems});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: colors.warning, size: 20),
            const SizedBox(width: 8),
            Text('Problèmes détectés',
                style: TextStyle(
                    color: colors.text,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 12),
        ...problems.map((p) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _ProblemCard(problem: p),
            )),
      ],
    );
  }
}

class _ProblemCard extends StatelessWidget {
  final SleepProblem problem;
  const _ProblemCard({required this.problem});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final severityColor = problem.severity == 'high'
        ? colors.danger
        : problem.severity == 'moderate'
            ? colors.warning
            : colors.info;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: severityColor.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: severityColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(problem.severityLabel,
                    style: TextStyle(
                        color: severityColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(problem.typeLabel,
                    style: TextStyle(
                        color: colors.text,
                        fontSize: 14,
                        fontWeight: FontWeight.w600)),
              ),
              Text('${problem.evidenceDays}j',
                  style: TextStyle(color: colors.textMuted, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 8),
          Text(problem.description,
              style: TextStyle(color: colors.textSecondary, fontSize: 13)),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: colors.accent.withOpacity(0.06),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.lightbulb_outline_rounded,
                    color: colors.accent, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(problem.recommendation,
                      style: TextStyle(
                          color: colors.text, fontSize: 12, height: 1.4)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Score Badge ──────────────────────────────────────────────────────────────

class _ScoreBadge extends StatelessWidget {
  final int score;
  final String label;
  const _ScoreBadge({required this.score, required this.label});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final badgeColor = score >= 80
        ? colors.success
        : score >= 60
            ? colors.warning
            : colors.danger;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: badgeColor.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('$score',
              style: TextStyle(
                  color: badgeColor,
                  fontSize: 14,
                  fontWeight: FontWeight.w700)),
          const SizedBox(width: 4),
          Text(label,
              style: TextStyle(color: badgeColor, fontSize: 10)),
        ],
      ),
    );
  }
}

// ── Pie Painter ─────────────────────────────────────────────────────────────

class _SleepPiePainter extends CustomPainter {
  final double deep;
  final double rem;
  final double light;
  final double awake;
  final SomaColors colors;

  _SleepPiePainter({
    required this.deep,
    required this.rem,
    required this.light,
    required this.awake,
    required this.colors,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 2;
    final total = deep + rem + light + awake;
    if (total <= 0) return;

    final segments = <MapEntry<double, Color>>[
      MapEntry(deep, const Color(0xFF6366F1)),
      MapEntry(rem, const Color(0xFF8B5CF6)),
      MapEntry(light, colors.accent),
      MapEntry(awake, colors.warning),
    ];

    double startAngle = -math.pi / 2;
    for (final entry in segments) {
      if (entry.key <= 0) continue;
      final sweep = (entry.key / total) * 2 * math.pi;
      final paint = Paint()
        ..color = entry.value
        ..style = PaintingStyle.fill;
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweep,
        true,
        paint,
      );
      startAngle += sweep;
    }

    // Inner circle for donut effect
    final innerPaint = Paint()..color = colors.surface;
    canvas.drawCircle(center, radius * 0.55, innerPaint);
  }

  @override
  bool shouldRepaint(covariant _SleepPiePainter old) =>
      deep != old.deep ||
      rem != old.rem ||
      light != old.light ||
      awake != old.awake;
}
