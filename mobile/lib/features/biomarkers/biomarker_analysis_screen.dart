/// SOMA LOT 17 — Biomarker Analysis Screen.
///
/// Analyse biomarqueurs : scores santé + impact longévité + 14 marqueurs.
/// Consomme [biomarkerAnalysisProvider] (GET /api/v1/labs/analysis).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/biomarker.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import '../../shared/widgets/longevity_impact_card.dart';
import '../../shared/widgets/biomarker_marker_row.dart';
import '../../shared/widgets/confidence_badge.dart';
import 'biomarker_notifier.dart';

class BiomarkerAnalysisScreen extends ConsumerWidget {
  const BiomarkerAnalysisScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final analysisAsync = ref.watch(biomarkerAnalysisProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Biomarqueurs',
        actions: [
          IconButton(
            icon: Icon(Icons.list_alt_rounded, color: colors.accent),
            onPressed: () => Navigator.pushNamed(context, '/biomarkers/results'),
            tooltip: 'Résultats de laboratoire',
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.invalidate(biomarkerAnalysisProvider),
            tooltip: 'Actualiser',
          ),
        ],
      ),
      body: analysisAsync.when(
        loading: () =>
            Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => _ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(biomarkerAnalysisProvider),
          onAddResults: () =>
              Navigator.pushNamed(context, '/biomarkers/results'),
        ),
        data: (analysis) {
          if (analysis.markersAnalyzed == 0) {
            return _EmptyView(
              onAdd: () => Navigator.pushNamed(context, '/biomarkers/results'),
            );
          }
          return _AnalysisBody(analysis: analysis);
        },
      ),
    );
  }
}

// ── Corps analyse ─────────────────────────────────────────────────────────────

class _AnalysisBody extends StatelessWidget {
  final BiomarkerAnalysis analysis;
  const _AnalysisBody({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── En-tête : date + confiance ─────────────────────────────────────
        Row(
          children: [
            Text(
              analysis.analysisDate,
              style: TextStyle(color: colors.textMuted, fontSize: 13),
            ),
            const Spacer(),
            ConfidenceBadge(confidence: analysis.confidence),
          ],
        ),
        const SizedBox(height: 16),

        // ── Scores santé ──────────────────────────────────────────────────
        const _SectionHeader(title: 'Scores de santé'),
        const SizedBox(height: 8),
        _HealthScoresRow(analysis: analysis),
        const SizedBox(height: 20),

        // ── Impact longévité ──────────────────────────────────────────────
        const _SectionHeader(title: 'Impact longévité'),
        const SizedBox(height: 8),
        LongevityImpactCard(
          longevityModifier: analysis.longevityModifier,
          markersAnalyzed: analysis.markersAnalyzed,
          optimalMarkers: analysis.optimalMarkers,
        ),
        const SizedBox(height: 20),

        // ── Actions prioritaires ──────────────────────────────────────────
        if (analysis.priorityActions.isNotEmpty) ...[
          const _SectionHeader(title: 'Actions prioritaires'),
          const SizedBox(height: 8),
          ...analysis.priorityActions.take(3).map(
                (action) => _ActionItem(text: action),
              ),
          const SizedBox(height: 20),
        ],

        // ── Marqueurs détaillés ───────────────────────────────────────────
        _SectionHeader(
            title: 'Marqueurs (${analysis.markersAnalyzed} analysés)'),
        const SizedBox(height: 8),
        ...analysis.markerAnalyses.map(
          (marker) => BiomarkerMarkerRow(marker: marker),
        ),

        // ── Recommandations supplémentation ──────────────────────────────
        if (analysis.supplementationRecommendations.isNotEmpty) ...[
          const SizedBox(height: 20),
          const _SectionHeader(title: 'Supplémentation'),
          const SizedBox(height: 8),
          ...analysis.supplementationRecommendations.map(
            (rec) => _RecommendationItem(text: rec, icon: Icons.medication_rounded),
          ),
        ],

        // ── Recommandations alimentaires ──────────────────────────────────
        if (analysis.dietaryRecommendations.isNotEmpty) ...[
          const SizedBox(height: 20),
          const _SectionHeader(title: 'Alimentation'),
          const SizedBox(height: 8),
          ...analysis.dietaryRecommendations.map(
            (rec) => _RecommendationItem(
                text: rec, icon: Icons.restaurant_rounded),
          ),
        ],
        const SizedBox(height: 32),
      ],
    );
  }
}

