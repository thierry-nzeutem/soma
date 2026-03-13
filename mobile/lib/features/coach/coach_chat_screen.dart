/// CoachChatScreen — Interface de chat avec le coach IA SOMA (LOT 9).
///
/// Fonctionnalités :
///   - Chat temps réel (question → réponse structurée)
///   - Quick prompts (4 suggestions rapides)
///   - Bulles de message différenciées (user / coach)
///   - Indicateur de chargement animé
///   - Accès à l'historique des conversations
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/coach.dart';
import '../../core/subscription/plan_models.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import '../../widgets/upgrade_gate.dart';
import 'coach_notifier.dart';

// ── Couleurs spécifiques au chat (non-thème) ────────────────────────────────
const _kAccentDim = Color(0xFF1A3D35);
const _kCoachBubble = Color(0xFF0D2A22);

// ── Screen ────────────────────────────────────────────────────────────────────

class CoachChatScreen extends ConsumerStatefulWidget {
  final String? initialThreadId;

  const CoachChatScreen({super.key, this.initialThreadId});

  @override
  ConsumerState<CoachChatScreen> createState() => _CoachChatScreenState();
}

class _CoachChatScreenState extends ConsumerState<CoachChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _showQuickPrompts = true;

  @override
  void initState() {
    super.initState();
    if (widget.initialThreadId != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ref
            .read(coachChatProvider.notifier)
            .loadThread(widget.initialThreadId!);
        setState(() => _showQuickPrompts = false);
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage([String? text]) {
    final q = text ?? _controller.text.trim();
    if (q.isEmpty) return;
    _controller.clear();
    setState(() => _showQuickPrompts = false);
    ref.read(coachChatProvider.notifier).ask(q);
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return UpgradeGate(
      feature: FeatureCode.aiCoach,
      child: _buildCoachContent(context),
    );
  }

  Widget _buildCoachContent(BuildContext context) {
    final colors = context.somaColors;
    final state = ref.watch(coachChatProvider);

    // Scroll to bottom quand de nouveaux messages arrivent
    ref.listen(coachChatProvider, (_, next) {
      if (!next.isLoading) _scrollToBottom();
    });

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'SOMA Coach',
        actions: [
          IconButton(
            icon: Icon(Icons.history_rounded, color: colors.text),
            tooltip: 'Historique',
            onPressed: () => context.push('/coach/history'),
          ),
          IconButton(
            icon: Icon(Icons.add_comment_rounded, color: colors.text),
            tooltip: 'Nouvelle conversation',
            onPressed: () {
              ref.read(coachChatProvider.notifier).newConversation();
              setState(() => _showQuickPrompts = true);
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Messages
          Expanded(
            child: state.messages.isEmpty
                ? _WelcomeView(
                    showQuickPrompts: _showQuickPrompts,
                    onPromptTap: _sendMessage,
                  )
                : _MessagesList(
                    messages: state.messages,
                    isLoading: state.isLoading,
                    scrollController: _scrollController,
                  ),
          ),

          // Erreur
          if (state.errorMessage != null)
            _ErrorBanner(message: state.errorMessage!),

          // Saisie
          _InputBar(
            controller: _controller,
            isLoading: state.isLoading,
            onSend: _sendMessage,
          ),
        ],
      ),
    );
  }
}

// ── Vue d'accueil ─────────────────────────────────────────────────────────────

class _WelcomeView extends StatelessWidget {
  final bool showQuickPrompts;
  final void Function(String) onPromptTap;

  const _WelcomeView({
    required this.showQuickPrompts,
    required this.onPromptTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const SizedBox(height: 24),
          // Logo SOMA coach
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [colors.accent, colors.info],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: const Icon(Icons.psychology_rounded,
                color: Colors.black, size: 44),
          ),
          const SizedBox(height: 20),
          Text(
            'SOMA Coach',
            style: TextStyle(
              color: colors.text,
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Ton coach santé personnalisé.\nPose-moi n\'importe quelle question sur tes données.',
            textAlign: TextAlign.center,
            style: TextStyle(color: colors.textMuted, fontSize: 14),
          ),
          const SizedBox(height: 32),
          if (showQuickPrompts) ...[
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Suggestions rapides',
                style: TextStyle(
                  color: colors.textMuted,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
            ),
            const SizedBox(height: 12),
            ...kCoachQuickPrompts.map(
              (p) => _QuickPromptCard(prompt: p, onTap: onPromptTap),
            ),
          ],
        ],
      ),
    );
  }
}

class _QuickPromptCard extends StatelessWidget {
  final CoachQuickPrompt prompt;
  final void Function(String) onTap;

  const _QuickPromptCard({required this.prompt, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: () => onTap(prompt.prompt),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: colors.border),
        ),
        child: Row(
          children: [
            Text(prompt.icon, style: const TextStyle(fontSize: 20)),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                prompt.label,
                style: TextStyle(
                  color: colors.text,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Icon(Icons.arrow_forward_ios_rounded,
                color: colors.textMuted, size: 14),
          ],
        ),
      ),
    );
  }
}

// ── Liste de messages ─────────────────────────────────────────────────────────

class _MessagesList extends StatelessWidget {
  final List<CoachMessage> messages;
  final bool isLoading;
  final ScrollController scrollController;

