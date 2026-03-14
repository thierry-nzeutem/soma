/// Full Athlete Profile Screen (coach view).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/coach/coach_invite_models.dart';
import '../../core/coach/coach_invite_notifier.dart';

class AthleteFullProfileScreen extends ConsumerWidget {
  final String athleteId;
  final String athleteName;

  const AthleteFullProfileScreen({
    super.key,
    required this.athleteId,
    required this.athleteName,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final profileAsync = ref.watch(athleteFullProfileProvider(athleteId));
    final recsAsync = ref.watch(athleteRecommendationsProvider(athleteId));

    return Scaffold(
      appBar: AppBar(
        title: Text(athleteName),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) => _onMenuAction(context, ref, value),
            itemBuilder: (_) => [
              const PopupMenuItem(
                value: 'pause',
                child: Row(
                  children: [
                    Icon(Icons.pause_circle_outline),
                    SizedBox(width: 8),
                    Text('Mettre en pause'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'archive',
                child: Row(
                  children: [
                    Icon(Icons.archive_outlined),
                    SizedBox(width: 8),
                    Text('Archiver'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Erreur: $e')),
        data: (profile) {
          if (profile == null) {
            return const Center(child: Text('Profil non trouvé'));
          }
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Identity Card ──────────────────────────────────────
                _SectionCard(
                  title: 'Identité',
                  icon: Icons.person_outline,
                  children: [
                    _InfoRow('Nom', profile.displayName),
                    if (profile.displayAge.isNotEmpty)
                      _InfoRow('Âge', profile.displayAge),
                    if (profile.sex != null)
                      _InfoRow('Sexe', _sexLabel(profile.sex!)),
                    if (profile.heightCm != null)
                      _InfoRow('Taille', '${profile.heightCm!.toStringAsFixed(0)} cm'),
                    if (profile.sport != null)
                      _InfoRow('Sport', profile.sport!),
                    if (profile.goal != null)
                      _InfoRow('Objectif', profile.goal!),
                  ],
                ),
                const SizedBox(height: 16),

                // ── Level Card ─────────────────────────────────────────
                if (profile.activityLevel != null ||
                    profile.fitnessLevel != null)
                  _SectionCard(
                    title: 'Niveau',
                    icon: Icons.fitness_center_outlined,
                    children: [
                      if (profile.activityLevel != null)
                        _InfoRow('Activité', _activityLabel(profile.activityLevel!)),
                      if (profile.fitnessLevel != null)
                        _InfoRow('Forme', _fitnessLabel(profile.fitnessLevel!)),
                    ],
                  ),
                const SizedBox(height: 16),

                // ── Relationship Status Card ────────────────────────────
                _SectionCard(
                  title: 'Relation coaching',
                  icon: Icons.handshake_outlined,
                  children: [
                    _InfoRow(
                      'Statut',
                      _linkStatusLabel(profile.linkStatus),
                      valueColor: _linkStatusColor(profile.linkStatus, theme),
                    ),
                    if (profile.linkedAt != null)
                      _InfoRow('Depuis', _formatDate(profile.linkedAt!)),
                    if (profile.relationshipNotes != null &&
                        profile.relationshipNotes!.isNotEmpty)
                      _InfoRow('Notes relation', profile.relationshipNotes!),
                  ],
                ),
                const SizedBox(height: 16),

                // ── Quick Stats ────────────────────────────────────────
                Row(
                  children: [
                    Expanded(
                      child: _StatChip(
                        icon: Icons.sticky_note_2_outlined,
                        label: '${profile.recentNotesCount}',
                        sublabel: 'notes',
                        color: theme.colorScheme.secondary,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _StatChip(
                        icon: Icons.checklist_rounded,
                        label: '${profile.pendingRecommendationsCount}',
                        sublabel: 'recommandations en cours',
                        color: profile.pendingRecommendationsCount > 0
                            ? Colors.orange
                            : theme.colorScheme.primary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // ── Recommendations ────────────────────────────────────
                Text(
                  'Recommandations',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                recsAsync.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (e, _) => Text('Erreur: $e'),
                  data: (recs) {
                    if (recs.isEmpty) {
                      return Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Center(
                          child: Text('Aucune recommandation pour l\'instant.'),
                        ),
                      );
                    }
                    return Column(
                      children: recs
                          .map((r) => _RecommendationCard(rec: r))
                          .toList(),
                    );
                  },
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Future<void> _onMenuAction(
      BuildContext context, WidgetRef ref, String value) async {
    // Status update - simplified for Phase 1
    final targetStatus = value == 'pause' ? 'paused' : 'archived';
    final label = value == 'pause' ? 'pause' : 'archivage';

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Confirmer la mise en $label ?'),
        content: Text(
            'Mettre la relation avec $athleteName en ${targetStatus == 'paused' ? 'pause' : 'archive'} ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );

    if (ok != true || !context.mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Statut mis à jour: $targetStatus')),
    );
  }

  String _sexLabel(String sex) {
    switch (sex) {
      case 'male': return 'Homme';
      case 'female': return 'Femme';
      default: return sex;
    }
  }

  String _activityLabel(String level) {
    switch (level) {
      case 'sedentary': return 'Sédentaire';
      case 'light': return 'Légèrement actif';
      case 'moderate': return 'Modérément actif';
      case 'active': return 'Actif';
      case 'very_active': return 'Très actif';
      default: return level;
    }
  }

  String _fitnessLabel(String level) {
    switch (level) {
      case 'beginner': return 'Débutant';
      case 'intermediate': return 'Intermédiaire';
      case 'advanced': return 'Avancé';
      case 'athlete': return 'Athlète';
      default: return level;
    }
  }

  String _linkStatusLabel(String status) {
    switch (status) {
      case 'active': return 'Actif';
      case 'paused': return 'En pause';
      case 'archived': return 'Archivé';
      case 'revoked': return 'Révoqué';
      default: return status;
    }
  }

  Color _linkStatusColor(String status, ThemeData theme) {
    switch (status) {
      case 'active': return Colors.green;
      case 'paused': return Colors.orange;
      case 'archived': return theme.colorScheme.onSurfaceVariant;
      case 'revoked': return theme.colorScheme.error;
      default: return theme.colorScheme.primary;
    }
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
  }
}

// ── Recommendation Card ──────────────────────────────────────────────────

class _RecommendationCard extends StatelessWidget {
  final CoachRecommendation rec;
  const _RecommendationCard({required this.rec});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: _priorityColor(rec.priority).withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _typeIcon(rec.recType),
                size: 20,
                color: _priorityColor(rec.priority),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    rec.title,
                    style: theme.textTheme.labelLarge
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    rec.description,
                    style: theme.textTheme.bodySmall,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            _StatusBadge(status: rec.status),
          ],
        ),
      ),
    );
  }

  Color _priorityColor(String priority) {
    switch (priority) {
      case 'urgent': return Colors.red;
      case 'high': return Colors.orange;
      case 'normal': return Colors.blue;
      case 'low': return Colors.grey;
      default: return Colors.blue;
    }
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'training': return Icons.fitness_center_rounded;
      case 'nutrition': return Icons.restaurant_rounded;
      case 'recovery': return Icons.bedtime_rounded;
      case 'medical': return Icons.medical_services_rounded;
      case 'lifestyle': return Icons.self_improvement_rounded;
      case 'mental': return Icons.psychology_rounded;
      default: return Icons.star_rounded;
    }
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Color c;
    String label;
    switch (status) {
      case 'pending':
        c = Colors.orange;
        label = 'À faire';
        break;
      case 'in_progress':
        c = Colors.blue;
        label = 'En cours';
        break;
      case 'completed':
        c = Colors.green;
        label = 'Fait';
        break;
      case 'dismissed':
        c = theme.colorScheme.onSurfaceVariant;
        label = 'Ignoré';
        break;
      default:
        c = theme.colorScheme.primary;
        label = status;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(color: c, fontSize: 11, fontWeight: FontWeight.w600),
      ),
    );
  }
}

// ── Helper Widgets ────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<Widget> children;

  const _SectionCard({
    required this.title,
    required this.icon,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 18, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;

  const _InfoRow(this.label, this.value, {this.valueColor});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w500,
                color: valueColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final String sublabel;
  final Color color;

  const _StatChip({
    required this.icon,
    required this.label,
    required this.sublabel,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 4),
          Text(
            label,
            style: theme.textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.bold, color: color),
          ),
          Text(
            sublabel,
            style: theme.textTheme.labelSmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
