/// Stripe billing service for Android and Web.
///
/// Android/Web subscriptions go through the Stripe web checkout page.
/// This service requests a checkout URL from the backend and opens it
/// in the system browser via url_launcher.
///
/// After successful checkout, Stripe sends a webhook to the backend,
/// which updates the user's plan. The Flutter app then refreshes
/// entitlements by calling entitlementsProvider.refresh().
library;

import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/api_client.dart';
import '../api/api_constants.dart';
import 'billing_service.dart';

/// Stripe-based billing service (Android + Web).
class StripeBillingService implements BillingService {
  StripeBillingService({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  @override
  Future<void> initialize() async {
    // No initialization needed for Stripe web checkout
  }

  @override
  Future<bool> get isAvailable async => true; // Always available (opens browser)

  /// Open Stripe checkout for the given [productId].
  ///
  /// Maps the product ID to a plan_code + billing_interval and requests
  /// a checkout URL from the backend. Opens the URL in an external browser.
  ///
  /// The subscription is activated asynchronously after Stripe webhook.
  /// Call entitlementsProvider.refresh() after returning to the app.
  @override
  Future<BillingResult> purchaseSubscription(String productId) async {
    // Map product ID to plan + interval
    final (planCode, interval) = _productToCheckoutParams(productId);
    if (planCode == null) {
      return BillingResult.failure('Unknown product: $productId');
    }

    try {
      final resp = await _apiClient.post<Map<String, dynamic>>(
        ApiConstants.billingCheckout,
        data: {'plan_code': planCode, 'billing_interval': interval},
      );

      if (resp.statusCode == 200) {
        final checkoutUrl = (resp.data as Map<String, dynamic>)['checkout_url'] as String?;
        if (checkoutUrl == null || checkoutUrl.isEmpty) {
          return const BillingResult.failure('No checkout URL returned');
        }

        final uri = Uri.parse(checkoutUrl);
        final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
        if (!launched) {
          return BillingResult.failure('Could not open checkout URL: $checkoutUrl');
        }

        // Stripe checkout runs in external browser.
        // The subscription activates after Stripe webhook -> backend.
        // Return success with a pending indicator — caller must refresh entitlements.
        debugPrint('[StripeBilling] Opened Stripe checkout for $planCode/$interval');
        return BillingResult.success(planCode: planCode);
      } else {
        return BillingResult.failure(
          'Checkout request failed: ${resp.statusCode}',
        );
      }
    } catch (e) {
      debugPrint('[StripeBilling] Checkout error: $e');
      return BillingResult.failure('Stripe checkout error: $e');
    }
  }

  /// Android/Web subscriptions are managed via Stripe billing portal.
  /// Restore is not applicable for Stripe (portal handles cancellation/renewal).
  @override
  Future<BillingResult> restorePurchases() async {
    debugPrint('[StripeBilling] restorePurchases called — opening Stripe portal');
    try {
      final resp = await _apiClient.get<Map<String, dynamic>>(
        ApiConstants.billingPortal,
      );
      if (resp.statusCode == 200) {
        final portalUrl = (resp.data as Map<String, dynamic>)['portal_url'] as String?;
        if (portalUrl != null && portalUrl.isNotEmpty) {
          await launchUrl(Uri.parse(portalUrl), mode: LaunchMode.externalApplication);
        }
      }
    } catch (e) {
      debugPrint('[StripeBilling] Portal error: $e');
    }
    return BillingResult.success(planCode: 'unknown');
  }

  @override
  void dispose() {}

  /// Map product ID to (planCode, interval) tuple.
  (String?, String) _productToCheckoutParams(String productId) {
    if (productId.contains('ai') && productId.contains('monthly')) {
      return ('ai', 'monthly');
    }
    if (productId.contains('ai') && productId.contains('yearly')) {
      return ('ai', 'yearly');
    }
    if (productId.contains('performance') && productId.contains('monthly')) {
      return ('performance', 'monthly');
    }
    if (productId.contains('performance') && productId.contains('yearly')) {
      return ('performance', 'yearly');
    }
    return (null, 'monthly');
  }
}
