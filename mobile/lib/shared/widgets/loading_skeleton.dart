/// Widget Loading Skeleton SOMA — LOT 5.
///
/// Affiche des placeholders animés pendant le chargement des données.
/// Compatible avec le design system dark de SOMA.
library;

import 'package:flutter/material.dart';

import '../../core/theme/theme_extensions.dart';

// ── Skeleton de base ──────────────────────────────────────────────────────────

/// Rectangle animé simulant un bloc de contenu en cours de chargement.
class SkeletonBox extends StatefulWidget {
  final double width;
  final double height;
  final BorderRadius? borderRadius;

  const SkeletonBox({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius,
  });

  @override
  State<SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<SkeletonBox>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _animation = Tween<double>(begin: 0.3, end: 0.7).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (_, __) => Container(
        width: widget.width,
        height: widget.height,
        decoration: BoxDecoration(
          color: Color.fromRGBO(
            40, 40, 40, _animation.value,
          ),
          borderRadius: widget.borderRadius ?? BorderRadius.circular(8),
        ),
      ),
    );
  }
}

// ── Skeleton MetricCard ───────────────────────────────────────────────────────

/// Skeleton qui imite une MetricCard (grille dashboard).
class MetricCardSkeleton extends StatelessWidget {
  const MetricCardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.border),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              SkeletonBox(width: 24, height: 24, borderRadius: BorderRadius.all(Radius.circular(6))),
              SizedBox(width: 8),
              SkeletonBox(width: 60, height: 12),
            ],
          ),
          SizedBox(height: 12),
          SkeletonBox(width: 80, height: 28),
          SizedBox(height: 8),
          SkeletonBox(width: 50, height: 10),
          SizedBox(height: 8),
          SkeletonBox(width: double.infinity, height: 4, borderRadius: BorderRadius.all(Radius.circular(2))),
        ],
      ),
    );
  }
}

// ── Skeleton Dashboard ────────────────────────────────────────────────────────

/// Skeleton complet pour l'écran Dashboard.
class DashboardSkeleton extends StatelessWidget {
  const DashboardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Date header
          const SkeletonBox(width: 120, height: 14),
          const SizedBox(height: 20),

          // Score récupération (pleine largeur)
          Container(
            height: 90,
            decoration: BoxDecoration(
              color: colors.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: colors.border),
            ),
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Row(
                children: [
                  SkeletonBox(width: 56, height: 56, borderRadius: BorderRadius.all(Radius.circular(28))),
                  SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SkeletonBox(width: 100, height: 12),
                        SizedBox(height: 8),
                        SkeletonBox(width: 60, height: 24),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Grille 2×4 de MetricCards
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.15,
              children: const [
                MetricCardSkeleton(),
                MetricCardSkeleton(),
                MetricCardSkeleton(),
                MetricCardSkeleton(),
                MetricCardSkeleton(),
                MetricCardSkeleton(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Skeleton Insights ─────────────────────────────────────────────────────────

/// Skeleton pour la liste d'insights.
class InsightsSkeleton extends StatelessWidget {
  const InsightsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 4,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (_, __) => Container(
        height: 120,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: colors.border),
        ),
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                SkeletonBox(width: 60, height: 20, borderRadius: BorderRadius.all(Radius.circular(8))),
                SizedBox(width: 8),
                SkeletonBox(width: 80, height: 12),
              ],
            ),
            SizedBox(height: 12),
            SkeletonBox(width: 200, height: 14),
            SizedBox(height: 8),
            SkeletonBox(width: double.infinity, height: 12),
            SizedBox(height: 4),
            SkeletonBox(width: 160, height: 12),
          ],
        ),
      ),
    );
  }
}
