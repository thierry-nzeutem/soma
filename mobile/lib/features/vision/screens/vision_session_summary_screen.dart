/// Écran de résumé de la session Computer Vision (LOT 7).
///
/// Affiche les métriques de la session terminée :
///   - Exercice, répétitions, durée
///   - Scores bioméchaniques (amplitude, stabilité, régularité)
///   - Bouton de sauvegarde vers le backend
///   - Retour au journal / workout
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/api_constants.dart';
import '../../../core/theme/theme_extensions.dart';
import '../models/movement_quality.dart';
import '../providers/vision_notifier.dart';
import '../widgets/quality_score_widget.dart';

// ── Screen ────────────────────────────────────────────────────────────────────

class VisionSessionSummaryScreen extends ConsumerStatefulWidget {
  const VisionSessionSummaryScreen({super.key});

  @override
  ConsumerState<VisionSessionSummaryScreen> createState() =>
      _VisionSessionSummaryScreenState();
}

class _VisionSessionSummaryScreenState
    extends ConsumerState<VisionSessionSummaryScreen> {
  bool _isSaving = false;
  bool _isSaved = false;
  String? _saveError;

  Future<void> _save() async {
    final session =
        ref.read(visionProvider).toVisionSession();

    setState(() {
      _isSaving = true;
      _saveError = null;
    });

    try {
      final api = ref.read(apiClientProvider);
      await api.post<void>(
        ApiConstants.visionSessions,
        data: session.toJson(),
      );
      setState(() => _isSaved = true);
    } catch (e) {
      setState(() => _saveError = 'Erreur de sauvegarde. Réessayez.');
    } finally {
      setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final session = ref.watch(visionProvider);
    final q = session.quality;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        title: const Text('Résumé de session'),
        backgroundColor: colors.navBackground,
        foregroundColor: colors.text,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close_rounded),
          onPressed: () => context.go('/journal'),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Header exercice ────────────────────────────────────────
            _ExerciseHeader(session: session),
            const SizedBox(height: 24),

            // ── Stats principales ──────────────────────────────────────
            _StatsRow(
              repCount: session.repState.count,
              durationSeconds: session.durationSeconds,
              isTimerBased: session.exercise?.isTimerBased ?? false,
            ),
            const SizedBox(height: 24),

            // ── Score global ───────────────────────────────────────────
            if (q.hasEnoughData) ...[
              _GlobalScoreCard(quality: q),
              const SizedBox(height: 16),
              _DetailScoresCard(quality: q),
              const SizedBox(height: 24),
            ] else ...[
              _InsufficientDataCard(),
              const SizedBox(height: 24),
            ],

            // ── Sauvegarde ─────────────────────────────────────────────
            if (!_isSaved) ...[
              if (_saveError != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    _saveError!,
                    style: TextStyle(
                        color: colors.danger, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                ),
              ElevatedButton.icon(
                onPressed: _isSaving ? null : _save,
                icon: _isSaving
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.black,
                        ),
                      )
                    : const Icon(Icons.save_rounded),
                label: Text(
                  _isSaving ? 'Enregistrement…' : 'Enregistrer la session',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.accent,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ] else ...[
              Container(
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: colors.accent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border:
                      Border.all(color: colors.accent.withOpacity(0.3)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.check_circle_rounded,
                        color: colors.accent, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Session enregistrée',
                      style: TextStyle(
                          color: colors.accent,
                          fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // ── Recommandations ────────────────────────────────────────
            if (q.hasEnoughData) _RecommendationsCard(quality: q),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

// ── Header exercice ───────────────────────────────────────────────────────────

class _ExerciseHeader extends StatelessWidget {
  final VisionSessionState session;

  const _ExerciseHeader({required this.session});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final exercise = session.exercise;
    if (exercise == null) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border:
            Border.all(color: colors.accent.withOpacity(0.3)),
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
            child: Icon(Icons.fitness_center_rounded,
                color: colors.accent, size: 24),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                exercise.nameFr,
                style: TextStyle(
                  color: colors.text,
                  fontWeight: FontWeight.w700,
                  fontSize: 20,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Session terminée',
                style:
                    TextStyle(color: colors.accent, fontSize: 13),
              ),
            ],
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
            style: TextStyle(color: colors.textMuted, fontSize: 12),
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

// ── Détails des scores ────────────────────────────────────────────────────────

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
              desc: quality.amplitudeLabel),
          const SizedBox(height: 12),
          _ScoreBar(
              label: 'Stabilité',
              score: quality.stabilityScore,
              desc: quality.stabilityLabel),
          const SizedBox(height: 12),
          _ScoreBar(
              label: 'Régularité',
              score: quality.regularityScore,
              desc: quality.regularityLabel),
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
                style: TextStyle(color: colors.text, fontSize: 13)),
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
              'Score biomécanique indisponible. Effectuez au moins 3 répétitions pour un score fiable.',
              style: TextStyle(color: colors.textMuted, fontSize: 13),
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
