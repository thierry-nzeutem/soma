/// Riverpod notifier for coach invitations and recommendations.
library;

import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../api/api_constants.dart';
import 'coach_invite_models.dart';

// ── State classes ──────────────────────────────────────────────────────────

class InvitationsState {
  final List<CoachInvitation> invitations;
  final bool isLoading;
  final String? error;

  const InvitationsState({
    this.invitations = const [],
    this.isLoading = false,
    this.error,
  });

  InvitationsState copyWith({
    List<CoachInvitation>? invitations,
    bool? isLoading,
    String? error,
  }) {
    return InvitationsState(
      invitations: invitations ?? this.invitations,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

// ── Invitations Notifier ─────────────────────────────────────────────────

class InvitationsNotifier extends AsyncNotifier<InvitationsState> {
  @override
  Future<InvitationsState> build() async {
    return _fetchInvitations();
  }

  Future<InvitationsState> _fetchInvitations() async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.get(ApiConstants.coachInvitations);
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        final invitations = data
            .map((e) => CoachInvitation.fromJson(e as Map<String, dynamic>))
            .toList();
        return InvitationsState(invitations: invitations);
      }
      return const InvitationsState();
    } catch (e) {
      return InvitationsState(error: e.toString());
    }
  }

  Future<CoachInvitation?> createInvitation({
    String? email,
    String? message,
    int expireDays = 7,
  }) async {
    state = AsyncData(state.value!.copyWith(isLoading: true));
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.post(
        ApiConstants.coachInvitations,
        body: jsonEncode({
          if (email != null) 'invitee_email': email,
          if (message != null) 'message': message,
          'expire_days': expireDays,
        }),
      );
      if (response.statusCode == 201) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final inv = CoachInvitation.fromJson(data);
        final current = state.value!;
        state = AsyncData(current.copyWith(
          invitations: [inv, ...current.invitations],
          isLoading: false,
        ));
        return inv;
      }
      state = AsyncData(state.value!.copyWith(isLoading: false));
      return null;
    } catch (e) {
      state = AsyncData(state.value!.copyWith(isLoading: false, error: e.toString()));
      return null;
    }
  }

  Future<bool> cancelInvitation(String inviteId) async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.delete(
        '${ApiConstants.coachInvitations}/$inviteId',
      );
      if (response.statusCode == 204) {
        final current = state.value!;
        state = AsyncData(current.copyWith(
          invitations: current.invitations
              .map((i) => i.id == inviteId
                  ? CoachInvitation(
                      id: i.id,
                      coachProfileId: i.coachProfileId,
                      inviteCode: i.inviteCode,
                      inviteToken: i.inviteToken,
                      inviteLink: i.inviteLink,
                      inviteeEmail: i.inviteeEmail,
                      status: 'cancelled',
                      message: i.message,
                      expiresAt: i.expiresAt,
                      acceptedAt: i.acceptedAt,
                      createdAt: i.createdAt,
                    )
                  : i)
              .toList(),
        ));
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = AsyncData(await _fetchInvitations());
  }
}

final invitationsProvider =
    AsyncNotifierProvider<InvitationsNotifier, InvitationsState>(
  InvitationsNotifier.new,
);

// ── Accept Invitation ─────────────────────────────────────────────────────

class AcceptInviteResult {
  final bool success;
  final String message;
  final String? coachName;

  const AcceptInviteResult({
    required this.success,
    required this.message,
    this.coachName,
  });
}

Future<AcceptInviteResult> acceptInvitation(
  WidgetRef ref,
  String token,
) async {
  try {
    final client = ref.read(apiClientProvider);
    final response = await client.post(
      '${ApiConstants.coachInvitationsAccept}/$token',
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return AcceptInviteResult(
        success: true,
        message: data['message'] as String,
        coachName: data['coach_name'] as String?,
      );
    }
    final errorData = jsonDecode(response.body) as Map<String, dynamic>;
    return AcceptInviteResult(
      success: false,
      message: errorData['detail'] as String? ?? 'Erreur lors de l\'acceptation.',
    );
  } catch (e) {
    return AcceptInviteResult(
      success: false,
      message: 'Erreur réseau: ${e.toString()}',
    );
  }
}

// ── Recommendations Provider ──────────────────────────────────────────────

final athleteRecommendationsProvider =
    FutureProvider.family<List<CoachRecommendation>, String>(
  (ref, athleteId) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get(
      '${ApiConstants.coachAthleteBase}/$athleteId/recommendations',
    );
    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
      return data
          .map((e) => CoachRecommendation.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  },
);

// ── Full Athlete Profile Provider ─────────────────────────────────────────

final athleteFullProfileProvider =
    FutureProvider.family<AthleteFullProfile?, String>(
  (ref, athleteId) async {
    final client = ref.read(apiClientProvider);
    final response = await client.get(
      '${ApiConstants.coachAthleteBase}/$athleteId/profile',
    );
    if (response.statusCode == 200) {
      return AthleteFullProfile.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
    }
    return null;
  },
);
