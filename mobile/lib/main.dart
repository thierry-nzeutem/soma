/// SOMA — Personal Health Intelligence
/// Entry point Flutter — LOT 12 Mobile Reliability.
///
/// Architecture :
///   - Riverpod (flutter_riverpod) pour la gestion d'état
///   - GoRouter pour la navigation déclarative avec guard auth
///   - 5 onglets : Dashboard | Journal | Plan | Insights | Profil
///   - Coach IA accessible via FAB dashboard + onglet Insights
///   - Sous-routes hors ShellRoute : saisie données, paramètres, historique, coach
///   - LOT 11 : Jumeau Numérique, Âge Biologique, Nutrition Adaptative, Motion Intelligence
///   - LOT 12 : Offline-first, sync queue, notifications, settings control center
///   - Design system avec theme clair/sombre/systeme (accent vert menthe #00E5A0)
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/auth/token_storage.dart';
import 'core/theme/theme_provider.dart';
import 'features/auth/auth_notifier.dart';
import 'features/vision/models/vision_session.dart';
import 'features/vision/screens/vision_exercise_setup_screen.dart';
import 'features/vision/screens/vision_history_screen.dart';
import 'features/vision/screens/vision_session_history_detail_screen.dart';
import 'features/vision/screens/vision_session_summary_screen.dart';
import 'features/vision/screens/vision_workout_screen.dart';
import 'features/auth/auth_state.dart';
import 'features/auth/login_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/health_plan/health_plan_screen.dart';
import 'features/history/metrics_history_screen.dart';
import 'features/hydration/hydration_screen.dart';
import 'features/insights/insights_screen.dart';
import 'features/journal/journal_hub_screen.dart';
import 'features/longevity/longevity_screen.dart';
import 'features/nutrition/food_search_screen.dart';
import 'features/nutrition/nutrition_entry_form_screen.dart';
import 'features/nutrition/nutrition_home_screen.dart';
import 'features/nutrition/photo_review_screen.dart';
import 'features/profile/edit_profile_screen.dart';
import 'features/profile/profile_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/sleep/sleep_screen.dart';
import 'features/workout/exercise_picker_screen.dart';
import 'features/workout/workout_session_create_screen.dart';
import 'features/workout/workout_session_detail_screen.dart';
import 'features/workout/workout_sessions_screen.dart';
import 'features/coach/coach_chat_screen.dart';
import 'features/coach/coach_conversation_list_screen.dart';

// ── LOT 11 — Advanced Intelligence ───────────────────────────────────────────
import 'features/twin/twin_status_screen.dart';
import 'features/twin/twin_history_screen.dart';
import 'features/biological_age/biological_age_screen.dart';
import 'features/biological_age/biological_age_history_screen.dart';
import 'features/adaptive_nutrition/adaptive_nutrition_screen.dart';
import 'features/motion/motion_summary_screen.dart';
import 'features/motion/motion_history_screen.dart';

// ── LOT 12 — Mobile Reliability ──────────────────────────────────────────────
import 'core/background/background_refresh_service.dart';
import 'core/notifications/notification_service.dart';
import 'features/settings/notification_preferences_screen.dart';
import 'features/settings/cache_management_screen.dart';

// ── LOT 13-16 — Extended Intelligence ────────────────────────────────────────
import 'features/learning/learning_profile_screen.dart';
import 'features/injury/injury_risk_screen.dart';

// ── LOT 17 — Coach Platform + Biomarkers ─────────────────────────────────────
import 'features/coach_platform/coach_dashboard_screen.dart';
import 'features/coach_platform/athlete_detail_screen.dart';
import 'features/biomarkers/biomarker_analysis_screen.dart';
import 'features/biomarkers/biomarker_results_screen.dart';

// ── LOT 18 — Productization & Daily Experience Engine ─────────────────────────
import 'features/onboarding/onboarding_screen.dart';
import 'features/briefing/morning_briefing_screen.dart';
import 'features/quick_journal/quick_journal_screen.dart';

// ── LOT 19 — Product Analytics Dashboard ──────────────────────────────────────
import 'features/admin/analytics_dashboard_screen.dart';

// -- Withings-inspired features (body composition, fitness, activity, HR, sleep quality, reports) --
import 'features/body_composition/body_composition_screen.dart';
import 'features/fitness/fitness_screen.dart';
import 'features/activity/activity_screen.dart';
import 'features/heart_rate/heart_rate_screen.dart';
import 'features/sleep/sleep_quality_screen.dart';
import 'features/reports/reports_screen.dart';

// ── BATCH 6 — Sleep Insights ──────────────────────────────────────────────────
import 'features/sleep/sleep_insights_screen.dart';