// ── Scores de santé ───────────────────────────────────────────────────────────

class _HealthScoresRow extends StatelessWidget {
  final BiomarkerAnalysis analysis;
  const _HealthScoresRow({required this.analysis});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _ScoreBar(
          label: 'Santé métabolique',
          value: analysis.metabolicHealthScore,
          color: _scoreColor(context, analysis.metabolicHealthScore),
          higherIsBetter: true,
        ),
        const SizedBox(height: 8),
        _ScoreBar(
          label: 'Inflammation',
          value: analysis.inflammationScore,
          color: _scoreColor(context, 100 - analysis.inflammationScore), // inverse
          higherIsBetter: false,
          infoText: '↓ plus bas = mieux',
        ),
        const SizedBox(height: 8),
        _ScoreBar(
          label: 'Risque cardiovasculaire',
          value: analysis.cardiovascularRisk,
          color: _scoreColor(context, 100 - analysis.cardiovascularRisk), // inverse
          higherIsBetter: false,
          infoText: '↓ plus bas = mieux',
        ),
      ],
    );
  }

  Color _scoreColor(BuildContext context, double score) {
    final colors = context.somaColors;
    if (score >= 70) return colors.success;
    if (score >= 40) return colors.warning;
    return colors.danger;
  }
}

class _ScoreBar extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  final bool higherIsBetter;
  final String? infoText;
  const _ScoreBar({
    required this.label,
    required this.value,
    required this.color,
    required this.higherIsBetter,
    this.infoText,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(label,
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 13,
                      fontWeight: FontWeight.w500)),
              const Spacer(),
              Text(
                '${value.toStringAsFixed(0)}/100',
                style: TextStyle(
                    color: color,
                    fontSize: 14,
                    fontWeight: FontWeight.bold),
              ),
              if (infoText != null) ...[
                const SizedBox(width: 6),
                Text(infoText!,
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 10)),
              ],
            ],
          ),
          const SizedBox(height: 6),
          LinearProgressIndicator(
            value: value / 100,
            backgroundColor: colors.textMuted,
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
            borderRadius: BorderRadius.circular(3),
          ),
        ],
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Text(title,
        style: TextStyle(
            color: colors.text, fontWeight: FontWeight.w600, fontSize: 16));
  }
}

class _ActionItem extends StatelessWidget {
  final String text;
  const _ActionItem({required this.text});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.arrow_right_rounded,
              color: colors.accent, size: 20),
          const SizedBox(width: 4),
          Expanded(
            child: Text(text,
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _RecommendationItem extends StatelessWidget {
  final String text;
  final IconData icon;
  const _RecommendationItem({required this.text, required this.icon});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: colors.info, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text,
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

// ── Vue vide ──────────────────────────────────────────────────────────────────

class _EmptyView extends StatelessWidget {
  final VoidCallback onAdd;
  const _EmptyView({required this.onAdd});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.science_rounded,
                color: colors.textMuted, size: 64),
            const SizedBox(height: 16),
            Text('Aucun résultat de laboratoire',
                style: TextStyle(color: colors.text, fontSize: 18)),
            const SizedBox(height: 8),
            Text(
              'Ajoutez vos résultats de bilan sanguin pour obtenir une analyse personnalisée.',
              textAlign: TextAlign.center,
              style: TextStyle(color: colors.textMuted, fontSize: 14),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
                minimumSize: const Size(200, 48),
              ),
              onPressed: onAdd,
              icon: const Icon(Icons.add),
              label: const Text('Ajouter des résultats'),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Vue erreur ────────────────────────────────────────────────────────────────

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  final VoidCallback onAddResults;
  const _ErrorView(
      {required this.message,
      required this.onRetry,
      required this.onAddResults});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline,
                color: colors.danger, size: 48),
            const SizedBox(height: 12),
            Text('Données insuffisantes pour l\'analyse',
                style: TextStyle(color: colors.text, fontSize: 16)),
            const SizedBox(height: 8),
            Text(message,
                style:
                    TextStyle(color: colors.textMuted, fontSize: 12),
                textAlign: TextAlign.center),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                      side: BorderSide(color: colors.textMuted)),
                  onPressed: onRetry,
                  child: Text('Réessayer',
                      style: TextStyle(color: colors.text)),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                      backgroundColor: colors.accent,
                      foregroundColor: Colors.black),
                  onPressed: onAddResults,
                  child: const Text('Ajouter des résultats'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
