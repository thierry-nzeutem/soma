/// Apple StoreKit 2 billing service implementation.
///
/// Uses the official `in_app_purchase` Flutter package which wraps
/// StoreKit on iOS. On purchase completion, the JWS-signed transaction
/// is sent to the backend for server-side verification.
///
/// iOS only — must not be instantiated on Android or Web.
library;

import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../api/api_client.dart';
import '../api/api_constants.dart';
import 'billing_service.dart';
import 'store_products.dart';

/// Apple StoreKit billing service.
///
/// Lifecycle:
///   1. [initialize] — queries available products, starts purchase stream.
///   2. [purchaseSubscription] — initiates StoreKit 2 purchase.
///   3. [restorePurchases] — restores past purchases.
///   4. [dispose] — cancels stream subscription.
class AppleBillingService implements BillingService {
  AppleBillingService({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;
  final InAppPurchase _iap = InAppPurchase.instance;

  StreamSubscription<List<PurchaseDetails>>? _purchaseSubscription;
  final Map<String, ProductDetails> _products = {};
  bool _initialized = false;

  // Completers for async purchase/restore flows
  Completer<BillingResult>? _purchaseCompleter;
  Completer<BillingResult>? _restoreCompleter;
  final List<PurchaseDetails> _restoredTransactions = [];

  @override
  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;

    // Listen to purchase updates from StoreKit
    _purchaseSubscription = _iap.purchaseStream.listen(
      _handlePurchaseUpdates,
      onError: (Object error) {
        debugPrint('[AppleBilling] Purchase stream error: $error');
        _purchaseCompleter?.completeError(error);
        _purchaseCompleter = null;
      },
    );

    // Pre-fetch product details from App Store
    await _loadProducts();
  }

  Future<void> _loadProducts() async {
    try {
      final response = await _iap.queryProductDetails(AppleProductId.all);
      if (response.error != null) {
        debugPrint('[AppleBilling] Product query error: ${response.error}');
        return;
      }
      for (final product in response.productDetails) {
        _products[product.id] = product;
      }
      debugPrint('[AppleBilling] Loaded ${_products.length} products from App Store');
    } catch (e) {
      debugPrint('[AppleBilling] Failed to load products: $e');
    }
  }

  @override
  Future<bool> get isAvailable => _iap.isAvailable();

  @override
  Future<BillingResult> purchaseSubscription(String productId) async {
    if (!await isAvailable) {
      return const BillingResult.failure('App Store is not available');
    }

    final product = _products[productId];
    if (product == null) {
      // Try to load the product on-demand
      await _loadProducts();
      final retried = _products[productId];
      if (retried == null) {
        return BillingResult.failure(
          'Product $productId not found in App Store. '
          'Ensure it is configured in App Store Connect.',
        );
      }
    }

    final purchaseParam = PurchaseParam(
      productDetails: _products[productId]!,
    );

    _purchaseCompleter = Completer<BillingResult>();

    try {
      // buyNonConsumable for subscriptions (StoreKit handles renewals)
      await _iap.buyNonConsumable(purchaseParam: purchaseParam);
    } catch (e) {
      _purchaseCompleter = null;
      return BillingResult.failure('Failed to initiate purchase: $e');
    }

    // Wait for StoreKit to call back via purchaseStream
    return _purchaseCompleter!.future.timeout(
      const Duration(minutes: 5),
      onTimeout: () {
        _purchaseCompleter = null;
        return const BillingResult.failure('Purchase timed out');
      },
    );
  }

  @override
  Future<BillingResult> restorePurchases() async {
    if (!await isAvailable) {
      return const BillingResult.failure('App Store is not available');
    }

    _restoreCompleter = Completer<BillingResult>();
    _restoredTransactions.clear();

    try {
      await _iap.restorePurchases();
    } catch (e) {
      _restoreCompleter = null;
      return BillingResult.failure('Failed to initiate restore: $e');
    }

    // Wait for StoreKit to deliver all restored transactions
    // StoreKit calls purchaseStream for each restored purchase, then
    // sends a PurchaseStatus.restored batch completion signal.
    return _restoreCompleter!.future.timeout(
      const Duration(minutes: 2),
      onTimeout: () {
        _restoreCompleter = null;
        return const BillingResult.failure('Restore timed out');
      },
    );
  }

  void _handlePurchaseUpdates(List<PurchaseDetails> purchases) {
    for (final purchase in purchases) {
      _processPurchase(purchase);
    }
  }

  Future<void> _processPurchase(PurchaseDetails purchase) async {
    switch (purchase.status) {
      case PurchaseStatus.purchased:
        await _verifyAndComplete(purchase);

      case PurchaseStatus.restored:
        _restoredTransactions.add(purchase);
        // Check if this is the end of the restore batch
        // StoreKit sends purchases one by one; we complete after a short delay
        _scheduleRestoreCompletion();

      case PurchaseStatus.error:
        final error = purchase.error?.message ?? 'Unknown error';
        debugPrint('[AppleBilling] Purchase error: $error');
        _purchaseCompleter?.complete(BillingResult.failure(error));
        _purchaseCompleter = null;
        if (purchase.pendingCompletePurchase) {
          await _iap.completePurchase(purchase);
        }

      case PurchaseStatus.canceled:
        debugPrint('[AppleBilling] Purchase cancelled by user');
        _purchaseCompleter?.complete(
          const BillingResult.failure('Purchase cancelled'),
        );
        _purchaseCompleter = null;

      case PurchaseStatus.pending:
        // StoreKit 2 — purchase is pending (e.g., Ask to Buy)
        debugPrint('[AppleBilling] Purchase pending (Ask to Buy or delayed)');
    }
  }

  Future<void> _verifyAndComplete(PurchaseDetails purchase) async {
    try {
      final jws = purchase.verificationData.serverVerificationData;
      final planCode = kAppleProductToPlan[purchase.productID] ?? SomaPlanCode.free;

      final resp = await _apiClient.post<Map<String, dynamic>>(
        ApiConstants.appleVerify,
        data: {
          'transaction_jws': jws,
          'product_id': purchase.productID,
        },
      );

      if (resp.statusCode == 200) {
        final data = resp.data as Map<String, dynamic>;
        final activatedPlan = data['plan_code'] as String? ?? planCode;
        debugPrint('[AppleBilling] Verified purchase: plan=$activatedPlan');

        if (purchase.pendingCompletePurchase) {
          await _iap.completePurchase(purchase);
        }

        _purchaseCompleter?.complete(
          BillingResult.success(planCode: activatedPlan),
        );
        _purchaseCompleter = null;
      } else {
        throw Exception('Backend verification returned ${resp.statusCode}');
      }
    } catch (e) {
      debugPrint('[AppleBilling] Verification error: $e');
      if (purchase.pendingCompletePurchase) {
        await _iap.completePurchase(purchase);
      }
      _purchaseCompleter?.complete(
        BillingResult.failure('Verification failed: $e'),
      );
      _purchaseCompleter = null;
    }
  }

  Timer? _restoreTimer;

  void _scheduleRestoreCompletion() {
    // Cancel any previous timer
    _restoreTimer?.cancel();
    // Wait 1 second after last restored transaction to consider batch complete
    _restoreTimer = Timer(const Duration(seconds: 1), () => _completeRestore());
  }

  Future<void> _completeRestore() async {
    if (_restoredTransactions.isEmpty) {
      _restoreCompleter?.complete(
        const BillingResult.failure('No purchases to restore'),
      );
      _restoreCompleter = null;
      return;
    }

    // Collect all JWS strings from restored transactions
    final jwsList = <String>[];
    for (final purchase in _restoredTransactions) {
      final jws = purchase.verificationData.serverVerificationData;
      if (jws.isNotEmpty) jwsList.add(jws);
      if (purchase.pendingCompletePurchase) {
        await _iap.completePurchase(purchase);
      }
    }

    if (jwsList.isEmpty) {
      _restoreCompleter?.complete(
        const BillingResult.failure('No valid transactions to restore'),
      );
      _restoreCompleter = null;
      return;
    }

    try {
      final resp = await _apiClient.post<Map<String, dynamic>>(
        ApiConstants.appleRestore,
        data: {'transaction_jws_list': jwsList},
      );

      if (resp.statusCode == 200) {
        final data = resp.data as Map<String, dynamic>;
        final planCode = data['plan_code'] as String? ?? SomaPlanCode.free;
        debugPrint('[AppleBilling] Restore complete: plan=$planCode');
        _restoreCompleter?.complete(BillingResult.success(planCode: planCode));
      } else {
        throw Exception('Backend restore returned ${resp.statusCode}');
      }
    } catch (e) {
      debugPrint('[AppleBilling] Restore error: $e');
      _restoreCompleter?.complete(BillingResult.failure('Restore failed: $e'));
    } finally {
      _restoreCompleter = null;
      _restoredTransactions.clear();
    }
  }

  /// Returns available products loaded from the App Store.
  Map<String, ProductDetails> get availableProducts => Map.unmodifiable(_products);

  @override
  void dispose() {
    _purchaseSubscription?.cancel();
    _restoreTimer?.cancel();
    _purchaseCompleter?.complete(const BillingResult.failure('Service disposed'));
    _restoreCompleter?.complete(const BillingResult.failure('Service disposed'));
    _purchaseCompleter = null;
    _restoreCompleter = null;
  }
}
