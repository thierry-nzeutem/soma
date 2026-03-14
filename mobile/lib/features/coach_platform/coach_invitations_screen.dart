/// Coach Invitations Management Screen.
/// Allows the coach to create, share, and manage invitations.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/coach/coach_invite_models.dart';
import '../../core/coach/coach_invite_notifier.dart';

class CoachInvitationsScreen extends ConsumerStatefulWidget {
  const CoachInvitationsScreen({super.key});

  @override
  ConsumerState<CoachInvitationsScreen> createState() =>
      _CoachInvitationsScreenState();
}

class _CoachInvitationsScreenState
    extends ConsumerState<CoachInvitationsScreen> {
  bool _creating = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final invAsync = ref.watch(invitationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Invitations'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'Nouvelle invitation',
            onPressed: _creating ? null : () => _showCreateDialog(context),
          ),
        ],
      ),
      body: invAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              Text('Erreur: $e'),
              TextButton(
                onPressed: () =>
                    ref.read(invitationsProvider.notifier).refresh(),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (state) {
          if (state.invitations.isEmpty) {
            return _buildEmpty(context);
          }
          return RefreshIndicator(
            onRefresh: () =>
                ref.read(invitationsProvider.notifier).refresh(),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: state.invitations.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (_, i) =>
                  _InvitationCard(invitation: state.invitations[i]),
            ),
          );
        },
      ),
    );
  }

  Widget _buildEmpty(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.link_rounded,
              size: 72,
              color: Theme.of(context).colorScheme.primary.withOpacity(0.4),
            ),
            const SizedBox(height: 20),
            Text(
              'Aucune invitation',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            const Text(
              'Créez une invitation et partagez le lien\navec votre athlète.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => _showCreateDialog(context),
              icon: const Icon(Icons.add),
              label: const Text('Créer une invitation'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showCreateDialog(BuildContext context) async {
    final emailCtrl = TextEditingController();
    final messageCtrl = TextEditingController();

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Nouvelle invitation'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: emailCtrl,
              decoration: const InputDecoration(
                labelText: 'Email de l\'athlète (optionnel)',
                hintText: 'athlete@email.com',
                prefixIcon: Icon(Icons.email_outlined),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: messageCtrl,
              decoration: const InputDecoration(
                labelText: 'Message d\'accompagnement',
                hintText: 'Rejoins mon espace coaching SOMA...',
                prefixIcon: Icon(Icons.message_outlined),
              ),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Créer'),
          ),
        ],
      ),
    );

    if (result != true || !mounted) return;

    setState(() => _creating = true);
    final inv = await ref.read(invitationsProvider.notifier).createInvitation(
          email: emailCtrl.text.trim().isEmpty ? null : emailCtrl.text.trim(),
          message: messageCtrl.text.trim().isEmpty
              ? null
              : messageCtrl.text.trim(),
        );
    if (!mounted) return;
    setState(() => _creating = false);

    if (inv != null) {
      _showShareSheet(context, inv);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Erreur lors de la création de l\'invitation.')),
      );
    }
  }

  void _showShareSheet(BuildContext context, CoachInvitation inv) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => _InviteShareSheet(invitation: inv),
    );
  }
}

// ── Invitation Card ──────────────────────────────────────────────────────

class _InvitationCard extends ConsumerWidget {
  final CoachInvitation invitation;
  const _InvitationCard({required this.invitation});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final statusColor = _statusColor(invitation.status, theme);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    invitation.inviteeEmail ?? 'Lien ouvert',
                    style: theme.textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _statusLabel(invitation.status),
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            if (invitation.message != null) ...[
              const SizedBox(height: 8),
              Text(
                invitation.message!,
                style: theme.textTheme.bodySmall,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.tag, size: 14, color: theme.colorScheme.primary),
                const SizedBox(width: 4),
                Text(
                  'Code: ${invitation.inviteCode}',
                  style: theme.textTheme.labelMedium?.copyWith(
                    fontFamily: 'monospace',
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Text(
                  'Expire: ${_formatDate(invitation.expiresAt)}',
                  style: theme.textTheme.labelSmall,
                ),
              ],
            ),
            if (invitation.isPending) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _copyCode(context, invitation.inviteCode),
                      icon: const Icon(Icons.copy, size: 16),
                      label: const Text('Copier le code'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _copyLink(context, invitation.inviteLink),
                      icon: const Icon(Icons.link, size: 16),
                      label: const Text('Copier le lien'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: () => _cancelInvite(context, ref),
                    icon: const Icon(Icons.close, size: 18),
                    tooltip: 'Annuler',
                    color: theme.colorScheme.error,
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _copyCode(BuildContext context, String code) {
    Clipboard.setData(ClipboardData(text: code));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Code "$code" copié !')),
    );
  }

  void _copyLink(BuildContext context, String link) {
    Clipboard.setData(ClipboardData(text: link));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Lien d\'invitation copié !')),
    );
  }

  Future<void> _cancelInvite(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Annuler l\'invitation ?'),
        content: const Text('Cette invitation ne sera plus utilisable.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Non'),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(ctx).colorScheme.error,
            ),
            child: const Text('Annuler l\'invitation'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    await ref.read(invitationsProvider.notifier).cancelInvitation(invitation.id);
  }

  Color _statusColor(String status, ThemeData theme) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'accepted':
        return Colors.green;
      case 'expired':
        return theme.colorScheme.error;
      case 'cancelled':
        return theme.colorScheme.onSurfaceVariant;
      default:
        return theme.colorScheme.primary;
    }
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'pending':
        return 'En attente';
      case 'accepted':
        return 'Acceptée';
      case 'expired':
        return 'Expirée';
      case 'cancelled':
        return 'Annulée';
      default:
        return status;
    }
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
  }
}

// ── Share Sheet ──────────────────────────────────────────────────────────

class _InviteShareSheet extends StatelessWidget {
  final CoachInvitation invitation;
  const _InviteShareSheet({required this.invitation});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Invitation créée !',
            style: theme.textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Partagez le code ou le lien avec votre athlète.',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                Text(
                  invitation.inviteCode,
                  style: theme.textTheme.displaySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    fontFamily: 'monospace',
                    letterSpacing: 6,
                    color: theme.colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Code d\'invitation',
                  style: theme.textTheme.labelSmall,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: () {
                    Clipboard.setData(
                        ClipboardData(text: invitation.inviteCode));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Code copié !')),
                    );
                  },
                  icon: const Icon(Icons.copy),
                  label: const Text('Copier le code'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    Clipboard.setData(
                        ClipboardData(text: invitation.inviteLink));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Lien copié !')),
                    );
                  },
                  icon: const Icon(Icons.link),
                  label: const Text('Copier le lien'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }
}