// -- V2 features (HRV, Gamification, Cycle) --
import 'features/hrv/hrv_screen.dart';
import 'features/gamification/gamification_screen.dart';

// ── BATCH 7 — i18n ───────────────────────────────────────────────────────────
import 'package:flutter_localizations/flutter_localizations.dart';
import 'l10n/app_localizations.dart';
import 'core/l10n/locale_provider.dart';

// ── Routes GoRouter ───────────────────────────────────────────────────────────

GoRouter _buildRouter(WidgetRef ref) {
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final auth = ref.read(authProvider);
      final isLogin = state.uri.path == '/login';
      if (auth is AuthStateUnauthenticated || auth is AuthStateInitial) {
        return isLogin ? null : '/login';
      }
      if (auth is AuthStateAuthenticated && isLogin) {
        return '/';
      }
      return null;
    },
    refreshListenable: _AuthListenable(ref),
    routes: [
      // ── Auth ────────────────────────────────────────────────────────────
      GoRoute(
        path: '/login',
        name: 'login',
        pageBuilder: (context, state) => const NoTransitionPage(
          child: LoginScreen(),
        ),
      ),

      // ── Shell principal 5 onglets ────────────────────────────────────────
      ShellRoute(
        builder: (context, state, child) => _MainShell(child: child),
        routes: [
          // Dashboard
          GoRoute(
            path: '/',
            name: 'dashboard',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: DashboardScreen(),
            ),
          ),
          // Journal hub
          GoRoute(
            path: '/journal',
            name: 'journal',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: JournalHubScreen(),
            ),
          ),
          // Plan du jour
          GoRoute(
            path: '/plan',
            name: 'health_plan',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: HealthPlanScreen(),
            ),
          ),
          // Insights
          GoRoute(
            path: '/insights',
            name: 'insights',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: InsightsScreen(),
            ),
          ),
          // Profil
          GoRoute(
            path: '/profile',
            name: 'profile',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ProfileScreen(),
            ),
          ),
          // Longévité (accessible depuis Profil)
          GoRoute(
            path: '/longevity',
            name: 'longevity',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: LongevityScreen(),
            ),
          ),
        ],
      ),

      // ── Sous-routes hors ShellRoute (plein écran, bouton retour) ─────────

      // Nutrition
      GoRoute(
        path: '/journal/nutrition',
        name: 'nutrition_home',
        builder: (context, state) => const NutritionHomeScreen(),
      ),
      GoRoute(
        path: '/journal/nutrition/add',
        name: 'nutrition_add',
        builder: (context, state) => const NutritionEntryFormScreen(),
      ),
      GoRoute(
        path: '/journal/nutrition/search',
        name: 'nutrition_search',
        builder: (context, state) => const FoodSearchScreen(),
      ),
      GoRoute(
        path: '/journal/nutrition/photo',
        name: 'nutrition_photo',
        builder: (context, state) => const PhotoReviewScreen(),
      ),

      // Workout
      GoRoute(
        path: '/journal/workout',
        name: 'workout_sessions',
        builder: (context, state) => const WorkoutSessionsScreen(),
      ),
      GoRoute(
        path: '/journal/workout/create',
        name: 'workout_create',
        builder: (context, state) => const WorkoutSessionCreateScreen(),
      ),
      GoRoute(
        path: '/journal/workout/:sessionId',
        name: 'workout_detail',
        builder: (context, state) => WorkoutSessionDetailScreen(
          sessionId: state.pathParameters['sessionId']!,
        ),
      ),
      GoRoute(
        path: '/journal/workout/:sessionId/exercises',
        name: 'exercise_picker',
        builder: (context, state) => const ExercisePickerScreen(),
      ),

      // Hydratation
      GoRoute(
        path: '/journal/hydration',
        name: 'hydration',
        builder: (context, state) => const HydrationScreen(),
      ),

      // Sommeil
      GoRoute(
        path: '/journal/sleep',
        name: 'sleep',
        builder: (context, state) => const SleepScreen(),
      ),
      GoRoute(
        path: '/journal/sleep/insights',
        name: 'sleep_insights',
        builder: (context, state) => const SleepInsightsScreen(),
      ),

      // Profil — édition
      GoRoute(
        path: '/profile/edit',
        name: 'profile_edit',
        builder: (context, state) => const EditProfileScreen(),
      ),

      // Historique métriques
      GoRoute(
        path: '/profile/history',
        name: 'history',
        builder: (context, state) => const MetricsHistoryScreen(),
      ),

      // Paramètres
      GoRoute(
        path: '/settings',
        name: 'settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/settings/notifications',
        name: 'settings_notifications',
        builder: (context, state) => const NotificationPreferencesScreen(),
      ),
      GoRoute(
        path: '/settings/cache',
        name: 'settings_cache',
        builder: (context, state) => const CacheManagementScreen(),
      ),

      // ── Computer Vision (LOT 7) ─────────────────────────────────────────
      GoRoute(
        path: '/vision/setup',
        name: 'vision_setup',
        builder: (context, state) => VisionExerciseSetupScreen(
          workoutSessionId: state.uri.queryParameters['sessionId'],
        ),
      ),
      GoRoute(
        path: '/vision/workout',
        name: 'vision_workout',
        builder: (context, state) => const VisionWorkoutScreen(),
      ),
      GoRoute(
        path: '/vision/summary',
        name: 'vision_summary',
        builder: (context, state) => const VisionSessionSummaryScreen(),
      ),
      GoRoute(
        path: '/vision/history',
        name: 'vision_history',
        builder: (context, state) => const VisionHistoryScreen(),
      ),
      GoRoute(
        path: '/vision/history/detail',
        name: 'vision_history_detail',
        builder: (context, state) => VisionSessionHistoryDetailScreen(
          session: state.extra as VisionSession,
        ),
      ),

      // ── Coach IA (LOT 9) ─────────────────────────────────────────────────
      GoRoute(
        path: '/coach',
        name: 'coach_chat',
        builder: (context, state) => CoachChatScreen(
          initialThreadId: state.extra as String?,
        ),
      ),
      GoRoute(
        path: '/coach/history',
        name: 'coach_history',
        builder: (context, state) => const CoachConversationListScreen(),
      ),

      // ── Jumeau Numérique (LOT 11) ─────────────────────────────────────────
      GoRoute(
        path: '/twin',
        name: 'twin',
        builder: (context, state) => const TwinStatusScreen(),
      ),
      GoRoute(
        path: '/twin/history',
        name: 'twin_history',
        builder: (context, state) => const TwinHistoryScreen(),
      ),

      // ── Âge Biologique (LOT 11) ───────────────────────────────────────────
      GoRoute(
        path: '/biological-age',
        name: 'biological_age',
        builder: (context, state) => const BiologicalAgeScreen(),
      ),
      GoRoute(
        path: '/biological-age/history',
        name: 'biological_age_history',
        builder: (context, state) => const BiologicalAgeHistoryScreen(),
      ),

      // ── Nutrition Adaptative (LOT 11) ─────────────────────────────────────
      GoRoute(
        path: '/adaptive-nutrition',
        name: 'adaptive_nutrition',
        builder: (context, state) => const AdaptiveNutritionScreen(),
      ),

      // ── Motion Intelligence (LOT 11) ──────────────────────────────────────
      GoRoute(
        path: '/motion',
        name: 'motion',
        builder: (context, state) => const MotionSummaryScreen(),
      ),
      GoRoute(
        path: '/motion/history',
        name: 'motion_history',
        builder: (context, state) => const MotionHistoryScreen(),
      ),

      // ── Profil Appris (LOT 13) ────────────────────────────────────────────
      GoRoute(
        path: '/learning',
        name: 'learning_profile',
        builder: (context, state) => const LearningProfileScreen(),
      ),

      // ── Risque Blessure Avancé (LOT 15) ──────────────────────────────────
      GoRoute(
        path: '/injury',
        name: 'injury_risk',
        builder: (context, state) => const InjuryRiskScreen(),
      ),

      // ── Coach Platform (LOT 17) ───────────────────────────────────────────
      GoRoute(
        path: '/coach-platform',
        name: 'coach_platform',
        builder: (context, state) => const CoachDashboardScreen(),
      ),
      GoRoute(
        path: '/coach-platform/athlete/:id',
        name: 'athlete_detail',
        builder: (context, state) => AthleteDetailScreen(
          athleteId: state.pathParameters['id']!,
        ),
      ),

      // ── Biomarqueurs (LOT 17) ─────────────────────────────────────────────
      GoRoute(
        path: '/biomarkers',
        name: 'biomarkers',
        builder: (context, state) => const BiomarkerAnalysisScreen(),
      ),
      GoRoute(
        path: '/biomarkers/results',
        name: 'biomarker_results',
        builder: (context, state) => const BiomarkerResultsScreen(),
      ),

      // ── LOT 18 — Onboarding + Briefing + Quick Journal ───────────────────
      GoRoute(
        path: '/onboarding',
        name: 'onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/briefing',
        name: 'morning_briefing',
        builder: (context, state) => const MorningBriefingScreen(),
      ),
      GoRoute(
        path: '/quick-journal',
        name: 'quick_journal',
        builder: (context, state) => const QuickJournalScreen(),
      ),

      // ── LOT 19 — Analytics Dashboard Admin ───────────────────────────────
      GoRoute(
        path: '/admin/analytics',
        name: 'admin_analytics',
        builder: (context, state) => const AnalyticsDashboardScreen(),
      ),

      // -- Withings-inspired features --
      GoRoute(
        path: '/body-composition',
        name: 'body_composition',
        builder: (context, state) => const BodyCompositionScreen(),
      ),
      GoRoute(
        path: '/fitness',
        name: 'fitness',
        builder: (context, state) => const FitnessScreen(),
      ),
      GoRoute(
        path: '/activity',
        name: 'activity_analytics',
        builder: (context, state) => const ActivityScreen(),
      ),
      GoRoute(
        path: '/heart-rate',
        name: 'heart_rate',
        builder: (context, state) => const HeartRateScreen(),
      ),
      GoRoute(
        path: '/sleep/quality',
        name: 'sleep_quality',
        builder: (context, state) => const SleepQualityScreen(),
      ),
      GoRoute(
        path: '/reports',
        name: 'reports',
        builder: (context, state) => const ReportsScreen(),
      ),
      GoRoute(
        path: '/hrv',
        name: 'hrv_analytics',
        builder: (context, state) => const HRVScreen(),
      ),
      GoRoute(
        path: '/gamification',
        name: 'gamification',
        builder: (context, state) => const GamificationScreen(),
      ),
    ],
  );
}

