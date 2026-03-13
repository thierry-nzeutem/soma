/// OfflineBanner — Bandeau réseau discret affiché en mode hors-ligne.
///
/// Usage :
///   Envelopper le body d'un écran avec [OfflineBannerWrapper],
///   ou afficher [OfflineBanner] directement dans un Column.
///
/// La bannière disparaît automatiquement à la reconnexion.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/offline/connectivity_service.dart';

/// Bannière autonome qui se cache quand le réseau est disponible.
class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(isOnlineProvider);
    if (isOnline) return const SizedBox.shrink();

    return _OfflineBannerContent();
  }
}

class _OfflineBannerContent extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: const Color(0xFFFF6B35).withOpacity(0.15),
      child: Row(
        children: [
          const Icon(
            Icons.wifi_off_rounded,
            size: 16,
            color: Color(0xFFFF6B35),
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Hors connexion — données en cache affichées',
              style: TextStyle(
                color: Color(0xFFFF6B35),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Wrapper qui insère automatiquement la bannière offline en haut du body.
///
/// Usage :
/// ```dart
/// Scaffold(
///   body: OfflineBannerWrapper(
///     child: MyContent(),
///   ),
/// )
/// ```
class OfflineBannerWrapper extends StatelessWidget {
  const OfflineBannerWrapper({
    super.key,
    required this.child,
  });

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const OfflineBanner(),
        Expanded(child: child),
      ],
    );
  }
}

/// Indicateur compact inline (ex: dans un AppBar ou une card).
class OfflineChip extends ConsumerWidget {
  const OfflineChip({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(isOnlineProvider);
    if (isOnline) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: const Color(0xFFFF6B35).withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.wifi_off_rounded, size: 12, color: Color(0xFFFF6B35)),
          SizedBox(width: 4),
          Text(
            'Hors ligne',
            style: TextStyle(
              color: Color(0xFFFF6B35),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
