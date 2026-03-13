/// SOMA LOT 15 — Injury Risk Screen.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:soma_mobile/features/injury/injury_notifier.dart';
import 'package:soma_mobile/core/models/injury_risk.dart';
import 'package:soma_mobile/core/theme/theme_extensions.dart';
import 'package:soma_mobile/shared/widgets/error_state.dart';

class InjuryRiskScreen extends ConsumerWidget {
  const InjuryRiskScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(injuryRiskProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: colors.background,
        title: Text('Risque Blessure', style: TextStyle(color: colors.text)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.textSecondary),
            onPressed: () => ref.read(injuryRiskProvider.notifier).refresh(),
          ),
        ],
      ),
      body: state.when(
        data: (risk) => _InjuryRiskBody(risk: risk),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ErrorState.server(onRetry: () => ref.invalidate(injuryRiskProvider)),
      ),
    );
  }
}

class _InjuryRiskBody extends StatelessWidget {
  final InjuryRisk risk;
  const _InjuryRiskBody({required this.risk});

  Color _riskColor(BuildContext context) {
    final colors = context.somaColors;
    return switch (risk.injuryRiskCategory) {
      'critical' => colors.danger,
      'high' => colors.warning,
      'moderate' => Colors.yellow,
      'low' => Colors.lightGreen,
      _ => colors.success,
    };
  }

  @override
  Widget build(BuildContext context) {
    final riskColor = _riskColor(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Main risk score
          _RiskScoreCard(risk: risk, color: riskColor),
          const SizedBox(height: 16),

          // Immediate actions (if any)
          if (risk.immediateActions.isNotEmpty) ...[
            _ImmediateActionsCard(actions: risk.immediateActions),
            const SizedBox(height: 16),
          ],

          // Component scores
          _ComponentsCard(risk: risk),
          const SizedBox(height: 16),

          // Risk zones
          if (risk.riskZones.isNotEmpty) ...[
            const _SectionTitle('Zones a Risque'),
            ...risk.riskZones.map((zone) => _RiskZoneCard(zone: zone)),
            const SizedBox(height: 16),
          ],

          // Recommendations
          if (risk.recommendations.isNotEmpty) ...[
            const _SectionTitle('Recommandations'),
            ...risk.recommendations.map(
              (rec) => _RecommendationTile(recommendation: rec),
            ),
          ],
        ],
      ),
    );
  }
}

class _RiskScoreCard extends StatelessWidget {
  final InjuryRisk risk;
  final Color color;
  const _RiskScoreCard({required this.risk, required this.color});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.4), width: 1.5),
      ),
      child: Row(
        children: [
          _ScoreRing(score: risk.injuryRiskScore, color: color),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Risque \${risk.categoryLabel}',
                  style: TextStyle(
                    color: color,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                if (risk.trainingOverloadRisk)
                  Text('⚠ Surcharge entrainement',
                      style: TextStyle(color: colors.warning, fontSize: 12)),
                if (risk.fatigueCompensationRisk)
                  Text('⚠ Compensation par fatigue',
                      style: TextStyle(color: colors.warning, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ScoreRing extends StatelessWidget {
  final double score;
  final Color color;
  const _ScoreRing({required this.score, required this.color});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 72,
      height: 72,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: score / 100,
            backgroundColor: Colors.white12,
            valueColor: AlwaysStoppedAnimation(color),
            strokeWidth: 6,
          ),
          Text(
            '\${score.toStringAsFixed(0)}',
            style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }
}

class _ImmediateActionsCard extends StatelessWidget {
  final List<String> actions;
  const _ImmediateActionsCard({required this.actions});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.danger.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.danger.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber, color: colors.danger, size: 18),
              const SizedBox(width: 6),
              Text('Actions immediates',
                  style: TextStyle(color: colors.danger, fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 8),
          ...actions.map((a) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(a, style: TextStyle(color: colors.danger, fontSize: 13)),
              )),
        ],
      ),
    );
  }
}

class _ComponentsCard extends StatelessWidget {
  final InjuryRisk risk;
  const _ComponentsCard({required this.risk});

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Facteurs de risque',
              style: TextStyle(color: colors.textSecondary, fontSize: 13)),
          const SizedBox(height: 12),
          _ComponentBar(label: 'ACWR', value: risk.acwrRiskScore),
          _ComponentBar(label: 'Fatigue', value: risk.fatigueRiskScore),
          _ComponentBar(label: 'Asymetrie', value: risk.asymmetryRiskScore),
          _ComponentBar(label: 'Sommeil', value: risk.sleepRiskScore),
          _ComponentBar(label: 'Monotonie', value: risk.monotonyRiskScore),
        ],
      ),
    );
  }
}

class _ComponentBar extends StatelessWidget {
  final String label;
  final double value;
  const _ComponentBar({required this.label, required this.value});

  Color _color(BuildContext context) {
    final colors = context.somaColors;
    if (value > 70) return colors.danger;
    if (value > 50) return colors.warning;
    if (value > 30) return Colors.yellow;
    return colors.success;
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final barColor = _color(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label,
                style: TextStyle(color: colors.textSecondary, fontSize: 12)),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: value / 100,
                backgroundColor: Colors.white12,
                valueColor: AlwaysStoppedAnimation(barColor),
                minHeight: 8,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text('\${value.toStringAsFixed(0)}',
              style: TextStyle(color: barColor, fontSize: 12)),
        ],
      ),
    );
  }
}

class _RiskZoneCard extends StatelessWidget {
  final RiskZone zone;
  const _RiskZoneCard({required this.zone});

  Color _color(BuildContext context) {
    final colors = context.somaColors;
    return switch (zone.riskLevel) {
      'critical' => colors.danger,
      'high' => colors.warning,
      'moderate' => Colors.yellow,
      _ => colors.success,
    };
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final zoneColor = _color(context);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: zoneColor.withOpacity(0.4)),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_outlined, color: zoneColor, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(zone.bodyPartLabel,
                    style: TextStyle(color: zoneColor, fontWeight: FontWeight.w600)),
                if (zone.contributingFactors.isNotEmpty)
                  Text(
                    zone.contributingFactors.join(', '),
                    style: TextStyle(color: colors.textMuted, fontSize: 11),
                  ),
              ],
            ),
          ),
          Text(
            '\${zone.riskScore.toStringAsFixed(0)}',
            style: TextStyle(
                color: zoneColor, fontSize: 16, fontWeight: FontWeight.w700),
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
            color: colors.text, fontSize: 16, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _RecommendationTile extends StatelessWidget {
  final String recommendation;
  const _RecommendationTile({required this.recommendation});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.check_circle_outline, color: colors.info, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(recommendation,
                style: TextStyle(color: colors.textSecondary, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}
