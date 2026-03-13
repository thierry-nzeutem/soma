/// MotionSummaryScreen — Motion Intelligence SOMA LOT 11.
///
/// Affiche le score de sante du mouvement, les sous-scores et les profils par exercice.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/motion_intelligence.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/movement_health_ring.dart';
import 'motion_notifier.dart';

class MotionSummaryScreen extends ConsumerWidget {
  const MotionSummaryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final motionAsync = ref.watch(motionProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: colors.background,
        title: Text('Sante du Mouvement', style: TextStyle(color: colors.text)),
        actions: [
          IconButton(
            icon: Icon(Icons.history, color: colors.textSecondary),
            onPressed: () => Navigator.pushNamed(context, '/motion/history'),
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: colors.textSecondary),
            onPressed: () => ref.read(motionProvider.notifier).refresh(),
          ),
        ],
      ),
      body: motionAsync.when(
        loading: () => Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 48, color: colors.danger),
              const SizedBox(height: 12),
              Text('Impossible de charger l\'analyse du mouvement',
                  style: TextStyle(color: colors.text)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.read(motionProvider.notifier).refresh(),
                child: const Text('Reessayer'),
              ),
            ],
          ),
        ),
        data: (result) {
          if (result == null) {
            return const _EmptyView();
          }
          return _MotionBody(result: result);
        },
      ),
    );
  }
}

// -- Corps principal -----------------------------------------------------------

class _MotionBody extends StatelessWidget {
  final MotionIntelligenceResult result;
  const _MotionBody({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.symmetric(vertical: 12),
        children: [
          // Ring principal + sous-scores
          _ScoreHeader(result: result),
          const SizedBox(height: 8),

          // Metadonnees
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _MetaChip(
                  label: 'Sessions',
                  value: '${result.sessionsAnalyzed}',
                  icon: Icons.sports,
                ),
                _MetaChip(
                  label: 'Periode',
                  value: '${result.daysAnalyzed} jours',
                  icon: Icons.calendar_today,
                ),
                _MetaChip(
                  label: 'Streak qualite',
                  value: '${result.consecutiveQualitySessions}',
                  icon: Icons.local_fire_department,
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Risque asymetrie
          if (result.asymmetryScore > 20) ...[
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              color: colors.warning.withOpacity(0.08),
              child: ListTile(
                leading: Icon(Icons.balance, color: colors.warning),
                title: Text(
                  'Asymetrie ${result.asymmetryRiskLevel} (${result.asymmetryScore.toStringAsFixed(0)}/100)',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: colors.warning,
                  ),
                ),
                subtitle: const Text(
                    'Travaillez la symetrie de vos mouvements'),
              ),
            ),
          ],

          // Profils par exercice
          if (result.exerciseProfiles.isNotEmpty) ...[
            _SectionHeader(title: 'Profils par exercice'),
            ...result.exerciseProfiles.entries.map(
              (e) => _ExerciseProfileTile(
                exerciseKey: e.key,
                profile: e.value,
              ),
            ),
          ],

          // Alertes risque
          if (result.riskAlerts.isNotEmpty) ...[
            _SectionHeader(title: 'Alertes'),
            ...result.riskAlerts.map(
              (a) => Card(
                margin:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
                color: colors.danger.withOpacity(0.06),
                child: ListTile(
                  leading: Icon(Icons.warning_amber_outlined,
                      color: colors.danger, size: 20),
                  title: Text(a, style: theme.textTheme.bodySmall),
                  dense: true,
                ),
              ),
            ),
          ],

          // Recommandations
          if (result.recommendations.isNotEmpty) ...[
            _SectionHeader(title: 'Recommandations'),
            ...result.recommendations.map(
              (r) => Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('•  ',
                        style: TextStyle(color: colors.info)),
                    Expanded(
                      child: Text(r,
                          style: theme.textTheme.bodySmall),
                    ),
                  ],
                ),
              ),
            ),
          ],

          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// -- En-tete scores ------------------------------------------------------------

