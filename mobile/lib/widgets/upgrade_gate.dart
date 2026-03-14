/// Feature access gate -- multi-provider, platform-aware.
///
/// Platform routing:
///   iOS     -> SubscriptionScreen (StoreKit 2, native App Store)
///   Android -> StripeBillingService (opens Stripe web checkout)
///   Web     -> Stripe checkout
///
/// App Store compliance:
///   - No pricing in the card itself (prices come from App Store on iOS).
///   - No external URL text visible.
///   - No anti-steering violation.
///   - Restore Purchases button present on iOS (Apple requirement).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/billing/billing_context.dart';
import '../core/billing/purchase_manager.dart';
import '../core/billing/store_products.dart';
import '../core/subscription/entitlements_notifier.dart';
import '../core/subscription/plan_models.dart';
import '../features/subscription/subscription_screen.dart';

/// Shows [child] if user has [feature], otherwise shows the locked paywall.
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
      loading: () => child,
      error: (_, __) => child,
      data: (entitlements) {
        if (entitlements.hasFeature(feature)) return child;
        return paywall ??
            LockedFeatureCard(
              feature: feature,
              requiredPlan: FeatureCode.requiredPlan(feature),
            );
      },
    );
  }
}

/// Locked-state card. Routes to the platform-appropriate purchase flow.
///
/// iOS     -> FilledButton 'Decouvrir les plans' -> SubscriptionScreen
/// Android -> OutlinedButton 'En savoir plus' -> Stripe via PurchaseManager
class LockedFeatureCard extends ConsumerWidget {
  final String feature;
  final String requiredPlan;

  const LockedFeatureCard({
    super.key,
    required this.feature,
    required this.requiredPlan,
  });

  String _planLabel() {
    if (requiredPlan == PlanCode.performance) return 'SOMA Performance';
    return 'SOMA AI';
  }

  String _featureLabel() {
    switch (feature) {
      case FeatureCode.aiCoach: return 'Coach IA personnalise';
      case FeatureCode.dailyBriefing: return 'Bilan matinal IA';
      case FeatureCode.pdfReports: return 'Rapports sante PDF';
      case FeatureCode.advancedInsights: return 'Insights avances';
      case FeatureCode.readinessScore: return 'Score Readiness';
      case FeatureCode.injuryPrediction: return 'Prevention blessures';
      case FeatureCode.biologicalAge: return 'Age biologique';
      case FeatureCode.anomalyDetection: return 'Detection anomalies';
      case FeatureCode.advancedVo2max: return 'VO2max avance';
      case FeatureCode.trainingLoad: return 'Charge entrainement';
      case FeatureCode.biomechanicsVision: return 'Vision biomecanique';
      default: return 'Fonctionnalite premium';
    }
  }

  String _defaultProductId() {
    if (requiredPlan == PlanCode.performance) {
      return AppleProductId.performanceMonthly;
    }
    return AppleProductId.aiMonthly;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final billing = BillingContext.current();

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
                child: Icon(Icons.lock_outline_rounded, size: 48,
                    color: theme.colorScheme.primary),
              ),
              const SizedBox(height: 24),
              Text(_featureLabel(),
                style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold),
                textAlign: TextAlign.center),
              const SizedBox(height: 12),

              // iOS-safe copy: no pricing, no external link mention
              const Text(
                'Cette fonctionnalite nest pas incluse dans votre plan actuel.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Connectez-vous avec un compte ${_planLabel()} pour y acceder.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // ------------------------------------------------
              // iOS: native StoreKit 2 subscription screen
              // ------------------------------------------------
              if (billing.canShowNativePurchase) ...[
                FilledButton.icon(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => SubscriptionScreen(
                        highlightFeature: _featureLabel(),
                      ),
                      fullscreenDialog: true,
                    ),
                  ),
                  icon: const Icon(Icons.stars_rounded),
                  label: const Text('Decouvrir les plans'),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 14),
                  ),
                ),
                const SizedBox(height: 8),
                // Restore Purchases -- required by Apple for apps with IAP
                TextButton(
                  onPressed: () async {
                    final notifier = ref.read(purchaseProvider.notifier);
                    final result = await notifier.restore();
                    if (!context.mounted) return;
                    if (result.success && result.planCode != SomaPlanCode.free) {
                      ref.read(entitlementsProvider.notifier).refresh();
                      if (context.mounted) Navigator.of(context).pop();
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content: Text('Aucun abonnement actif trouve.')),
                      );
                    }
                  },
                  child: const Text('Restaurer mes achats',
                      style: TextStyle(fontSize: 13)),
                ),
              ],

              // ------------------------------------------------
              // Android / Web: Stripe checkout via PurchaseManager
              // ------------------------------------------------
              if (billing.canShowUpgradeCTA && !billing.canShowNativePurchase) ...[
                OutlinedButton.icon(
                  onPressed: () async {
                    final notifier = ref.read(purchaseProvider.notifier);
                    await notifier.purchase(_defaultProductId());
                    if (!context.mounted) return;
                    // Stripe runs in browser; webhook activates plan async.
                    // Refresh entitlements after returning to app.
                    await Future.delayed(const Duration(seconds: 2));
                    ref.read(entitlementsProvider.notifier).refresh();
                  },
                  icon: const Icon(Icons.open_in_browser_outlined),
                  label: const Text('En savoir plus'),
                ),
                const SizedBox(height: 12),
              ],

              // Back button -- always present
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
