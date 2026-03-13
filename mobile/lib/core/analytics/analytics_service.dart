/// Analytics Service — LOT 18 + LOT 19.
///
/// Envoie des événements produit au backend SOMA de manière fire-and-forget.
/// Ne bloque jamais l'UI — toutes les erreurs sont ignorées silencieusement.
///
/// LOT 19 : ajout des événements d'engagement Briefing et Quick Journal.
///
/// Usage :
/// ```dart
/// AnalyticsService.track(
///   ref.read(apiClientProvider),
///   AnalyticsEvents.workoutLogged,
///   props: {'type': 'strength', 'duration': 45},
/// );
/// ```
library;

import 'dart:async';

import '../api/api_client.dart';
import '../api/api_constants.dart';

// ── Constantes d'événements ────────────────────────────────────────────────────

/// Noms d'événements analytics SOMA (miroir de `EVENTS` backend).
class AnalyticsEvents {
  AnalyticsEvents._();

  /// Application ouverte (au premier build de SomaApp).
  static const String appOpen = 'app_open';

  /// Briefing matinal consulté.
  static const String morningBriefingView = 'morning_briefing_view';

  /// Saisie quelconque via le journal rapide ou écrans spécifiques.
  static const String journalEntry = 'journal_entry';

  /// Question envoyée au coach IA (thread ou quick-advice).
  static const String coachQuestion = 'coach_question';

  /// Séance d'entraînement enregistrée.
  static const String workoutLogged = 'workout_logged';

  /// Repas / entrée nutritionnelle enregistrée.
  static const String nutritionLogged = 'nutrition_logged';

  /// Insight consulté ou lu.
  static const String insightViewed = 'insight_viewed';

  /// Onboarding terminé avec succès.
  static const String onboardingComplete = 'onboarding_complete';

  /// Quick-advice coach demandé.
  static const String quickAdviceRequested = 'quick_advice_requested';

  // ── LOT 19 : Engagement Briefing ────────────────────────────────────────────

  /// Briefing matinal ouvert côté mobile (distinct de morning_briefing_view backend).
  static const String briefingOpened = 'briefing_opened';

  /// Carte du briefing consultée (ex: sleep_card, training_card…).
  static const String briefingCardView = 'briefing_card_view';

  /// CTA du briefing cliqué (journal, coach, workout).
  static const String briefingCtaClick = 'briefing_cta_click';

  // ── LOT 19 : Engagement Quick Journal ───────────────────────────────────────

  /// Quick Journal ouvert (écran chargé).
  static const String journalOpen = 'journal_open';

  /// Action soumise depuis le Quick Journal (repas, workout, hydration…).
  static const String journalActionSubmitted = 'journal_action_submitted';

  /// Action annulée (sheet fermée sans soumission).
  static const String journalActionCancelled = 'journal_action_cancelled';
}

// ── Service ───────────────────────────────────────────────────────────────────

/// Service analytics — wrappeur stateless fire-and-forget.
class AnalyticsService {
  AnalyticsService._();

  /// Envoie un événement analytics au backend.
  ///
  /// - N'attend PAS la réponse (`unawaited`).
  /// - Ne lève jamais d'exception.
  /// - Propriétés additionnelles optionnelles via [props].
  static void track(
    ApiClient client,
    String event, {
    Map<String, dynamic>? props,
  }) {
    unawaited(_send(client, event, props));
  }

  static Future<void> _send(
    ApiClient client,
    String event,
    Map<String, dynamic>? props,
  ) async {
    try {
      await client.post(
        ApiConstants.analyticsEvent,
        data: {
          'event_name': event,
          if (props != null) 'properties': props,
        },
      );
    } catch (_) {
      // Silencieux — l'analytics ne doit jamais impacter l'UX.
    }
  }
}