  const _MessagesList({
    required this.messages,
    required this.isLoading,
    required this.scrollController,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: scrollController,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      itemCount: messages.length + (isLoading ? 1 : 0),
      itemBuilder: (ctx, i) {
        if (i == messages.length) {
          return const _TypingIndicator();
        }
        return CoachMessageBubble(message: messages[i]);
      },
    );
  }
}

// ── Bulle de message ──────────────────────────────────────────────────────────

class CoachMessageBubble extends StatelessWidget {
  final CoachMessage message;

  const CoachMessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final isUser = message.isUser;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            // Avatar coach
            Container(
              width: 32,
              height: 32,
              margin: const EdgeInsets.only(right: 8, top: 2),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [colors.accent, colors.info],
                ),
              ),
              child: const Icon(Icons.psychology_rounded,
                  color: Colors.black, size: 18),
            ),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isUser ? colors.border : _kCoachBubble,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(isUser ? 16 : 4),
                  topRight: Radius.circular(isUser ? 4 : 16),
                  bottomLeft: const Radius.circular(16),
                  bottomRight: const Radius.circular(16),
                ),
                border: Border.all(
                  color: isUser
                      ? colors.border
                      : colors.accent.withOpacity(0.3),
                ),
              ),
              child: isUser
                  ? Text(
                      message.content,
                      style: TextStyle(
                          color: colors.text, fontSize: 14),
                    )
                  : _CoachResponseContent(content: message.content),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }
}

/// Affiche la réponse coach avec mise en forme Markdown simple.
class _CoachResponseContent extends StatelessWidget {
  final String content;

  const _CoachResponseContent({required this.content});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    // Parsing basique des sections Markdown
    final lines = content.split('\n');
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: lines.map((line) {
        if (line.startsWith('**') && line.contains('**', 2)) {
          // Titre en gras
          final title = line.replaceAll('**', '').trim().replaceAll(':', '');
          return Padding(
            padding: const EdgeInsets.only(bottom: 4, top: 6),
            child: Text(
              title,
              style: TextStyle(
                color: colors.accent,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          );
        } else if (line.startsWith('• ') || line.startsWith('- ')) {
          // Bullet point
          return Padding(
            padding: const EdgeInsets.only(bottom: 4, left: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('• ',
                    style: TextStyle(color: colors.accent, fontSize: 13)),
                Expanded(
                  child: Text(
                    line.substring(2).trim(),
                    style: TextStyle(
                        color: colors.text, fontSize: 13, height: 1.4),
                  ),
                ),
              ],
            ),
          );
        } else if (line.contains('⚠')) {
          // Alerte
          return Container(
            margin: const EdgeInsets.only(top: 8),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFF2A1A00),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFFFB347).withOpacity(0.4)),
            ),
            child: Text(
              line.trim(),
              style: const TextStyle(
                  color: Color(0xFFFFB347), fontSize: 12),
            ),
          );
        } else if (line.trim().isEmpty) {
          return const SizedBox(height: 4);
        } else {
          return Text(
            line,
            style: TextStyle(
                color: colors.textSecondary, fontSize: 13, height: 1.4),
          );
        }
      }).toList(),
    );
  }
}

// ── Indicateur "typing" ───────────────────────────────────────────────────────

class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            margin: const EdgeInsets.only(right: 8),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [colors.accent, colors.info],
              ),
            ),
            child: const Icon(Icons.psychology_rounded,
                color: Colors.black, size: 18),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: _kCoachBubble,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: colors.accent.withOpacity(0.3)),
            ),
            child: SizedBox(
              width: 40,
              child: LinearProgressIndicator(
                color: colors.accent,
                backgroundColor: const Color(0xFF0D3828),
                minHeight: 3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Barre de saisie ───────────────────────────────────────────────────────────

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final bool isLoading;
  final void Function([String?]) onSend;

  const _InputBar({
    required this.controller,
    required this.isLoading,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      decoration: BoxDecoration(
        color: colors.navBackground,
        border: Border(top: BorderSide(color: colors.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !isLoading,
              style: TextStyle(color: colors.text, fontSize: 14),
              maxLines: 4,
              minLines: 1,
              textInputAction: TextInputAction.send,
              onSubmitted: isLoading ? null : (_) => onSend(),
              decoration: InputDecoration(
                hintText: 'Pose ta question à SOMA…',
                hintStyle: TextStyle(
                    color: colors.textMuted, fontSize: 14),
                filled: true,
                fillColor: colors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                    horizontal: 14, vertical: 12),
              ),
            ),
          ),
          const SizedBox(width: 10),
          GestureDetector(
            onTap: isLoading ? null : () => onSend(),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: isLoading
                    ? _kAccentDim
                    : colors.accent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                isLoading
                    ? Icons.hourglass_empty_rounded
                    : Icons.send_rounded,
                color: isLoading ? colors.accent : Colors.black,
                size: 20,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Bannière d'erreur ─────────────────────────────────────────────────────────

class _ErrorBanner extends StatelessWidget {
  final String message;

  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: const Color(0xFF2A0A0A),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded,
              color: colors.danger, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                  color: colors.danger, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
