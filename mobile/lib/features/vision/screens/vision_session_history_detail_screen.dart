/// Écran de détail d'une session vision depuis l'historique (LOT 8).
///
/// Vue read-only : affiche les métriques d'une session déjà sauvegardée.
/// Reçoit la [VisionSession] via GoRouter extra.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/theme_extensions.dart';
import '../models/exercise_frame.dart';
import '../models/movement_quality.dart';
import '../models/vision_session.dart';
import '../widgets/quality_score_widget.dart';

// ── Screen ────────────────────────────────────────────────────────────────────

class VisionSessionHistoryDetailScreen extends StatelessWidget {
  final VisionSession session;

  const VisionSessionHistoryDetailScreen({
    super.key,
    required this.session,
  });

  static String _formatDate(DateTime dt) {
    const months = [
      'jan.', 'fév.', 'mar.', 'avr.', 'mai', 'juin',
      'jul.', 'aoû.', 'sep.', 'oct.', 'nov.', 'déc.',
    ];
    final m = months[dt.month - 1];
    return '${dt.day} $m ${dt.year}';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final q = session.quality;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        title: Text(
          '${session.exercise.nameFr} · ${_formatDate(session.startedAt)}',
          style: TextStyle(
            color: colors.text,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        backgroundColor: colors.navBackground,
        foregroundColor: colors.text,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => context.pop(),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: colors.border),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Header exercice ──────────────────────────────────────────
            _ExerciseHeader(session: session),
            const SizedBox(height: 24),

            // ── Stats principales ────────────────────────────────────────
            _StatsRow(
              repCount: session.repCount,
              durationSeconds: session.durationSeconds,
              isTimerBased: session.exercise.isTimerBased,
            ),
            const SizedBox(height: 24),

            // ── Score global ─────────────────────────────────────────────
            if (q.hasEnoughData) ...[
              _GlobalScoreCard(quality: q),
              const SizedBox(height: 16),
              _DetailScoresCard(quality: q),
              const SizedBox(height: 16),
              _RecommendationsCard(quality: q),
            ] else ...[
              _InsufficientDataCard(),
            ],

            const SizedBox(height: 16),

            // ── Métadonnées session ──────────────────────────────────────
            _MetadataCard(session: session),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

// ── Header exercice ───────────────────────────────────────────────────────────

class _ExerciseHeader extends StatelessWidget {
  final VisionSession session;

  const _ExerciseHeader({required this.session});

  static IconData _iconFor(SupportedExercise e) => switch (e) {
        SupportedExercise.squat => Icons.accessibility_new_rounded,
        SupportedExercise.pushUp => Icons.fitness_center_rounded,
        SupportedExercise.plank => Icons.horizontal_rule_rounded,
        SupportedExercise.jumpingJack => Icons.sports_gymnastics_rounded,
        SupportedExercise.lunge => Icons.directions_walk_rounded,
        SupportedExercise.sitUp => Icons.self_improvement_rounded,
      };

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: colors.accent.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: colors.accent.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(
              _iconFor(session.exercise),
              color: colors.accent,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  session.exercise.nameFr,
                  style: TextStyle(
                    color: colors.text,
                    fontWeight: FontWeight.w700,
                    fontSize: 20,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Session enregistrée',
                  style: TextStyle(
                      color: colors.accent, fontSize: 13),
                ),
              ],
            ),
          ),
          // Icône sauvegardé
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: colors.accent.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.cloud_done_rounded,
              color: colors.accent,
              size: 18,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Stats row ─────────────────────────────────────────────────────────────────

class _StatsRow extends StatelessWidget {
  final int repCount;
  final int durationSeconds;
  final bool isTimerBased;

  const _StatsRow({
    required this.repCount,
    required this.durationSeconds,
    required this.isTimerBased,
  });

  String _formatDuration(int s) {
    final m = s ~/ 60;
    final sec = s % 60;
    if (m == 0) return '${sec}s';
    return '${m}m ${sec.toString().padLeft(2, '0')}s';
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            label: isTimerBased ? 'Temps tenu' : 'Répétitions',
            value: isTimerBased
                ? _formatDuration(durationSeconds)
                : repCount.toString(),
            icon: isTimerBased
                ? Icons.timer_outlined
                : Icons.repeat_rounded,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            label: 'Durée totale',
            value: _formatDuration(durationSeconds),
            icon: Icons.schedule_rounded,
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(icon, color: colors.textMuted, size: 20),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: colors.text,
              fontWeight: FontWeight.w800,
              fontSize: 28,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
                color: colors.textMuted, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

// ── Score global ──────────────────────────────────────────────────────────────

class _GlobalScoreCard extends StatelessWidget {
  final MovementQuality quality;

  const _GlobalScoreCard({required this.quality});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Text(
            'Score biomécanique global',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
          const SizedBox(height: 16),
          QualityScoreWidget(
            score: quality.overallScore,
            label: quality.overallLabel,
            size: 100,
          ),
        ],
      ),
    );
  }
}

// ── Détail des scores ─────────────────────────────────────────────────────────

class _DetailScoresCard extends StatelessWidget {
  final MovementQuality quality;

