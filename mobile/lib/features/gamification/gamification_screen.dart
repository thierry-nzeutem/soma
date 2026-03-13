/// Gamification Screen - streaks, achievements et XP SOMA.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'gamification_notifier.dart';

IconData _achievementIcon(String name) {
  switch (name) {
    case 'dumbbell': return Icons.fitness_center_rounded;
    case 'trophy': return Icons.emoji_events_rounded;
    case 'medal': return Icons.military_tech_rounded;
    case 'apple': return Icons.apple_rounded;
    case 'moon': return Icons.nightlight_round;
    case 'droplets': return Icons.water_drop_rounded;
    case 'crown': return Icons.workspace_premium_rounded;
    default: return Icons.star_rounded;
  }
}

class GamificationScreen extends ConsumerWidget {
  const GamificationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(gamificationProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'My Progress',
        showBackButton: true,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.textSecondary),
            onPressed: () => ref.read(gamificationProvider.notifier).refresh(),
          ),
        ],
      ),
      body: async.when(
        loading: () => Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.error_outline, color: colors.danger, size: 40),
          const SizedBox(height: 12),
          Text('Could not load progress', style: TextStyle(color: colors.textMuted)),
          const SizedBox(height: 16),
          TextButton(onPressed: () => ref.read(gamificationProvider.notifier).refresh(), child: const Text('Retry')),
        ])),
        data: (profile) => profile == null
            ? Center(child: Text('No data available', style: TextStyle(color: colors.textMuted)))
            : _GamificationBody(profile: profile),
      ),
    );
  }
}

class _GamificationBody extends StatelessWidget {
  final GamificationProfile profile;
  const _GamificationBody({required this.profile});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final xpProgress = profile.xp / (profile.xp + profile.xpToNextLevel);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        // Level card
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: colors.accent.withAlpha(80)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                width: 48, height: 48,
                decoration: BoxDecoration(color: colors.accent.withAlpha(30), borderRadius: BorderRadius.circular(12)),
                child: Center(child: Text('${profile.level}', style: TextStyle(color: colors.accent, fontWeight: FontWeight.bold, fontSize: 22))),
              ),
              const SizedBox(width: 14),
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(profile.levelName, style: TextStyle(color: colors.textSecondary, fontWeight: FontWeight.bold, fontSize: 17)),
                Text('${profile.xp} XP  |  ${profile.totalDaysActive} days active', style: TextStyle(color: colors.textMuted, fontSize: 12)),
              ]),
              const Spacer(),
              Icon(Icons.workspace_premium_rounded, color: colors.accent, size: 28),
            ]),
            const SizedBox(height: 14),
            Text('${profile.xpToNextLevel} XP to next level', style: TextStyle(color: colors.textMuted, fontSize: 12)),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: xpProgress.clamp(0, 1),
                minHeight: 8,
                backgroundColor: colors.border,
                valueColor: AlwaysStoppedAnimation<Color>(colors.accent),
              ),
            ),
          ]),
        ),
        const SizedBox(height: 20),
        // Overall score
        Row(children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: colors.success.withAlpha(20),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: colors.success.withAlpha(80)),
            ),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.local_fire_department_rounded, color: colors.success, size: 16),
              const SizedBox(width: 6),
              Text('Consistency score: ${profile.streaks.overallScore}/100', style: TextStyle(color: colors.success, fontWeight: FontWeight.w600, fontSize: 13)),
            ]),
          ),
        ]),
        const SizedBox(height: 16),
        // Streaks section
        Text('Streaks', style: TextStyle(fontWeight: FontWeight.bold, color: colors.textSecondary, fontSize: 15)),
        const SizedBox(height: 10),
        _StreakRow(label: 'Activity', icon: Icons.directions_run_rounded, color: const Color(0xFFFF6B35), streak: profile.streaks.activity),
        const SizedBox(height: 8),
        _StreakRow(label: 'Nutrition', icon: Icons.restaurant_rounded, color: const Color(0xFF4CAF50), streak: profile.streaks.nutritionLogging),
        const SizedBox(height: 8),
        _StreakRow(label: 'Hydration', icon: Icons.water_drop_rounded, color: const Color(0xFF29B6F6), streak: profile.streaks.hydration),
        const SizedBox(height: 8),
        _StreakRow(label: 'Sleep', icon: Icons.nightlight_round, color: const Color(0xFF9C27B0), streak: profile.streaks.sleepLogging),
        const SizedBox(height: 24),
        // Achievements section
        Text('Achievements', style: TextStyle(fontWeight: FontWeight.bold, color: colors.textSecondary, fontSize: 15)),
        const SizedBox(height: 10),
        ...profile.achievements.map((a) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _AchievementTile(achievement: a),
        )),
        const SizedBox(height: 24),
      ]),
    );
  }
}

