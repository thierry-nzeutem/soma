/// Riverpod provider for billing operations.
///
/// Routes to [AppleBillingService] on iOS, [StripeBillingService] on
/// Android/Web, based on [BillingContext.current()].
library;

import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import 'apple_billing_service.dart';
import 'billing_context.dart';
import 'billing_service.dart';
import 'stripe_billing_service.dart';

// ---------------------------------------------------------------------------
// Purchase state
// ---------------------------------------------------------------------------

enum PurchaseStatus { idle, loading, success, error }

@immutable
class PurchaseState {
  const PurchaseState({
    this.status = PurchaseStatus.idle,
    this.planCode,
    this.error,
  });

  const PurchaseState.idle()
      : status = PurchaseStatus.idle,
        planCode = null,
        error = null;

  const PurchaseState.loading()
      : status = PurchaseStatus.loading,
        planCode = null,
        error = null;

  const PurchaseState.success({required String planCode})
      : status = PurchaseStatus.success,
        planCode = planCode,
        error = null;

  const PurchaseState.error(String error)
      : status = PurchaseStatus.error,
        planCode = null,
        error = error;

  final PurchaseStatus status;
  final String? planCode;
  final String? error;

  bool get isLoading => status == PurchaseStatus.loading;
  bool get isSuccess => status == PurchaseStatus.success;
  bool get isError => status == PurchaseStatus.error;

  @override
  String toString() => 'PurchaseState(${status.name}, plan=$planCode, err=$error)';
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

/// Provider for the platform-appropriate BillingService.
///
/// iOS -> AppleBillingService
/// Android/Web -> StripeBillingService
final billingServiceProvider = Provider<BillingService>((ref) {
  final apiClient = ref.read(apiClientProvider);
  final billing = BillingContext.current();

  BillingService service;
  if (billing.isIos) {
    service = AppleBillingService(apiClient: apiClient);
  } else {
    service = StripeBillingService(apiClient: apiClient);
  }

  ref.onDispose(service.dispose);
  return service;
});

/// Notifier that manages purchase and restore flows.
class PurchaseNotifier extends AsyncNotifier<PurchaseState> {
  @override
  Future<PurchaseState> build() async {
    final service = ref.read(billingServiceProvider);
    await service.initialize();
    return const PurchaseState.idle();
  }

  /// Purchase a subscription product.
  ///
  /// After success, the caller should call entitlementsProvider.refresh()
  /// to update the UI with the new plan.
  Future<BillingResult> purchase(String productId) async {
    state = const AsyncData(PurchaseState.loading());

    final service = ref.read(billingServiceProvider);
    final result = await service.purchaseSubscription(productId);

    if (result.success) {
      state = AsyncData(PurchaseState.success(planCode: result.planCode ?? 'unknown'));
    } else {
      state = AsyncData(PurchaseState.error(result.error ?? 'Unknown error'));
    }

    return result;
  }

  /// Restore purchases (iOS only — Stripe portal on Android).
  Future<BillingResult> restore() async {
    state = const AsyncData(PurchaseState.loading());

    final service = ref.read(billingServiceProvider);
    final result = await service.restorePurchases();

    if (result.success) {
      state = AsyncData(PurchaseState.success(planCode: result.planCode ?? 'unknown'));
    } else {
      state = AsyncData(PurchaseState.error(result.error ?? 'Unknown error'));
    }

    return result;
  }

  void reset() {
    state = const AsyncData(PurchaseState.idle());
  }
}

/// Main purchase provider — use this in widgets.
final purchaseProvider =
    AsyncNotifierProvider<PurchaseNotifier, PurchaseState>(PurchaseNotifier.new);
