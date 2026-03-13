/// SOMA LOT 17 — Coach Platform Notifier.
///
/// Gère le dashboard coach : liste athlètes, alertes, vue d'ensemble.
/// POST /api/v1/coach-platform/coach/profile (création profil)
/// POST /api/v1/coach-platform/athletes (ajout athlète)
/// GET /api/v1/coach-platform/dashboard (agrégateur)
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/coach_platform.dart';

// ── Provider principal : dashboard coach ──────────────────────────────────────

final coachDashboardProvider = AsyncNotifierProvider<CoachDashboardNotifier,
    CoachAthletesOverview?>(CoachDashboardNotifier.new);

class CoachDashboardNotifier
    extends AsyncNotifier<CoachAthletesOverview?> {
  @override
  Future<CoachAthletesOverview?> build() async {
    return _fetchDashboard();
  }

  Future<CoachAthletesOverview?> _fetchDashboard() async {
    final client = ref.read(apiClientProvider);
    try {
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.coachDashboard,
      );
      final data = responseJson(response);
      return CoachAthletesOverview.fromJson(data);
    } catch (e) {
      // Coach profile may not exist yet — return null gracefully.
      return null;
    }
  }

  /// Recharge le dashboard depuis l'API.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchDashboard);
  }

  /// Crée ou met à jour le profil coach de l'utilisateur connecté.
  Future<void> createOrUpdateCoachProfile(CoachProfileCreate create) async {
    final client = ref.read(apiClientProvider);
    await client.post(
      ApiConstants.coachProfile,
      data: create.toJson(),
    );
    await refresh();
  }

  /// Ajoute un athlète à la liste du coach.
  Future<void> addAthlete(AthleteCreate create) async {
    final client = ref.read(apiClientProvider);
    await client.post(
      ApiConstants.coachAthletes,
      data: create.toJson(),
    );
    await refresh();
  }

  /// Supprime (désactive) un lien coach–athlète.
  Future<void> removeAthlete(String athleteId) async {
    final client = ref.read(apiClientProvider);
    await client.delete(
      '${ApiConstants.coachAthletes}/$athleteId',
    );
    await refresh();
  }
}

// ── Provider profil coach ─────────────────────────────────────────────────────

final coachProfileProvider =
    AsyncNotifierProvider<CoachProfileNotifier, CoachProfile?>(
  CoachProfileNotifier.new,
);

class CoachProfileNotifier extends AsyncNotifier<CoachProfile?> {
  @override
  Future<CoachProfile?> build() async {
    final client = ref.read(apiClientProvider);
    try {
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.coachProfile,
      );
      final data = responseJson(response);
      return CoachProfile.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final client = ref.read(apiClientProvider);
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.coachProfile,
      );
      return CoachProfile.fromJson(responseJson(response));
    });
  }
}

// ── Provider alertes athlète (pour detail screen) ─────────────────────────────

final athleteAlertsProvider = AsyncNotifierProviderFamily<
    AthleteAlertsNotifier, List<AthleteAlert>, String>(
  AthleteAlertsNotifier.new,
);

class AthleteAlertsNotifier
    extends FamilyAsyncNotifier<List<AthleteAlert>, String> {
  @override
  Future<List<AthleteAlert>> build(String athleteId) async {
    return _fetchAlerts(athleteId);
  }

  Future<List<AthleteAlert>> _fetchAlerts(String athleteId) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<List<dynamic>>(
      '${ApiConstants.coachAthletes}/$athleteId/alerts',
    );
    final data = response.data ?? [];
    return data
        .cast<Map<String, dynamic>>()
        .map(AthleteAlert.fromJson)
        .toList();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchAlerts(arg));
  }
}

// ── Provider notes athlète ────────────────────────────────────────────────────

final athleteNotesProvider = AsyncNotifierProviderFamily<
    AthleteNotesNotifier, List<AthleteNote>, String>(
  AthleteNotesNotifier.new,
);

class AthleteNotesNotifier
    extends FamilyAsyncNotifier<List<AthleteNote>, String> {
  @override
  Future<List<AthleteNote>> build(String athleteId) async {
    return _fetchNotes(athleteId);
  }

  Future<List<AthleteNote>> _fetchNotes(String athleteId) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<List<dynamic>>(
      ApiConstants.coachNotes,
      queryParameters: {'athlete_id': athleteId},
    );
    final data = response.data ?? [];
    return data
        .cast<Map<String, dynamic>>()
        .map(AthleteNote.fromJson)
        .toList();
  }

  Future<void> addNote(AthleteNoteCreate create) async {
    final client = ref.read(apiClientProvider);
    await client.post(ApiConstants.coachNotes, data: create.toJson());
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchNotes(arg));
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchNotes(arg));
  }
}
