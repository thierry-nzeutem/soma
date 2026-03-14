/// Abstract billing service interface.
///
/// Concrete implementations:
///   - [AppleBillingService] — StoreKit 2 (iOS)
///   - [StripeBillingService] — Stripe web checkout (Android)
library;

import 'package:flutter/foundation.dart';

/// Result of a billing operation.
@immutable
class BillingResult {
  const BillingResult({
    required this.success,
    this.error,
    this.planCode,
  });

  const BillingResult.success({required String planCode})
      : success = true,
        error = null,
        planCode = planCode;

  const BillingResult.failure(String error)
      : success = false,
        error = error,
        planCode = null;

  final bool success;
  final String? error;

  /// The activated plan code (free | ai | performance), if known.
  final String? planCode;

  @override
  String toString() =>
      'BillingResult(success=$success, plan=$planCode, error=$error)';
}

/// Abstract interface for billing operations.
///
/// Platform implementations must handle product availability, purchase flow,
/// receipt/transaction verification, and subscription restoration.
abstract class BillingService {
  /// Initialize the billing service and set up any required listeners.
  /// Must be called before any other method.
  Future<void> initialize();

  /// Whether the billing service is available on this device.
  Future<bool> get isAvailable;

  /// Purchase a subscription product by its platform-specific product ID.
  ///
  /// On iOS: initiates StoreKit 2 purchase flow.
  /// On Android: opens Stripe checkout web page.
  ///
  /// [productId] — platform-specific product ID (see [AppleProductId]).
  Future<BillingResult> purchaseSubscription(String productId);

  /// Restore previously purchased subscriptions.
  ///
  /// On iOS: calls StoreKit restorePurchases() and verifies all transactions
  ///         against the backend.
  /// On Android: not applicable (Stripe manages subscription state).
  Future<BillingResult> restorePurchases();

  /// Clean up resources (subscription streams, listeners, etc.).
  void dispose();
}
