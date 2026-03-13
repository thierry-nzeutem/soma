/// Onboarding Notifier — SOMA LOT 18.
///
/// Gère l'état de l'onboarding et la soumission au serveur.
/// Pattern StateNotifier compatible avec l'architecture SOMA existante.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/onboarding.dart';

// ── Provider ──────────────────────────────────────────────────────────────────

/// Provider de l'état d'onboarding.
/// Utiliser `ref.read(onboardingProvider.notifier)` pour modifier l'état.
final onboardingProvider =
    StateNotifierProvider<OnboardingNotifier, OnboardingData>(
  (ref) => OnboardingNotifier(ref.read(apiClientProvider)),
);

// ── Notifier ──────────────────────────────────────────────────────────────────

class OnboardingNotifier extends StateNotifier<OnboardingData> {
  final ApiClient _client;

  OnboardingNotifier(this._client) : super(OnboardingData());

  // ── Mises à jour des champs ───────────────────────────────────────────────

  void setFirstName(String? name) {
    state = state.copyWith(firstName: name);
  }

  void setPrimaryGoal(String goal) {
    state = state.copyWith(primaryGoal: goal);
  }

  void setAge(int age) {
    state = state.copyWith(age: age);
  }

  void setSex(String sex) {
    state = state.copyWith(sex: sex);
  }

  void setHeightCm(double h) {
    state = state.copyWith(heightCm: h);
  }

  void setWeightKg(double w) {
    state = state.copyWith(weightKg: w);
  }

  void setGoalWeightKg(double? gw) {
    state = state.copyWith(goalWeightKg: gw);
  }

  void setActivityLevel(String level) {
    // Mapping auto du fitnessLevel selon l'activité
    final fitness = switch (level) {
      'athlete' => 'athlete',
      'moderate' => 'intermediate',
      _ => 'beginner',
    };
    state = state.copyWith(activityLevel: level, fitnessLevel: fitness);
  }

  void setSportFrequency(int freq) {
    state = state.copyWith(sportFrequencyPerWeek: freq);
  }

  void setSleepHours(double h) {
    state = state.copyWith(sleepHoursPerNight: h);
  }

  void setSleepQuality(String quality) {
    state = state.copyWith(estimatedSleepQuality: quality);
  }

  void setHasBiomarkerAccess(bool value) {
    state = state.copyWith(hasBiomarkerAccess: value);
  }

  // ── Soumission ────────────────────────────────────────────────────────────

  /// POST /profile/onboarding — retourne [OnboardingResult].
  ///
  /// Throws [Exception] si l'appel échoue.
  Future<OnboardingResult> submit() async {
    final response = await _client.post(
      ApiConstants.profileOnboarding,
      data: state.toJson(),
    );
    return OnboardingResult.fromJson(
      response.data as Map<String, dynamic>,
    );
  }

  /// Remet l'état à zéro (ex: déconnexion).
  void reset() {
    state = OnboardingData();
  }
}
