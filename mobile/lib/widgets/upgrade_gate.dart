/// Feature access gate — Apple App Store compliant.
///
/// Architecture rule:
///   This widget NEVER shows a "buy" button, external checkout link, pricing
///   information, or any CTA that drives a user to purchase outside the app.
///
///   The locked-state UI is purely informational:
///     • What the feature is called
///     • That the user's current plan does not include it
///     • An invitation to sign in with an eligible account (if unauthenticated)
///
///   Whether to show ANY upgrade CTA at all is delegated to [BillingContext].
///   On iOS the CTA is hidden entirely, which guarantees compliance with
///   Apple Review Guideline 3.1.1 and the anti-steering provisions.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/billing/billing_context.dart';
import '../core/subscription/entitlements_notifier.dart';
import '../core/subscription/plan_models.dart';

/// Widget guard: shows [child] if the user has [feature],
/// otherwise shows [paywall] or the default [LockedFeatureCard].
class UpgradeGate extends ConsumerWidget {
  final String feature;
  final Widget child;

  /// Optional custom locked-state widget.
  /// Provide one only if you need highly contextual copy on a specific screen.
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
      // Optimistic: show content while loading (avoids flash of locked screen)
      loading: () => child,
      // On network error, don't block the user
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

/// Informational card shown when a feature is not available on the user's plan.
///
/// App Store compliance:
///   • NO pricing shown.
///   • NO external links.
///   • NO "Subscribe on the website" or similar wording.
///   • On iOS: no upgrade CTA button at all.
///   • On Android/Web: a neutral informational CTA is shown (no price, no
///     external navigation from this widget — the actual checkout lives in
///     the web app; this button is reserved for a future in-app flow).
class LockedFeatureCard extends StatelessWidget {
  final String feature;
  final String requiredPlan;

  const LockedFeatureCard({
    super.key,
    required this.feature,
    required this.requiredPlan,
  });

  // ── Copy helpers ────────────────────────────────────────────────────────

  String _planLabel() {
    if (requiredPlan == PlanCode.performance) return 'SOMA Performance';
    return 'SOMA AI';
  }

  String _featureLabel() {
    switch (feature) {
      case FeatureCode.aiCoach:
        return 'Coach IA personnalisé';
      case FeatureCode.dailyBriefing:
        return 'Bilan matinal IA';
      case FeatureCode.pdfReports:
        return 'Rapports santé PDF';
      case FeatureCode.advancedInsights:
        return 'Insights avancés';
      case FeatureCode.readinessScore:
        return 'Score Readiness';
      case FeatureCode.injuryPrediction:
        return 'Prévention blessures';
      case FeatureCode.biologicalAge:
        return 'Âge biologique';
      case FeatureCode.anomalyDetection:
        return 'Détection d\'anomalies';
      case FeatureCode.advancedVo2max:
        return 'VO₂max avancé';
      case FeatureCode.trainingLoad:
        return 'Charge d\'entraînement';
      case FeatureCode.biomechanicsVision:
        return 'Vision biomécanique';
      default:
        return 'Fonctionnalité premium';
    }
  }

  // ── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final billing = BillingContext.current();

    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Lock icon
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

              // Feature name
              Text(
                _featureLabel(),
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),

              // ── iOS-safe informational copy ──────────────────────────────
              // Apple-approved wording: describes plan requirement without
              // mentioning pricing or directing to an external purchase.
              Text(
                'Cette fonctionnalité n\'est pas incluse dans votre plan actuel.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Connectez-vous avec un compte ${_planLabel()} pour y accéder.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // ── Conditional upgrade CTA ──────────────────────────────────
              // Shown ONLY on Android / Web. Hidden on iOS.
              // This does NOT open a checkout flow from here — the actual
              // Stripe checkout lives in the Next.js web app only.
              // This button is a placeholder for a future Android native flow.
              if (billing.canShowUpgradeCTA) ...[
                OutlinedButton.icon(
                  onPressed: () {
                    // TODO(android/web): navigate to account upgrade flow
                    // when the Android native billing module is implemented.
                    // Do NOT open Stripe from here on iOS.
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(
                          'Gérez votre abonnement sur soma-app.com.',
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.open_in_browser_outlined),
                  label: const Text('En savoir plus'),
                ),
                const SizedBox(height: 12),
              ],

              // Back button — always present
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
