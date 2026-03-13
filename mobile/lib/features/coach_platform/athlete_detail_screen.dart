/// SOMA LOT 17 — Athlete Detail Screen.
///
/// Dashboard individuel d'un athlète : scores + alertes + programmes + notes.
/// Reçoit l'athleteId depuis la route /coach-platform/athlete/:id.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/coach_platform.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import '../../shared/widgets/risk_level_badge.dart';
import '../../shared/widgets/athlete_alert_card.dart';
import 'coach_platform_notifier.dart';

class AthleteDetailScreen extends ConsumerWidget {
  final String athleteId;

  const AthleteDetailScreen({super.key, required this.athleteId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    // Find the summary from the dashboard overview
    final dashboardAsync = ref.watch(coachDashboardProvider);
    final alertsAsync = ref.watch(athleteAlertsProvider(athleteId));
    final notesAsync = ref.watch(athleteNotesProvider(athleteId));

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Athlète',
        actions: [
          IconButton(
            icon: Icon(Icons.note_add_rounded, color: colors.accent),
            onPressed: () => _showAddNoteDialog(context, ref),
            tooltip: 'Ajouter une note',
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () {
              ref.invalidate(athleteAlertsProvider(athleteId));
              ref.invalidate(athleteNotesProvider(athleteId));
            },
          ),
        ],
      ),
      body: dashboardAsync.when(
        loading: () => Center(
            child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (overview) {
          final summary = overview?.athletesSummary
              .where((a) => a.athleteId == athleteId)
              .firstOrNull;
          return _AthleteDetailBody(
            summary: summary,
            alertsAsync: alertsAsync,
            notesAsync: notesAsync,
            athleteId: athleteId,
          );
        },
      ),
    );
  }

  void _showAddNoteDialog(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final contentController = TextEditingController();
    String selectedCategory = 'general';
    const categories = [
      'general',
      'nutrition',
      'recovery',
      'performance',
      'injury',
      'mental'
    ];
    const categoryLabels = [
      'Général',
      'Nutrition',
      'Récupération',
      'Performance',
      'Blessure',
      'Mental'
    ];

    showDialog<void>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          backgroundColor: colors.surface,
          title: Text('Ajouter une note',
              style: TextStyle(color: colors.text)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<String>(
                value: selectedCategory,
                dropdownColor: colors.border,
                decoration: InputDecoration(
                  labelText: 'Catégorie',
                  labelStyle: TextStyle(color: colors.textMuted),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: colors.textMuted),
                  ),
                ),
                style: TextStyle(color: colors.text),
                items: List.generate(
                  categories.length,
                  (i) => DropdownMenuItem(
                    value: categories[i],
                    child: Text(categoryLabels[i]),
                  ),
                ),
                onChanged: (v) =>
                    setState(() => selectedCategory = v ?? 'general'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: contentController,
                style: TextStyle(color: colors.text),
                maxLines: 4,
                decoration: InputDecoration(
                  labelText: 'Contenu',
                  labelStyle: TextStyle(color: colors.textMuted),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: colors.textMuted),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: colors.accent),
                  ),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Annuler',
                  style: TextStyle(color: Colors.white54)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
              ),
              onPressed: () {
                if (contentController.text.trim().isEmpty) return;
                Navigator.pop(context);
                ref.read(athleteNotesProvider(athleteId).notifier).addNote(
                      AthleteNoteCreate(
                        athleteId: athleteId,
                        content: contentController.text.trim(),
                        category: selectedCategory,
                      ),
                    );
              },
              child: const Text('Enregistrer'),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Corps détail athlète ──────────────────────────────────────────────────────

class _AthleteDetailBody extends StatelessWidget {
  final AthleteDashboardSummary? summary;
  final AsyncValue<List<AthleteAlert>> alertsAsync;
  final AsyncValue<List<AthleteNote>> notesAsync;
  final String athleteId;

