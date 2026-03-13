/// CoachConversationListScreen — Historique des conversations coach (LOT 9).
///
/// Liste tous les fils de conversation de l'utilisateur.
/// Permet d'en ouvrir un pour continuer ou de créer un nouveau.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/coach.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'coach_notifier.dart';

class CoachConversationListScreen extends ConsumerWidget {
  const CoachConversationListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final state = ref.watch(coachThreadsProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Conversations',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.text),
            onPressed: () =>
                ref.read(coachThreadsProvider.notifier).refresh(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: colors.accent,
        foregroundColor: Colors.black,
        icon: const Icon(Icons.add_comment_rounded),
        label: const Text('Nouveau',
            style: TextStyle(fontWeight: FontWeight.w600)),
        onPressed: () {
          ref.read(coachChatProvider.notifier).newConversation();
          context.push('/coach');
        },
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => _ErrorView(
          onRetry: () =>
              ref.read(coachThreadsProvider.notifier).refresh(),
        ),
        data: (threads) => threads.isEmpty
            ? const _EmptyView()
            : _ThreadList(threads: threads),
      ),
    );
  }
}

// ── Liste de fils ─────────────────────────────────────────────────────────────

class _ThreadList extends StatelessWidget {
  final List<CoachThread> threads;

  const _ThreadList({required this.threads});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
      itemCount: threads.length,
      itemBuilder: (ctx, i) => _ThreadCard(thread: threads[i]),
    );
  }
}

class _ThreadCard extends StatelessWidget {
  final CoachThread thread;

  const _ThreadCard({required this.thread});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final d = thread.createdAt;
    final dateStr =
        '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

    return GestureDetector(
      onTap: () => context.push('/coach', extra: thread.id),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: colors.border),
        ),
        child: Row(
          children: [
            // Icône
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: colors.accent.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: colors.accent.withOpacity(0.3)),
              ),
              child: Icon(Icons.chat_bubble_outline_rounded,
                  color: colors.accent, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    thread.displayTitle,
                    style: TextStyle(
                      color: colors.text,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                  if (thread.summary != null && thread.summary!.isNotEmpty)
                    Text(
                      thread.summary!,
                      style: TextStyle(
                          color: colors.textSecondary, fontSize: 12),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    )
                  else
                    Text(
                      dateStr,
                      style: TextStyle(
                          color: colors.textMuted, fontSize: 12),
                    ),
                ],
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

// ── États vides / erreur ──────────────────────────────────────────────────────

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline_rounded,
                size: 56, color: colors.textMuted),
            const SizedBox(height: 16),
            Text('Aucune conversation',
                style: TextStyle(color: colors.text, fontSize: 16)),
            const SizedBox(height: 8),
            Text(
              'Commence une conversation avec SOMA Coach\npour poser tes questions santé.',
              textAlign: TextAlign.center,
              style: TextStyle(color: colors.textMuted, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final VoidCallback onRetry;

  const _ErrorView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.error_outline_rounded,
              size: 48, color: colors.textMuted),
          const SizedBox(height: 12),
          Text('Erreur de chargement',
              style: TextStyle(color: colors.text)),
          const SizedBox(height: 16),
          TextButton(
            onPressed: onRetry,
            child: Text('Réessayer',
                style: TextStyle(color: colors.accent)),
          ),
        ],
      ),
    );
  }
}
