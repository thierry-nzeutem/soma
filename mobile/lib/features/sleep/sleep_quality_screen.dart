/// SleepQualityScreen - Score de qualite du sommeil SOMA.
///
/// Affiche :
///   - Indicateur circulaire du score global
///   - Label (Good / Fair / Poor)
///   - Sous-scores avec LinearProgressIndicator
///   - Stats : duree, sommeil profond, REM
///   - Hypnogramme simplifie (blocs colores)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'sleep_quality_notifier.dart';

// -- Score color helper ----------------------------------------------------

Color _scoreColor(int score) {
  if (score >= 80) return const Color(0xFF34C759);
  if (score >= 60) return const Color(0xFFFF9500);
  return const Color(0xFFFF3B30);
}

// -- Stage colors and labels -----------------------------------------------

Color _stageColor(String stage) {
  switch (stage.toLowerCase()) {
    case 'awake':
      return const Color(0xFFFF3B30);
    case 'light':
      return const Color(0xFF00B4D8);
    case 'deep':
      return const Color(0xFF3730A3);
    case 'rem':
      return const Color(0xFF7C3AED);
    default:
      return const Color(0xFF888888);
  }
}

String _stageLabel(String stage) {
  switch (stage.toLowerCase()) {
    case 'awake':
      return 'Awake';
    case 'light':
      return 'Light';
    case 'deep':
      return 'Deep';
    case 'rem':
      return 'REM';
    default:
      return stage;
  }
}

// -- Duration format --------------------------------------------------------

String _formatMinutes(int? minutes) {
  if (minutes == null) return '--';
  final h = minutes ~/ 60;
  final m = minutes % 60;
  if (h == 0) return '${m}m';
  return '${h}h ${m}m';
}

// -- Screen -----------------------------------------------------------------

class SleepQualityScreen extends ConsumerWidget {
  const SleepQualityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(sleepQualityProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Sleep Quality',
        showBackButton: true,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.textSecondary),
            tooltip: 'Refresh',
            onPressed: () =>
                ref.read(sleepQualityProvider.notifier).refresh(),
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (e, _) => _ErrorView(
          message: 'Could not load sleep quality data',
          onRetry: () =>
              ref.read(sleepQualityProvider.notifier).refresh(),
        ),
        data: (data) {
          if (data == null) return const _EmptyView();
          return _SleepQualityBody(data: data);
        },
      ),
    );
  }
}

// -- Body -------------------------------------------------------------------

