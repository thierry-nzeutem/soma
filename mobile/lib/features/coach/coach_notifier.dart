/// Coach IA Notifier — SOMA LOT 9.
///
/// Gère le state de la conversation avec le coach SOMA.
/// Providers :
///   coachChatProvider          → état du chat courant (question + réponse)
///   coachThreadsProvider       → liste des fils de conversation
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/coach.dart';

// ── State Chat ────────────────────────────────────────────────────────────────

class CoachChatState {
  final AsyncValue<CoachAnswer?> lastAnswer;
  final List<CoachMessage> messages;
  final String? currentThreadId;
  final bool isLoading;
  final String? errorMessage;

  const CoachChatState({
    this.lastAnswer = const AsyncValue.data(null),
    this.messages = const [],
    this.currentThreadId,
    this.isLoading = false,
    this.errorMessage,
  });

  CoachChatState copyWith({
    AsyncValue<CoachAnswer?>? lastAnswer,
    List<CoachMessage>? messages,
    String? currentThreadId,
    bool? isLoading,
    String? errorMessage,
    bool clearError = false,
  }) {
    return CoachChatState(
      lastAnswer: lastAnswer ?? this.lastAnswer,
      messages: messages ?? this.messages,
      currentThreadId: currentThreadId ?? this.currentThreadId,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

// ── Notifier Chat ─────────────────────────────────────────────────────────────

class CoachChatNotifier extends StateNotifier<CoachChatState> {
  final Ref _ref;

  CoachChatNotifier(this._ref) : super(const CoachChatState());

  ApiClient get _client => _ref.read(apiClientProvider);

  /// Envoie une question au coach et reçoit la réponse.
  Future<void> ask(String question) async {
    if (question.trim().isEmpty) return;

    // Ajout immédiat du message utilisateur (optimiste)
    final userMsg = CoachMessage(
      id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
      threadId: state.currentThreadId ?? '',
      role: 'user',
      content: question,
      createdAt: DateTime.now(),
    );
    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isLoading: true,
      clearError: true,
    );

    try {
      final body = <String, dynamic>{'question': question};
      if (state.currentThreadId != null) {
        body['thread_id'] = state.currentThreadId;
      }

      final response = await _client.post<Map<String, dynamic>>(
        ApiConstants.coachAsk,
        data: body,
      );

      final answer = CoachAnswer.fromJson(responseJson(response));

      // Ajouter la réponse du coach à la liste des messages
      final coachMsg = CoachMessage(
        id: answer.messageId,
        threadId: answer.threadId,
        role: 'coach',
        content: answer.fullResponse,
        createdAt: DateTime.now(),
      );

      state = state.copyWith(
        lastAnswer: AsyncValue.data(answer),
        messages: [...state.messages, coachMsg],
        currentThreadId: answer.threadId,
        isLoading: false,
      );
    } catch (e, st) {
      state = state.copyWith(
        lastAnswer: AsyncValue.error(e, st),
        isLoading: false,
        errorMessage: 'Erreur lors de la communication avec le coach',
      );
    }
  }

  /// Charge les messages d'un thread existant.
  Future<void> loadThread(String threadId) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await _client.get<Map<String, dynamic>>(
        '${ApiConstants.coachHistory}/$threadId',
      );
      final data = responseJson(response);
      final msgs = (data['messages'] as List<dynamic>? ?? [])
          .map((m) => CoachMessage.fromJson(m as Map<String, dynamic>))
          .toList();
      state = state.copyWith(
        messages: msgs,
        currentThreadId: threadId,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Impossible de charger la conversation',
      );
    }
  }

  /// Réinitialise pour une nouvelle conversation.
  void newConversation() {
    state = const CoachChatState();
  }
}

// ── Provider Chat ─────────────────────────────────────────────────────────────

final coachChatProvider =
    StateNotifierProvider.autoDispose<CoachChatNotifier, CoachChatState>(
  (ref) => CoachChatNotifier(ref),
);

// ── Provider Historique (liste des threads) ───────────────────────────────────

class CoachThreadsNotifier extends AsyncNotifier<List<CoachThread>> {
  @override
  Future<List<CoachThread>> build() => _fetchThreads();

  Future<List<CoachThread>> _fetchThreads() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.coachHistory,
    );
    final data = responseJson(response);
    final threads = (data['threads'] as List<dynamic>? ?? [])
        .map((t) => CoachThread.fromJson(t as Map<String, dynamic>))
        .toList();
    return threads;
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchThreads);
  }
}

final coachThreadsProvider =
    AsyncNotifierProvider<CoachThreadsNotifier, List<CoachThread>>(
  CoachThreadsNotifier.new,
);
