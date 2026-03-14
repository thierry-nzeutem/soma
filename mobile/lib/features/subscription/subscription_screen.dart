/// iOS subscription paywall screen — App Store compliant.
///
/// Shows available plans with pricing fetched from the App Store,
/// handles purchase flow, and provides a "Restore Purchases" button.
///
/// App Store compliance:
/// - No mention of Stripe, external payment, or web checkout.
/// - "Restore Purchases" button is required by Apple for apps with IAP.
/// - No cross-platform pricing comparison.
/// - Wording is informational and benefit-focused.
library;

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../../core/billing/apple_billing_service.dart';
import '../../core/billing/billing_context.dart';
import '../../core/billing/purchase_manager.dart';
import '../../core/billing/store_products.dart';
import '../../core/subscription/entitlements_notifier.dart';

/// iOS App Store subscription paywall screen.
class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key, this.highlightFeature});

  /// If provided, shown as the reason why the user is seeing this screen.
  final String? highlightFeature;

  @override
  ConsumerState<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  String? _selectedProductId;
  bool _isLoadingProducts = true;
  Map<String, ProductDetails> _products = {};

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    final service = ref.read(billingServiceProvider);
    if (service is AppleBillingService) {
      // Trigger product load if not already done
      await service.initialize();
      if (mounted) {
        setState(() {
          _products = service.availableProducts;
          // Default selection: AI monthly
          _selectedProductId ??=
              _products.containsKey(AppleProductId.aiMonthly)
                  ? AppleProductId.aiMonthly
                  : null;
          _isLoadingProducts = false;
        });
      }
    } else {
      if (mounted) setState(() => _isLoadingProducts = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final purchaseAsync = ref.watch(purchaseProvider);
    final isLoading = purchaseAsync.when(
      data: (s) => s.isLoading,
      loading: () => true,
      error: (_, __) => false,
    );

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          // "Restore Purchases" — required by Apple App Store guidelines
          TextButton(
            onPressed: isLoading ? null : _handleRestore,
            child: const Text(
              'Restaurer',
              style: TextStyle(color: Color(0xFF00E5A0), fontSize: 14),
            ),
          ),
        ],
      ),
      body: _isLoadingProducts
          ? const Center(child: CupertinoActivityIndicator())
          : _buildContent(context, isLoading),
    );
  }

  Widget _buildContent(BuildContext context, bool isLoading) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          const Icon(Icons.auto_awesome, color: Color(0xFF00E5A0), size: 48),
          const SizedBox(height: 16),
          Text(
            widget.highlightFeature != null
                ? 'Débloquez ${widget.highlightFeature}'
                : 'Passez à la vitesse supérieure',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          const Text(
            'Choisissez le plan qui correspond à vos objectifs.',
            style: TextStyle(color: Color(0xFFAAAAAA), fontSize: 15),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),

          // Plan selector tabs (AI / Performance)
          _buildPlanTabs(),
          const SizedBox(height: 16),

          // Product cards (monthly / yearly)
          _buildProductCards(),
          const SizedBox(height: 32),

          // Feature highlights
          _buildFeatureList(),
          const SizedBox(height: 32),

          // Purchase CTA
          _buildPurchaseButton(isLoading),
          const SizedBox(height: 16),

          // Legal disclaimer
          const Text(
            'L\'abonnement sera débité sur votre compte Apple ID. '
            'L\'abonnement se renouvelle automatiquement sauf annulation '
            '24 heures avant la fin de la période en cours. '
            'Vous pouvez gérer vos abonnements dans les Réglages.',
            style: TextStyle(color: Color(0xFF666666), fontSize: 11),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildPlanTabs() {
    final isAi = _selectedProductId == null ||
        _selectedProductId!.contains('ai');

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: _PlanTab(
              label: 'SOMA AI',
              subtitle: 'Coach & Insights',
              selected: isAi,
              onTap: () => setState(() {
                _selectedProductId = AppleProductId.aiMonthly;
              }),
            ),
          ),
          Expanded(
            child: _PlanTab(
              label: 'SOMA Performance',
              subtitle: 'Athlète & Elite',
              selected: !isAi,
              onTap: () => setState(() {
                _selectedProductId = AppleProductId.performanceMonthly;
              }),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProductCards() {
    final isAi = _selectedProductId?.contains('ai') ?? true;
    final monthlyId = isAi ? AppleProductId.aiMonthly : AppleProductId.performanceMonthly;
    final yearlyId = isAi ? AppleProductId.aiYearly : AppleProductId.performanceYearly;

    return Column(
      children: [
        _ProductCard(
          productId: monthlyId,
          label: 'Mensuel',
          product: _products[monthlyId],
          selected: _selectedProductId == monthlyId,
          onTap: () => setState(() => _selectedProductId = monthlyId),
        ),
        const SizedBox(height: 8),
        _ProductCard(
          productId: yearlyId,
          label: 'Annuel',
          savingsBadge: '2 mois offerts',
          product: _products[yearlyId],
          selected: _selectedProductId == yearlyId,
          onTap: () => setState(() => _selectedProductId = yearlyId),
        ),
      ],
    );
  }

  Widget _buildFeatureList() {
    final isAi = _selectedProductId?.contains('ai') ?? true;
    final features = isAi
        ? const [
            ('Coach IA personnalisé', Icons.psychology_outlined),
            ('Briefing quotidien', Icons.wb_sunny_outlined),
            ('Insights avancés', Icons.insights),
            ('Rapports PDF', Icons.picture_as_pdf_outlined),
            ('Âge biologique', Icons.favorite_outline),
          ]
        : const [
            ('Tout le plan SOMA AI', Icons.check_circle_outline),
            ('Score de forme du jour', Icons.speed),
            ('Prédiction blessures', Icons.health_and_safety_outlined),
            ('Analyse biomécanique vidéo', Icons.videocam_outlined),
            ('VO₂max avancé', Icons.air),
            ('Charge d\'entraînement', Icons.fitness_center),
          ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: features
          .map(
            (f) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Icon(f.$2, color: const Color(0xFF00E5A0), size: 18),
                  const SizedBox(width: 10),
                  Text(
                    f.$1,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _buildPurchaseButton(bool isLoading) {
    return FilledButton(
      onPressed: isLoading || _selectedProductId == null
          ? null
          : _handlePurchase,
      style: FilledButton.styleFrom(
        backgroundColor: const Color(0xFF00E5A0),
        foregroundColor: Colors.black,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
      child: isLoading
          ? const SizedBox(
              height: 20,
              width: 20,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
            )
          : const Text(
              'Commencer l\'essai gratuit',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
    );
  }

  Future<void> _handlePurchase() async {
    if (_selectedProductId == null) return;
    final notifier = ref.read(purchaseProvider.notifier);
    final result = await notifier.purchase(_selectedProductId!);

    if (!mounted) return;

    if (result.success) {
      // Refresh entitlements to reflect new plan
      ref.read(entitlementsProvider.notifier).refresh();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Abonnement activé ! Bienvenue dans ${kPlanDisplayName[result.planCode] ?? "SOMA Premium"}.',
          ),
          backgroundColor: const Color(0xFF00E5A0),
        ),
      );
      if (mounted) Navigator.pop(context);
    } else {
      if (result.error != 'Purchase cancelled') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.error ?? 'Erreur lors de l\'achat.'),
            backgroundColor: const Color(0xFFFF3B30),
          ),
        );
      }
    }
  }

  Future<void> _handleRestore() async {
    final notifier = ref.read(purchaseProvider.notifier);
    final result = await notifier.restore();

    if (!mounted) return;

    if (result.success && result.planCode != SomaPlanCode.free) {
      ref.read(entitlementsProvider.notifier).refresh();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Abonnement restauré : ${kPlanDisplayName[result.planCode] ?? "SOMA Premium"}.',
          ),
          backgroundColor: const Color(0xFF00E5A0),
        ),
      );
      if (mounted) Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aucun abonnement actif trouvé.')),
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Sub-widgets
// ---------------------------------------------------------------------------

class _PlanTab extends StatelessWidget {
  const _PlanTab({
    required this.label,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.all(4),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF00E5A0) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: TextStyle(
                color: selected ? Colors.black : Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
              textAlign: TextAlign.center,
            ),
            Text(
              subtitle,
              style: TextStyle(
                color: selected ? const Color(0xFF004D33) : const Color(0xFF888888),
                fontSize: 11,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({
    required this.productId,
    required this.label,
    required this.selected,
    required this.onTap,
    this.product,
    this.savingsBadge,
  });

  final String productId;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final ProductDetails? product;
  final String? savingsBadge;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected
              ? const Color(0xFF00E5A0).withOpacity(0.1)
              : const Color(0xFF1A1A1A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? const Color(0xFF00E5A0) : const Color(0xFF2A2A2A),
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(
                  selected
                      ? Icons.radio_button_checked
                      : Icons.radio_button_off,
                  color: selected
                      ? const Color(0xFF00E5A0)
                      : const Color(0xFF444444),
                  size: 20,
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                    if (savingsBadge != null)
                      Container(
                        margin: const EdgeInsets.only(top: 2),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00E5A0).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          savingsBadge!,
                          style: const TextStyle(
                            color: Color(0xFF00E5A0),
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
            // Price from App Store (set by Apple, not us — no hardcoded price)
            Text(
              product?.price ?? '—',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
