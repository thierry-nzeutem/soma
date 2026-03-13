/// Modèles de données Coach IA SOMA — LOT 9.
///
/// CoachAnswer     : réponse structurée du coach
/// CoachThread     : fil de conversation
/// CoachMessage    : message individuel (user | coach)
library;

// ── Réponse coach ─────────────────────────────────────────────────────────────

class CoachAnswer {
  final String summary;
  final String fullResponse;
  final List<String> recommendations;
  final List<String> warnings;
  final double confidence;
  final int contextTokensEstimate;
  final String modelUsed;
  final String threadId;
  final String messageId;

  const CoachAnswer({
    required this.summary,
    required this.fullResponse,
    required this.recommendations,
    required this.warnings,
    required this.confidence,
    required this.contextTokensEstimate,
    required this.modelUsed,
    required this.threadId,
    required this.messageId,
  });

  factory CoachAnswer.fromJson(Map<String, dynamic> json) {
    return CoachAnswer(
      summary: json['summary'] as String? ?? '',
      fullResponse: json['full_response'] as String? ?? '',
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.75,
      contextTokensEstimate: json['context_tokens_estimate'] as int? ?? 0,
      modelUsed: json['model_used'] as String? ?? 'mock',
      threadId: json['thread_id'] as String? ?? '',
      messageId: json['message_id'] as String? ?? '',
    );
  }
}

// ── Fil de conversation ───────────────────────────────────────────────────────

class CoachThread {
  final String id;
  final String? title;
  final String? summary;
  final DateTime createdAt;
  final DateTime updatedAt;

  const CoachThread({
    required this.id,
    this.title,
    this.summary,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CoachThread.fromJson(Map<String, dynamic> json) {
    return CoachThread(
      id: json['id'] as String? ?? '',
      title: json['title'] as String?,
      summary: json['summary'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : DateTime.now(),
    );
  }

  /// Label d'affichage : titre ou date formatée.
  String get displayTitle {
    if (title != null && title!.isNotEmpty) return title!;
    final d = createdAt;
    return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
  }
}

// ── Message de conversation ───────────────────────────────────────────────────

class CoachMessage {
  final String id;
  final String threadId;
  final String role; // 'user' | 'coach'
  final String content;
  final DateTime createdAt;
  final Map<String, dynamic>? metadata;

  const CoachMessage({
    required this.id,
    required this.threadId,
    required this.role,
    required this.content,
    required this.createdAt,
    this.metadata,
  });

  bool get isUser => role == 'user';
  bool get isCoach => role == 'coach';

  factory CoachMessage.fromJson(Map<String, dynamic> json) {
    return CoachMessage(
      id: json['id'] as String? ?? '',
      threadId: json['thread_id'] as String? ?? '',
      role: json['role'] as String? ?? 'user',
      content: json['content'] as String? ?? '',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}

// ── Quick prompts ─────────────────────────────────────────────────────────────

class CoachQuickPrompt {
  final String label;
  final String prompt;
  final String icon;

  const CoachQuickPrompt({
    required this.label,
    required this.prompt,
    required this.icon,
  });
}

const kCoachQuickPrompts = [
  CoachQuickPrompt(
    label: 'Analyse ma journée',
    prompt: 'Analyse ma journée d\'aujourd\'hui et dis-moi ce que je dois améliorer.',
    icon: '📊',
  ),
  CoachQuickPrompt(
    label: 'Dois-je m\'entraîner ?',
    prompt: 'Est-ce que je dois m\'entraîner aujourd\'hui compte tenu de mon état de récupération ?',
    icon: '💪',
  ),
  CoachQuickPrompt(
    label: 'Que manger ce soir ?',
    prompt: 'Que dois-je manger ce soir pour atteindre mes objectifs nutritionnels du jour ?',
    icon: '🥗',
  ),
  CoachQuickPrompt(
    label: 'Pourquoi suis-je fatigué ?',
    prompt: 'Pourquoi suis-je aussi fatigué aujourd\'hui ? Analyse mes données.',
    icon: '😴',
  ),
];
