/// Apple App Store and Google Play product ID constants and mappings.
///
/// iOS products must be registered in App Store Connect under
/// your app → Subscriptions → Subscription Groups.
///
/// Android products (for future Google Play Billing migration) are
/// currently placeholders — SOMA Android uses Stripe web checkout.
library;

/// Billing provider enum — determines which payment infrastructure to use.
enum BillingProvider {
  apple,   // StoreKit 2 (iOS App Store)
  stripe,  // Stripe Checkout (Android / Web)
}

/// SOMA subscription plan codes — must match backend PlanCode enum.
class SomaPlanCode {
  static const String free = 'free';
  static const String ai = 'ai';
  static const String performance = 'performance';
}

/// Apple App Store product IDs.
/// Register these exact strings in App Store Connect → Subscriptions.
class AppleProductId {
  static const String aiMonthly = 'soma.ai.monthly';
  static const String aiYearly = 'soma.ai.yearly';
  static const String performanceMonthly = 'soma.performance.monthly';
  static const String performanceYearly = 'soma.performance.yearly';

  /// All Apple product IDs for initial store query.
  static const Set<String> all = {
    aiMonthly,
    aiYearly,
    performanceMonthly,
    performanceYearly,
  };

  /// AI plan product IDs.
  static const Set<String> ai = {aiMonthly, aiYearly};

  /// Performance plan product IDs.
  static const Set<String> performance = {performanceMonthly, performanceYearly};
}

/// Google Play product IDs (reserved for future Google Play Billing migration).
/// Currently NOT used — Android uses Stripe web checkout.
class PlayProductId {
  static const String aiMonthly = 'soma_ai_monthly';
  static const String aiYearly = 'soma_ai_yearly';
  static const String performanceMonthly = 'soma_performance_monthly';
  static const String performanceYearly = 'soma_performance_yearly';
}

/// Map Apple product ID → internal plan code.
const Map<String, String> kAppleProductToPlan = {
  AppleProductId.aiMonthly: SomaPlanCode.ai,
  AppleProductId.aiYearly: SomaPlanCode.ai,
  AppleProductId.performanceMonthly: SomaPlanCode.performance,
  AppleProductId.performanceYearly: SomaPlanCode.performance,
};

/// Map Apple product ID → billing interval label (for display).
const Map<String, String> kAppleProductToInterval = {
  AppleProductId.aiMonthly: 'monthly',
  AppleProductId.aiYearly: 'yearly',
  AppleProductId.performanceMonthly: 'monthly',
  AppleProductId.performanceYearly: 'yearly',
};

/// Display labels for plans.
const Map<String, String> kPlanDisplayName = {
  SomaPlanCode.free: 'SOMA Free',
  SomaPlanCode.ai: 'SOMA AI',
  SomaPlanCode.performance: 'SOMA Performance',
};
