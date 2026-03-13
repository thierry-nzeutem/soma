import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/subscription/plan_models.dart';
import '../core/subscription/entitlements_notifier.dart';

/// Widget guard: shows [child] if the user has the feature,
/// otherwise shows [paywall] or a [LockedFeatureCard] by default.
class UpgradeGate extends ConsumerWidget {
  final String feature;
  final Widget child;
  final Widget? paywall;

  const UpgradeGate({
    super.key,
    required this.feature,
    required this.child,
    this.paywall,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entitlementsAsync = ref.watch(entitlementsProvider);
    return entitlementsAsync.when(
      loading: () => child, // Show content while loading (optimistic)
      error: (_, __) => child, // On error, don't block
      data: (entitlements) {
        if (entitlements.hasFeature(feature)) {
          return child;
        }
        return paywall ??
            LockedFeatureCard(
              feature: feature,
              requiredPlan: FeatureCode.requiredPlan(feature),
            );
      },
    );
  }
}

/// Card shown when a feature is locked.
class LockedFeatureCard extends StatelessWidget {
  final String feature;
  final String requiredPlan;

  const LockedFeatureCard({
    super.key,
    required this.feature,
    required this.requiredPlan,
  });

  String _planLabel() {
    if (requiredPlan == PlanCode.performance) {
      return 'SOMA Performance';
    }
    return 'SOMA AI';
  }

  String _featureLabel() {
    switch (feature) {
      case FeatureCode.aiCoach:
        return 'Coach IA personnalise';
      case FeatureCode.dailyBriefing:
        return 'Bilan matinal IA';
      case FeatureCode.pdfReports:
        return 'Rapports sante PDF';
      case FeatureCode.advancedInsights:
        return 'Insights avances';
      case FeatureCode.readinessScore:
        return 'Score Readiness';
      case FeatureCode.injuryPrediction:
        return 'Prevention blessures';
      case FeatureCode.biologicalAge:
        return 'Age biologique';
      default:
        return 'Fonctionnalite premium';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.lock_outline_rounded,
                  size: 48,
                  color: theme.colorScheme.primary,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _featureLabel(),
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                'Cette fonctionnalite est disponible avec le plan ${_planLabel()}.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              FilledButton.icon(
                onPressed: () {
                  // TODO: navigate to upgrade screen / paywall
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        'Passez au plan ${_planLabel()} pour acceder a cette fonctionnalite.',
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.rocket_launch_outlined),
                label: Text('Passer au plan ${_planLabel()}'),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Retour'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
