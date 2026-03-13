/// CacheBadge — Badge discret indiquant la fraîcheur des données en cache.
///
/// S'affiche uniquement si les données proviennent du cache (pas du réseau).
///
/// Usage :
///   CacheBadge(source: DataSource.cache, updatedAt: DateTime.now())
library;

import 'package:flutter/material.dart';

import '../../core/cache/cached_notifier.dart';
import '../../core/theme/theme_extensions.dart';

/// Badge compact affiché en bas d'une card pour indiquer l'âge du cache.
class CacheBadge extends StatelessWidget {
  const CacheBadge({
    super.key,
    required this.source,
    this.updatedAt,
    this.compact = false,
  });

  final DataSource source;
  final DateTime? updatedAt;

  /// Si true, affiche uniquement l'icône sans texte.
  final bool compact;

  @override
  Widget build(BuildContext context) {
    if (source == DataSource.network) return const SizedBox.shrink();

    final colors = context.somaColors;
    final isStale = source == DataSource.stale;
    final color = isStale ? colors.warning : const Color(0xFF9E9E9E);
    final label = _label(isStale);

    if (compact) {
      return Icon(
        isStale ? Icons.warning_amber_rounded : Icons.cached_rounded,
        size: 14,
        color: color,
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          isStale ? Icons.warning_amber_rounded : Icons.cached_rounded,
          size: 12,
          color: color,
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 11,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  String _label(bool isStale) {
    if (updatedAt == null) {
      return isStale ? 'Données obsolètes' : 'Données en cache';
    }
    final diff = DateTime.now().difference(updatedAt!);
    final minutes = diff.inMinutes;
    if (minutes < 1) return 'Cache récent';
    if (minutes < 60) return 'Cache · il y a ${minutes}min';
    final hours = diff.inHours;
    if (hours < 24) return 'Cache · il y a ${hours}h';
    return isStale ? 'Données obsolètes (${diff.inDays}j)' : 'Cache · ${diff.inDays}j';
  }
}

/// Wrapper qui ajoute automatiquement un badge cache en bas d'un widget.
class WithCacheBadge extends StatelessWidget {
  const WithCacheBadge({
    super.key,
    required this.child,
    required this.source,
    this.updatedAt,
    this.alignment = Alignment.bottomRight,
    this.padding = const EdgeInsets.all(8),
  });

  final Widget child;
  final DataSource source;
  final DateTime? updatedAt;
  final Alignment alignment;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    if (source == DataSource.network) return child;

    return Stack(
      children: [
        child,
        Positioned(
          bottom: padding.bottom,
          right: padding.right,
          child: CacheBadge(source: source, updatedAt: updatedAt, compact: true),
        ),
      ],
    );
  }
}