// ── App principale ────────────────────────────────────────────────────────────

const _kNavBg = Color(0xFF0A0A0A);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await TokenStorage.load();

  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: _kNavBg,
    systemNavigationBarIconBrightness: Brightness.light,
  ));

  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // LOT 12: Initialiser les services de fiabilité.
  await NotificationService.instance.initialize();
  BackgroundRefreshService.instance.initialize();

  runApp(
    const ProviderScope(child: SomaApp()),
  );
}

class SomaApp extends ConsumerStatefulWidget {
  const SomaApp({super.key});

  @override
  ConsumerState<SomaApp> createState() => _SomaAppState();
}

class _SomaAppState extends ConsumerState<SomaApp> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangePlatformBrightness() {
    // Update platform brightness when system theme changes.
    ref.read(platformBrightnessProvider.notifier).state =
        WidgetsBinding.instance.platformDispatcher.platformBrightness;
  }

  @override
  Widget build(BuildContext context) {
    final router = _buildRouter(ref);
    final theme = ref.watch(somaThemeProvider);
    final brightness = ref.watch(resolvedBrightnessProvider);

    // Update system UI overlay style based on theme.
    final isDark = brightness == Brightness.dark;
    SystemChrome.setSystemUIOverlayStyle(
      isDark ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark,
    );

    final locale = ref.watch(localeProvider);

    return MaterialApp.router(
      title: 'SOMA',
      debugShowCheckedModeBanner: false,
      routerConfig: router,
      theme: theme,
      locale: locale,
      supportedLocales: kSupportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}

// ── Shell avec BottomNavigationBar (5 onglets) ────────────────────────────────

class _MainShell extends ConsumerWidget {
  final Widget child;

  const _MainShell({required this.child});

  static int _locationToIndex(String location) {
    if (location.startsWith('/journal')) return 1;
    if (location.startsWith('/plan')) return 2;
    if (location.startsWith('/insights')) return 3;
    if (location.startsWith('/profile') ||
        location.startsWith('/longevity')) { return 4; }
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;
    final currentIndex = _locationToIndex(location);
    final colors = ref.watch(somaColorsProvider);

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: colors.navBackground,
          border: Border(top: BorderSide(color: colors.navBorder)),
        ),
        child: BottomNavigationBar(
          currentIndex: currentIndex,
          backgroundColor: colors.navBackground,
          selectedItemColor: colors.accent,
          unselectedItemColor: colors.textMuted,
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          selectedFontSize: 11,
          unselectedFontSize: 11,
          onTap: (index) {
            switch (index) {
              case 0:
                context.go('/');
              case 1:
                context.go('/journal');
              case 2:
                context.go('/plan');
              case 3:
                context.go('/insights');
              case 4:
                context.go('/profile');
            }
          },
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_rounded),
              label: 'Dashboard',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.book_rounded),
              label: 'Journal',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.today_rounded),
              label: 'Plan',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.lightbulb_outline_rounded),
              label: 'Insights',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_rounded),
              label: 'Profil',
            ),
          ],
        ),
      ),
    );
  }
}

// ── Listenable pour le refresh du router ──────────────────────────────────────

class _AuthListenable extends ChangeNotifier {
  _AuthListenable(WidgetRef ref) {
    ref.listen<AuthState>(authProvider, (_, __) => notifyListeners());
  }
}