class _StreakRow extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final StreakInfo streak;
  const _StreakRow({required this.label, required this.icon, required this.color, required this.streak});

  @override
  Widget build(BuildContext context) {
    final c = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: c.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: c.border)),
      child: Row(children: [
        Container(
          width: 36, height: 36,
          decoration: BoxDecoration(color: color.withAlpha(25), borderRadius: BorderRadius.circular(8)),
          child: Icon(icon, color: color, size: 18),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.w600, color: c.textSecondary, fontSize: 13)),
          if (streak.activeToday)
            Row(children: [
              Container(width: 6, height: 6, margin: const EdgeInsets.only(right: 4), decoration: BoxDecoration(color: c.success, shape: BoxShape.circle)),
              Text('Active today', style: TextStyle(color: c.success, fontSize: 11)),
            ]),
        ])),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Row(children: [
            Icon(Icons.local_fire_department_rounded, color: streak.current > 0 ? color : c.textMuted, size: 16),
            const SizedBox(width: 3),
            Text('${streak.current}', style: TextStyle(fontWeight: FontWeight.bold, color: streak.current > 0 ? color : c.textMuted, fontSize: 18)),
            Text(' days', style: TextStyle(color: c.textMuted, fontSize: 11)),
          ]),
          Text('Best: ${streak.best}d', style: TextStyle(color: c.textMuted, fontSize: 11)),
        ]),
      ]),
    );
  }
}

class _AchievementTile extends StatelessWidget {
  final Achievement achievement;
  const _AchievementTile({required this.achievement});

  @override
  Widget build(BuildContext context) {
    final c = context.somaColors;
    final iconColor = achievement.unlocked ? c.accent : c.textMuted;
    final progress = achievement.progress ?? 0.0;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: c.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: achievement.unlocked ? c.accent.withAlpha(80) : c.border),
      ),
      child: Row(children: [
        Container(
          width: 44, height: 44,
          decoration: BoxDecoration(color: iconColor.withAlpha(20), borderRadius: BorderRadius.circular(10)),
          child: Stack(children: [
            Center(child: Icon(_achievementIcon(achievement.icon), color: iconColor, size: 22)),
            if (!achievement.unlocked)
              Positioned(right: 0, bottom: 0, child: Container(
                width: 16, height: 16,
                decoration: BoxDecoration(color: c.surface, shape: BoxShape.circle, border: Border.all(color: c.border)),
                child: Icon(Icons.lock_rounded, size: 10, color: c.textMuted),
              )),
          ]),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(achievement.title, style: TextStyle(fontWeight: FontWeight.w600, color: achievement.unlocked ? c.textSecondary : c.textMuted, fontSize: 13)),
          Text(achievement.description, style: TextStyle(color: c.textMuted, fontSize: 11)),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress.clamp(0, 1),
              minHeight: 4,
              backgroundColor: c.border,
              valueColor: AlwaysStoppedAnimation<Color>(achievement.unlocked ? c.accent : c.textMuted),
            ),
          ),
        ])),
        const SizedBox(width: 12),
        if (achievement.unlocked)
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(color: c.accent.withAlpha(20), shape: BoxShape.circle),
            child: Icon(Icons.check_rounded, color: c.accent, size: 14),
          )
        else
          Text('${(progress * 100).toInt()}%', style: TextStyle(color: c.textMuted, fontSize: 12, fontWeight: FontWeight.w600)),
      ]),
    );
  }
}