  const _AthleteDetailBody({
    required this.summary,
    required this.alertsAsync,
    required this.notesAsync,
    required this.athleteId,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── En-tête athlète ────────────────────────────────────────────────
        if (summary != null) _AthleteHeader(summary: summary!),
        const SizedBox(height: 20),

        // ── Scores ────────────────────────────────────────────────────────
        if (summary != null) ...[
          const _SectionTitle(text: 'Scores'),
          const SizedBox(height: 8),
          _ScoresGrid(summary: summary!),
          const SizedBox(height: 20),
        ],

        // ── Alertes ────────────────────────────────────────────────────────
        const _SectionTitle(text: 'Alertes'),
        const SizedBox(height: 8),
        alertsAsync.when(
          loading: () => Center(
              child: CircularProgressIndicator(color: colors.accent)),
          error: (e, _) =>
              Text(e.toString(), style: const TextStyle(color: Colors.red)),
          data: (alerts) {
            if (alerts.isEmpty) {
              return const _EmptySection(message: 'Aucune alerte active');
            }
            return Column(
              children: alerts
                  .map((a) => AthleteAlertCard(
                        athleteName: a.alertType,
                        severity: a.severity,
                        message: a.message,
                      ))
                  .toList(),
            );
          },
        ),
        const SizedBox(height: 20),

        // ── Notes ──────────────────────────────────────────────────────────
        const _SectionTitle(text: 'Notes coach'),
        const SizedBox(height: 8),
        notesAsync.when(
          loading: () => Center(
              child: CircularProgressIndicator(color: colors.accent)),
          error: (e, _) =>
              Text(e.toString(), style: const TextStyle(color: Colors.red)),
          data: (notes) {
            if (notes.isEmpty) {
              return const _EmptySection(message: 'Aucune note');
            }
            return Column(
              children: notes.map((n) => _NoteCard(note: n)).toList(),
            );
          },
        ),
        const SizedBox(height: 32),
      ],
    );
  }
}

// ── Header athlète ────────────────────────────────────────────────────────────

class _AthleteHeader extends StatelessWidget {
  final AthleteDashboardSummary summary;
  const _AthleteHeader({required this.summary});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: colors.border,
            child: Text(
              summary.athleteName.isNotEmpty
                  ? summary.athleteName[0].toUpperCase()
                  : '?',
              style: TextStyle(
                  color: colors.text,
                  fontSize: 20,
                  fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(summary.athleteName,
                    style: TextStyle(
                        color: colors.text,
                        fontSize: 18,
                        fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(summary.snapshotDate,
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 12)),
              ],
            ),
          ),
          RiskLevelBadge(riskLevel: summary.riskLevel),
        ],
      ),
    );
  }
}

// ── Grille scores ─────────────────────────────────────────────────────────────

class _ScoresGrid extends StatelessWidget {
  final AthleteDashboardSummary summary;
  const _ScoresGrid({required this.summary});

  @override
  Widget build(BuildContext context) {
    final scores = <(String, double?, String)>[
      ('Récupération', summary.readinessScore, '/100'),
      ('Fatigue', summary.fatigueScore, '/100'),
      ('Risque blessure', summary.injuryRiskScore, '/100'),
      ('Santé mouvements', summary.movementHealthScore, '/100'),
      ('Sommeil', summary.sleepQuality, '/5'),
      ('ACWR', summary.acwr, ''),
    ];
    final available = scores.where((s) => s.$2 != null).toList();

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
        childAspectRatio: 2.2,
      ),
      itemCount: available.length,
      itemBuilder: (_, i) {
        final score = available[i];
        return _ScoreChip(
            label: score.$1,
            value: score.$2!.toStringAsFixed(1),
            unit: score.$3);
      },
    );
  }
}

class _ScoreChip extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  const _ScoreChip(
      {required this.label, required this.value, required this.unit});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.border,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '$value$unit',
            style: TextStyle(
                color: colors.accent,
                fontSize: 16,
                fontWeight: FontWeight.bold),
          ),
          Text(
            label,
            style: TextStyle(color: colors.textMuted, fontSize: 11),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

// ── Carte note ────────────────────────────────────────────────────────────────

class _NoteCard extends StatelessWidget {
  final AthleteNote note;
  const _NoteCard({required this.note});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border(
          left: BorderSide(color: colors.accent, width: 3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(note.categoryLabel,
                  style: TextStyle(
                      color: colors.accent,
                      fontSize: 11,
                      fontWeight: FontWeight.w600)),
              const Spacer(),
              Text(note.noteDate,
                  style: TextStyle(
                      color: colors.textMuted, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 6),
          Text(note.content,
              style: TextStyle(color: colors.text, fontSize: 14)),
        ],
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle({required this.text});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Text(text,
        style: TextStyle(
            color: colors.text,
            fontWeight: FontWeight.w600,
            fontSize: 16));
  }
}

class _EmptySection extends StatelessWidget {
  final String message;
  const _EmptySection({required this.message});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Center(
        child: Text(message,
            style: TextStyle(color: colors.textMuted, fontSize: 14)),
      ),
    );
  }
}