  const _DetailScoresCard({required this.quality});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Détail des scores',
            style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w600,
                fontSize: 14),
          ),
          const SizedBox(height: 16),
          _ScoreBar(
            label: 'Amplitude',
            score: quality.amplitudeScore,
            desc: quality.amplitudeLabel,
          ),
          const SizedBox(height: 12),
          _ScoreBar(
            label: 'Stabilité',
            score: quality.stabilityScore,
            desc: quality.stabilityLabel,
          ),
          const SizedBox(height: 12),
          _ScoreBar(
            label: 'Régularité',
            score: quality.regularityScore,
            desc: quality.regularityLabel,
          ),
        ],
      ),
    );
  }
}

class _ScoreBar extends StatelessWidget {
  final String label;
  final double score;
  final String desc;

  const _ScoreBar({
    required this.label,
    required this.score,
    required this.desc,
  });

  Color get _color {
    if (score >= 80) return const Color(0xFF00E5A0);
    if (score >= 60) return const Color(0xFFFFB347);
    return const Color(0xFFFF6B6B);
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(
                    color: colors.text, fontSize: 13)),
            Text(
              '${score.round()} — $desc',
              style: TextStyle(color: _color, fontSize: 13),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: score / 100,
            backgroundColor: colors.border,
            valueColor: AlwaysStoppedAnimation(_color),
            minHeight: 6,
          ),
        ),
      ],
    );
  }
}

// ── Données insuffisantes ─────────────────────────────────────────────────────

class _InsufficientDataCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline_rounded,
              color: colors.textMuted, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Score biomécanique indisponible pour cette session.',
              style:
                  TextStyle(color: colors.textMuted, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Recommandations ───────────────────────────────────────────────────────────

class _RecommendationsCard extends StatelessWidget {
  final MovementQuality quality;

  const _RecommendationsCard({required this.quality});

  List<String> get _recommendations {
    final recs = <String>[];
    if (quality.amplitudeScore < 70) {
      recs.add(
          '📐 Travaillez l\'amplitude : descendez plus bas pour maximiser l\'activation musculaire.');
    }
    if (quality.stabilityScore < 70) {
      recs.add(
          '🏗️ Améliorez la stabilité : contractez le gainage et gardez le dos droit.');
    }
    if (quality.regularityScore < 70) {
      recs.add(
          '⏱️ Régularisez le rythme : maintenez une cadence constante entre chaque répétition.');
    }
    if (recs.isEmpty) {
      recs.add('🌟 Excellent travail ! Continuez sur cette lancée.');
    }
    return recs;
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Recommandations',
            style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w600,
                fontSize: 14),
          ),
          const SizedBox(height: 12),
          ..._recommendations.map(
            (r) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(
                r,
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 13),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Métadonnées session ───────────────────────────────────────────────────────

class _MetadataCard extends StatelessWidget {
  final VisionSession session;

  const _MetadataCard({required this.session});

  static String _formatDateTime(DateTime dt) {
    final d = dt.day.toString().padLeft(2, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final h = dt.hour.toString().padLeft(2, '0');
    final min = dt.minute.toString().padLeft(2, '0');
    return '$d/$m/${dt.year} à $h:$min';
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final meta = session.metadata;
    final algoVersion =
        meta['algorithm_version'] as String? ?? 'v1.0';
    final framesAnalyzed = session.quality.framesAnalyzed;
    final repsAnalyzed = session.quality.repsAnalyzed;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Informations session',
            style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w600,
                fontSize: 14),
          ),
          const SizedBox(height: 12),
          _MetaRow(
            icon: Icons.calendar_today_rounded,
            label: 'Date',
            value: _formatDateTime(session.startedAt),
          ),
          const SizedBox(height: 8),
          _MetaRow(
            icon: Icons.memory_rounded,
            label: 'Algorithme',
            value: algoVersion,
          ),
          const SizedBox(height: 8),
          _MetaRow(
            icon: Icons.videocam_rounded,
            label: 'Frames analysées',
            value: '$framesAnalyzed',
          ),
          const SizedBox(height: 8),
          _MetaRow(
            icon: Icons.repeat_rounded,
            label: 'Reps analysées',
            value: '$repsAnalyzed',
          ),
          if (session.workoutSessionId != null) ...[
            const SizedBox(height: 8),
            _MetaRow(
              icon: Icons.link_rounded,
              label: 'Séance workout',
              value: session.workoutSessionId!.length > 8
                  ? '…${session.workoutSessionId!.substring(session.workoutSessionId!.length - 8)}'
                  : session.workoutSessionId!,
            ),
          ],
        ],
      ),
    );
  }
}

class _MetaRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _MetaRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: [
        Icon(icon, size: 14, color: colors.textMuted),
        const SizedBox(width: 8),
        Text(
          '$label : ',
          style: TextStyle(
              color: colors.textMuted, fontSize: 13),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
                color: colors.text, fontSize: 13),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
