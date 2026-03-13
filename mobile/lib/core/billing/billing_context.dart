/// Billing orchestration — platform-aware billing context.
///
/// Strategic rule (App Store compliance):
///   iOS   → NO external checkout, NO portal, NO upgrade CTA, NO pricing links.
///   Web   → Stripe fully enabled (Next.js).
///   Android → Stripe enabled (same as Web for current business decision).
///
/// All billing UI decisions in Flutter MUST go through this class.
/// Never use `Platform.isIOS` scattered in widgets — use BillingContext.
library;

import 'package:flutter/foundation.dart';

/// The platform that is currently running the billing flow.
enum BillingPlatform {
  /// iOS App Store — external checkout strictly forbidden.
  ios,

  /// Android — Stripe checkout allowed per current business decision.
  android,

  /// Web (flutter web or webview launched from web) — Stripe fully enabled.
  web,
}

/// Central billing capability resolver.
///
/// Usage:
/// ```dart
/// final ctx = BillingContext.current();
/// if (ctx.canShowCheckout) { ... }
/// ```
class BillingContext {
  const BillingContext._(this.platform);

  final BillingPlatform platform;

  // ── Factory ───────────────────────────────────────────────────────────────

  /// Resolves the billing platform from the current Flutter runtime.
  ///
  /// Override [forcePlatform] in tests or special scenarios.
  factory BillingContext.current({BillingPlatform? forcePlatform}) {
    if (forcePlatform != null) return BillingContext._(forcePlatform);
    if (kIsWeb) return const BillingContext._(BillingPlatform.web);
    if (defaultTargetPlatform == TargetPlatform.iOS) {
      return const BillingContext._(BillingPlatform.ios);
    }
    // Android + other Flutter desktop targets
    return const BillingContext._(BillingPlatform.android);
  }

  // ── Capability gates ──────────────────────────────────────────────────────

  /// Whether this platform may show a Stripe/external checkout button.
  /// iOS → false. Android/Web → true.
  bool get canShowCheckout => platform != BillingPlatform.ios;

  /// Whether this platform may show a billing portal / subscription management link.
  /// iOS → false. Android/Web → true.
  bool get canShowManageBilling => platform != BillingPlatform.ios;

  /// Whether this platform may show an "Upgrade" CTA that leads to external payment.
  /// iOS → false. Android/Web → true.
  bool get canShowUpgradeCTA => platform != BillingPlatform.ios;

  /// Whether this platform may open an external pricing page or website link.
  /// iOS → false. Android/Web → true.
  bool get canOpenExternalPricing => platform != BillingPlatform.ios;

  /// Whether this platform sends `X-Client-Platform: ios` to the backend,
  /// which triggers server-side protection on checkout/portal endpoints.
  bool get isIos => platform == BillingPlatform.ios;

  /// Convenience: platform name for the `X-Client-Platform` HTTP header.
  String get headerValue => platform.name; // "ios" | "android" | "web"

  @override
  String toString() => 'BillingContext(platform: ${platform.name}, '
      'canShowCheckout: $canShowCheckout, '
      'canShowUpgradeCTA: $canShowUpgradeCTA)';
}
