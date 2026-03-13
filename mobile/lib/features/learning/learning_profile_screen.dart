/// SOMA LOT 13 — Learning Profile Screen.
///
/// Shows personalized physiological profile learned from user's history.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:soma_mobile/features/learning/learning_notifier.dart';
import 'package:soma_mobile/core/models/learning_profile.dart';
import 'package:soma_mobile/core/theme/theme_extensions.dart';
import 'package:soma_mobile/shared/widgets/empty_state.dart';
import 'package:soma_mobile/shared/widgets/error_state.dart';

class LearningProfileScreen extends ConsumerWidget {
  const LearningProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(learningProfileProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: colors.background,
        title: Text('Profil Appris', style: TextStyle(color: colors.text)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.textSecondary),
            onPressed: () => ref.read(learningProfileProvider.notifier).recompute(),
          ),
        ],
      ),
      body: state.when(
        data: (profile) => _LearningProfileBody(profile: profile),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ErrorState.server(onRetry: () => ref.invalidate(learningProfileProvider)),
      ),
    );
  }
}

class _LearningProfileBody extends StatelessWidget {
  final LearningProfile profile;
  const _LearningProfileBody({required this.profile});

  @override
  Widget build(BuildContext context) {
    if (!profile.dataSufficient) {
      return EmptyState.insufficientData();
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Confidence badge
          _ConfidenceBanner(confidence: profile.confidence, daysAnalyzed: profile.daysAnalyzed),
          const SizedBox(height: 20),

          // Metabolism section
          const _SectionTitle('Metabolisme'),
          _MetabolismCard(profile: profile),
          const SizedBox(height: 16),

          // Recovery section
          const _SectionTitle('Recuperation'),
          _RecoveryCard(profile: profile),
          const SizedBox(height: 16),

          // Training section
          const _SectionTitle('Entrainement'),
          _TrainingCard(profile: profile),
          const SizedBox(height: 16),

          // Nutrition response section
          const _SectionTitle('Reponse Nutritionnelle'),
          _NutritionResponseCard(profile: profile),
          const SizedBox(height: 20),

          // Insights
          if (profile.insights.isNotEmpty) ...[
            const _SectionTitle('Insights Personnalises'),
            ...profile.insights.map((insight) => _InsightCard(insight: insight)),
          ],
        ],
      ),
    );
  }
}

class _ConfidenceBanner extends StatelessWidget {
  final double confidence;
  final int daysAnalyzed;

  const _ConfidenceBanner({required this.confidence, required this.daysAnalyzed});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final pct = (confidence * 100).toInt();

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.success.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.psychology, color: colors.success, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              "Confiance \$pct% — base sur \$daysAnalyzed jours d'historique",
              style: TextStyle(color: colors.textSecondary, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: TextStyle(
          color: colors.text,
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _MetabolismCard extends StatelessWidget {
  final LearningProfile profile;
  const _MetabolismCard({required this.profile});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          _MetricRow(
            label: 'TDEE reel',
            value: profile.trueTdee != null
                ? '\${profile.trueTdee!.round()} kcal/j'
                : 'Insuffisant',
            subtitle: profile.estimatedMifflinTdee != null
                ? 'vs \${profile.estimatedMifflinTdee!.round()} kcal estime'
                : null,
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'Efficacite metabolique',
            value: '\${(profile.metabolicEfficiency * 100).toStringAsFixed(0)}%',
            subtitle: profile.metabolicEfficiencyLabel,
            valueColor: profile.isSlowMetabolizer
                ? colors.warning
                : profile.isFastMetabolizer
                    ? colors.success
                    : null,
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'Tendance metabolique',
            value: switch (profile.metabolicTrend) {
              'improving' => '^ Amelioration',
              'declining' => 'v Declin',
              _ => '-> Stable',
            },
          ),
        ],
      ),
    );
  }
}

class _RecoveryCard extends StatelessWidget {
  final LearningProfile profile;
  const _RecoveryCard({required this.profile});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          _MetricRow(
            label: 'Profil recuperation',
            value: profile.recoveryProfileLabel,
            valueColor: switch (profile.recoveryProfile) {
              'fast' => colors.success,
              'slow' => colors.warning,
              _ => null,
            },
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'Jours recup. moyens',
            value: '\${profile.avgRecoveryDays.toStringAsFixed(1)}j',
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'Facteur sommeil',
            value: '\${(profile.sleepRecoveryFactor * 100).toStringAsFixed(0)}%',
            subtitle: 'Qualite relative',
          ),
        ],
      ),
    );
  }
}

class _TrainingCard extends StatelessWidget {
  final LearningProfile profile;
  const _TrainingCard({required this.profile});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          _MetricRow(
            label: 'Tolerance charge',
            value: '\${profile.trainingLoadTolerance.round()} AU/sem',
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'ACWR optimal',
            value: profile.optimalAcwr.toStringAsFixed(2),
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'Taux adaptation',
            value: '\${(profile.adaptationRate * 100).toStringAsFixed(0)}%',
          ),
        ],
      ),
    );
  }
}

class _NutritionResponseCard extends StatelessWidget {
  final LearningProfile profile;
  const _NutritionResponseCard({required this.profile});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          _MetricRow(
            label: 'Reponse glucides',
            value: _responseLabel(profile.carbResponse),
            valueColor: profile.carbResponse > 0.2
                ? colors.success
                : profile.carbResponse < -0.2
                    ? colors.warning
                    : null,
          ),
          Divider(color: colors.border),
          _MetricRow(
            label: 'Reponse proteines',
            value: _responseLabel(profile.proteinResponse),
            valueColor: profile.proteinResponse > 0.2
                ? colors.success
                : profile.proteinResponse < -0.2
                    ? colors.warning
                    : null,
          ),
        ],
      ),
    );
  }

  String _responseLabel(double v) {
    if (v > 0.3) return 'Excellente';
    if (v > 0.1) return 'Bonne';
    if (v > -0.1) return 'Neutre';
    if (v > -0.3) return 'Moderee';
    return 'Faible';
  }
}

class _MetricRow extends StatelessWidget {
  final String label;
  final String value;
  final String? subtitle;
  final Color? valueColor;

  const _MetricRow({
    required this.label,
    required this.value,
    this.subtitle,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: colors.textSecondary, fontSize: 14)),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: TextStyle(
                  color: valueColor ?? colors.text,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (subtitle != null)
                Text(subtitle!, style: TextStyle(color: colors.textMuted, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }
}

class _InsightCard extends StatelessWidget {
  final String insight;
  const _InsightCard({required this.insight});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.info.withOpacity(0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.lightbulb_outline, color: colors.info, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              insight,
              style: TextStyle(color: colors.textSecondary, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
