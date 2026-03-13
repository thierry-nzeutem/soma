/// DayTypeBadge — Badge coloré indiquant le type de journée nutritionnelle.
///
/// Couleurs : REST=gris, TRAINING=bleu, INTENSE=violet, RECOVERY=vert, DELOAD=orange.
library;

import 'package:flutter/material.dart';

import '../../core/models/adaptive_nutrition.dart';

class DayTypeBadge extends StatelessWidget {
  final String dayType;
  final bool large;

  const DayTypeBadge({
    super.key,
    required this.dayType,
    this.large = false,
  });

  Color get _color {
    switch (dayType) {
      case DayType.rest:
        return const Color(0xFF6B7280);
      case DayType.training:
        return const Color(0xFF3B82F6);
      case DayType.intenseTraining:
        return const Color(0xFF8B5CF6);
      case DayType.recovery:
        return const Color(0xFF22C55E);
      case DayType.deload:
        return const Color(0xFFF59E0B);
      default:
        return const Color(0xFF6B7280);
    }
  }

  IconData get _icon {
    switch (dayType) {
      case DayType.rest:
        return Icons.hotel;
      case DayType.training:
        return Icons.fitness_center;
      case DayType.intenseTraining:
        return Icons.local_fire_department;
      case DayType.recovery:
        return Icons.healing;
      case DayType.deload:
        return Icons.self_improvement;
      default:
        return Icons.circle_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final label = DayType.label(dayType);

    if (large) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: _color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _color.withOpacity(0.4)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(_icon, size: 20, color: _color),
            const SizedBox(width: 8),
            Text(
              label,
              style: theme.textTheme.titleMedium?.copyWith(
                color: _color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _color.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(_icon, size: 14, color: _color),
          const SizedBox(width: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: _color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