class _ScoreHeader extends StatelessWidget {
  final MotionIntelligenceResult result;
  const _ScoreHeader({required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          // Grand anneau
          MovementHealthRing(
            score: result.movementHealthScore,
            size: 130,
          ),
          const SizedBox(width: 20),
          // Sous-scores
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SubScore(
                  label: 'Stabilite',
                  score: result.stabilityScore,
                  color: const Color(0xFF3B82F6),
                ),
                const SizedBox(height: 10),
                _SubScore(
                  label: 'Mobilite',
                  score: result.mobilityScore,
                  color: const Color(0xFF8B5CF6),
                ),
                const SizedBox(height: 10),
                _SubScore(
                  label: 'Symetrie',
                  score: 100 - result.asymmetryScore,
                  color: const Color(0xFF22C55E),
                ),
                const SizedBox(height: 10),
                // Trend badge
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.onSurface.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    result.trendLabel,
                    style: theme.textTheme.labelSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
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

class _SubScore extends StatelessWidget {
  final String label;
  final double score;
  final Color color;
  const _SubScore(
      {required this.label, required this.score, required this.color});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: theme.textTheme.labelSmall),
            Text(
              score.toStringAsFixed(0),
              style: theme.textTheme.labelSmall?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 3),
        ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: LinearProgressIndicator(
            value: (score / 100).clamp(0.0, 1.0),
            backgroundColor: theme.colorScheme.onSurface.withOpacity(0.08),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 5,
          ),
        ),
      ],
    );
  }
}

// -- Tile profil exercice ------------------------------------------------------

class _ExerciseProfileTile extends StatefulWidget {
  final String exerciseKey;
  final ExerciseMotionProfile profile;
  const _ExerciseProfileTile(
      {required this.exerciseKey, required this.profile});

  @override
  State<_ExerciseProfileTile> createState() => _ExerciseProfileTileState();
}

class _ExerciseProfileTileState extends State<_ExerciseProfileTile> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = context.somaColors;
    final p = widget.profile;

    Color qualityColor(double q) {
      if (q >= 80) return colors.success;
      if (q >= 60) return const Color(0xFF84CC16);
      if (q >= 40) return colors.warning;
      return colors.danger;
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      p.exerciseDisplayName,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  Text(
                    p.trendLabel,
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: p.qualityTrend == 'improving'
                          ? colors.success
                          : p.qualityTrend == 'declining'
                              ? colors.danger
                              : theme.colorScheme.onSurface.withOpacity(0.5),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Q: ${p.avgQuality.toStringAsFixed(0)}',
                    style: theme.textTheme.labelMedium?.copyWith(
                      color: qualityColor(p.avgQuality),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    size: 20,
                  ),
                ],
              ),
              if (_expanded) ...[
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _ScorePill('Stabilite', p.avgStability,
                        const Color(0xFF3B82F6)),
                    _ScorePill('Amplitude', p.avgAmplitude,
                        const Color(0xFF8B5CF6)),
                    _ScorePill('Qualite', p.avgQuality,
                        qualityColor(p.avgQuality)),
                  ],
                ),
                if (p.alerts.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  ...p.alerts.map(
                    (a) => Text(
                      'Warning: $a',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: colors.warning,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 4),
                Text(
                  '${p.sessionsAnalyzed} sessions analysees',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.4),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ScorePill extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  const _ScorePill(this.label, this.value, this.color);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Text(
          value.toStringAsFixed(0),
          style: theme.textTheme.titleSmall?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.5),
          ),
        ),
      ],
    );
  }
}

// -- Helpers -------------------------------------------------------------------

class _MetaChip extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _MetaChip(
      {required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final theme = Theme.of(context);

    return Column(
      children: [
        Icon(icon, size: 20, color: colors.accent),
        const SizedBox(height: 2),
        Text(value,
            style: theme.textTheme.titleSmall
                ?.copyWith(fontWeight: FontWeight.bold)),
        Text(label,
            style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.5))),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      child: Text(
        title,
        style: TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 14,
          color: colors.textSecondary,
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
          Icon(Icons.directions_run, size: 64, color: colors.textMuted),
          const SizedBox(height: 16),
          Text('Aucune session CV analysee',
              style: TextStyle(color: colors.text)),
          const SizedBox(height: 8),
          Text(
            'Enregistrez des seances avec la camera pour activer l\'analyse.',
            style: TextStyle(color: colors.textMuted),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