class _SleepQualityBody extends StatelessWidget {
  final SleepQualityData data;
  const _SleepQualityBody({required this.data});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final score = data.overallScore;
    final scoreCol =
        score != null ? _scoreColor(score) : colors.textMuted;

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      children: [
        // -- Circular score -------------------------------------------------
        Center(
          child: Column(
            children: [
              Container(
                width: 140,
                height: 140,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: scoreCol, width: 6),
                  color: scoreCol.withOpacity(0.07),
                ),
                child: Center(
                  child: Text(
                    score != null ? '$score' : '--',
                    style: TextStyle(
                      color: scoreCol,
                      fontSize: 48,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -1,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              if (data.overallLabel != null)
                Text(
                  data.overallLabel!,
                  style: TextStyle(
                    color: scoreCol,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              Text(
                data.date,
                style: TextStyle(color: colors.textMuted, fontSize: 13),
              ),
            ],
          ),
        ),
        const SizedBox(height: 28),

        // -- Sleep stats row ------------------------------------------------
        Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: colors.border),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _StatChip(
                icon: Icons.schedule_rounded,
                label: 'Duration',
                value: _formatMinutes(data.durationMinutes),
                color: colors.info,
              ),
              _StatChip(
                icon: Icons.waves_rounded,
                label: 'Deep',
                value: _formatMinutes(data.deepSleepMinutes),
                color: const Color(0xFF3730A3),
              ),
              _StatChip(
                icon: Icons.psychology_rounded,
                label: 'REM',
                value: _formatMinutes(data.remSleepMinutes),
                color: const Color(0xFF7C3AED),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // -- Sub-scores ------------------------------------------------------
        if (data.subScores.isNotEmpty) ...[
          const _SectionHeader(title: 'Sub-scores'),
          const SizedBox(height: 10),
          ...data.subScores.map((sub) => _SubScoreRow(sub: sub)),
          const SizedBox(height: 24),
        ],

        // -- Hypnogram -------------------------------------------------------
        if (data.hypnogram.isNotEmpty) ...[
          const _SectionHeader(title: 'Sleep stages'),
          const SizedBox(height: 10),
          _HypnogramBar(stages: data.hypnogram),
          const SizedBox(height: 8),
          const _HypnogramLegend(),
          const SizedBox(height: 24),
        ],
      ],
    );
  }
}

// -- Sub-score row ----------------------------------------------------------

class _SubScoreRow extends StatelessWidget {
  final SleepSubScore sub;
  const _SubScoreRow({required this.sub});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final col = _scoreColor(sub.score);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  sub.name,
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                '${sub.score}',
                style: TextStyle(
                  color: col,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                '/ 100',
                style: TextStyle(color: colors.textMuted, fontSize: 11),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (sub.score / 100).clamp(0.0, 1.0),
              backgroundColor: colors.border,
              valueColor: AlwaysStoppedAnimation<Color>(col),
              minHeight: 6,
            ),
          ),
          if (sub.label.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              sub.label,
              style: TextStyle(color: colors.textMuted, fontSize: 11),
            ),
          ],
        ],
      ),
    );
  }
}

// -- Hypnogram bar ----------------------------------------------------------

class _HypnogramBar extends StatelessWidget {
  final List<HypnogramStage> stages;
  const _HypnogramBar({required this.stages});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    if (stages.isEmpty) return const SizedBox.shrink();

    final totalMinutes =
        stages.fold<int>(0, (sum, s) => sum + s.durationMinutes);
    if (totalMinutes == 0) return const SizedBox.shrink();

    return Container(
      height: 36,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: Row(
        children: stages.map((s) {
          final flex = s.durationMinutes > 0 ? s.durationMinutes : 1;
          return Expanded(
            flex: flex,
            child: Tooltip(
              message:
                  '${_stageLabel(s.stage)} (${s.durationMinutes}m)',
              child: Container(color: _stageColor(s.stage)),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// -- Hypnogram legend -------------------------------------------------------

class _HypnogramLegend extends StatelessWidget {
  const _HypnogramLegend();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    const stages = [
      ('awake', 'Awake'),
      ('light', 'Light'),
      ('deep', 'Deep'),
      ('rem', 'REM'),
    ];
    return Wrap(
      spacing: 16,
      runSpacing: 4,
      children: stages.map((s) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                color: _stageColor(s.$1),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 4),
            Text(
              s.$2,
              style: TextStyle(color: colors.textMuted, fontSize: 11),
            ),
          ],
        );
      }).toList(),
    );
  }
}

// -- Stat chip --------------------------------------------------------------

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatChip({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: colors.text,
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
        Text(
          label,
          style: TextStyle(color: colors.textMuted, fontSize: 11),
        ),
      ],
    );
  }
}

// -- Section header ---------------------------------------------------------

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

// -- Utility views ----------------------------------------------------------

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
            Icon(Icons.error_outline_rounded,
                size: 56, color: colors.danger),
            const SizedBox(height: 16),
            Text(
              message,
              style:
                  TextStyle(color: colors.textSecondary, fontSize: 15),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF34C759),
                foregroundColor: Colors.black,
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
          Icon(Icons.bedtime_outlined, size: 64, color: colors.textMuted),
          const SizedBox(height: 16),
          Text(
            'No sleep quality data available',
            style: TextStyle(color: colors.textSecondary, fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            'Track your sleep to see your quality score.',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
