/// Gamification Notifier - streaks et achievements SOMA.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';

// ── Models ────────────────────────────────────────────────────────────────────

class StreakInfo {
  final int current;
  final int best;
  final String? lastActive;
  final bool activeToday;
  const StreakInfo({required this.current, required this.best, this.lastActive, this.activeToday = false});
  factory StreakInfo.fromJson(Map<String, dynamic> j) => StreakInfo(
    current: (j['current'] as int?) ?? 0,
    best: (j['best'] as int?) ?? 0,
    lastActive: j['last_active'] as String?,
    activeToday: (j['active_today'] as bool?) ?? false,
  );
}

class StreaksData {
  final StreakInfo activity;
  final StreakInfo nutritionLogging;
  final StreakInfo hydration;
  final StreakInfo sleepLogging;
  final int overallScore;
  const StreaksData({required this.activity, required this.nutritionLogging, required this.hydration, required this.sleepLogging, required this.overallScore});
  factory StreaksData.fromJson(Map<String, dynamic> j) => StreaksData(
    activity: StreakInfo.fromJson(j['activity'] as Map<String, dynamic>),
    nutritionLogging: StreakInfo.fromJson(j['nutrition_logging'] as Map<String, dynamic>),
    hydration: StreakInfo.fromJson(j['hydration'] as Map<String, dynamic>),
    sleepLogging: StreakInfo.fromJson(j['sleep_logging'] as Map<String, dynamic>),
    overallScore: (j['overall_score'] as int?) ?? 0,
  );
}

class Achievement {
  final String id, title, description, icon;
  final bool unlocked;
  final double? progress;
  const Achievement({required this.id, required this.title, required this.description, required this.icon, this.unlocked = false, this.progress});
  factory Achievement.fromJson(Map<String, dynamic> j) => Achievement(
    id: j['id'] as String,
    title: j['title'] as String,
    description: j['description'] as String,
    icon: j['icon'] as String,
    unlocked: (j['unlocked'] as bool?) ?? false,
    progress: (j['progress'] as num?)?.toDouble(),
  );
}

class GamificationProfile {
  final StreaksData streaks;
  final List<Achievement> achievements;
  final int level;
  final String levelName;
  final int xp;
  final int xpToNextLevel;
  final int totalDaysActive;
  const GamificationProfile({required this.streaks, required this.achievements, required this.level, required this.levelName, required this.xp, required this.xpToNextLevel, required this.totalDaysActive});
  factory GamificationProfile.fromJson(Map<String, dynamic> j) => GamificationProfile(
    streaks: StreaksData.fromJson(j['streaks'] as Map<String, dynamic>),
    achievements: (j['achievements'] as List<dynamic>).map((e) => Achievement.fromJson(e as Map<String, dynamic>)).toList(),
    level: (j['level'] as int?) ?? 1,
    levelName: j['level_name'] as String? ?? 'Debutant',
    xp: (j['xp'] as int?) ?? 0,
    xpToNextLevel: (j['xp_to_next_level'] as int?) ?? 500,
    totalDaysActive: (j['total_days_active'] as int?) ?? 0,
  );
}

// ── Provider ──────────────────────────────────────────────────────────────────

final gamificationProvider = AsyncNotifierProvider<GamificationNotifier, GamificationProfile?>(GamificationNotifier.new);

class GamificationNotifier extends AsyncNotifier<GamificationProfile?> {
  @override
  Future<GamificationProfile?> build() => _fetch();

  Future<GamificationProfile?> _fetch() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(ApiConstants.gamificationProfile);
    final data = responseJson(response);
    return GamificationProfile.fromJson(data);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }
}
