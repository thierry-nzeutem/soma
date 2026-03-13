/// SOMA LOT 17 — Biomarker Results Screen.
///
/// Liste des résultats de laboratoire + FAB pour ajouter un nouveau résultat.
/// Consomme GET /api/v1/labs/results et POST /api/v1/labs/result.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart' show AsyncNotifierProvider;

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/biomarker.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'biomarker_notifier.dart';

// ── Provider liste des résultats lab ─────────────────────────────────────────

final labResultsProvider =
    AsyncNotifierProvider<LabResultsNotifier, List<LabResultItem>>(
  LabResultsNotifier.new,
);

class LabResultItem {
  final String id;
  final String markerName;
  final double value;
  final String unit;
  final String labDate;
  final String source;
  final double confidence;

  const LabResultItem({
    required this.id,
    required this.markerName,
    required this.value,
    required this.unit,
    required this.labDate,
    required this.source,
    required this.confidence,
  });

  factory LabResultItem.fromJson(Map<String, dynamic> json) {
    return LabResultItem(
      id: json['id'] as String? ?? '',
      markerName: json['marker_name'] as String? ?? '',
      value: (json['value'] as num?)?.toDouble() ?? 0.0,
      unit: json['unit'] as String? ?? '',
      labDate: json['lab_date'] as String? ?? '',
      source: json['source'] as String? ?? 'manual',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
    );
  }

  String get displayName => switch (markerName) {
        'vitamin_d' => 'Vitamine D',
        'ferritin' => 'Ferritine',
        'crp' => 'CRP',
        'testosterone_total' => 'Testostérone',
        'hba1c' => 'HbA1c',
        'fasting_glucose' => 'Glycémie jeûne',
        'cholesterol_total' => 'Cholestérol total',
        'hdl' => 'HDL',
        'ldl' => 'LDL',
        'triglycerides' => 'Triglycérides',
        'cortisol' => 'Cortisol',
        'homocysteine' => 'Homocystéine',
        'magnesium' => 'Magnésium',
        'omega3_index' => 'Index Oméga-3',
        _ => markerName,
      };
}

class LabResultsNotifier extends AsyncNotifier<List<LabResultItem>> {
  @override
  Future<List<LabResultItem>> build() => _fetchResults();

  Future<List<LabResultItem>> _fetchResults() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<List<dynamic>>(
      ApiConstants.labsResult,
    );
    final data = response.data ?? [];
    return data
        .cast<Map<String, dynamic>>()
        .map(LabResultItem.fromJson)
        .toList();
  }

  Future<void> addResult(LabResultCreate create) async {
    final client = ref.read(apiClientProvider);
    await client.post(ApiConstants.labsResult, data: create.toJson());
    // Refresh analysis + results
    ref.invalidate(biomarkerAnalysisProvider);
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchResults);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchResults);
  }
}

// ── Écran principal ───────────────────────────────────────────────────────────

class BiomarkerResultsScreen extends ConsumerWidget {
  const BiomarkerResultsScreen({super.key});

  // 14 marqueurs supportés (marker_name, unité par défaut)
  static const _supportedMarkers = [
    ('vitamin_d', 'ng/mL'),
    ('ferritin', 'ng/mL'),
    ('crp', 'mg/L'),
    ('testosterone_total', 'ng/dL'),
    ('hba1c', '%'),
    ('fasting_glucose', 'mg/dL'),
    ('cholesterol_total', 'mg/dL'),
    ('hdl', 'mg/dL'),
    ('ldl', 'mg/dL'),
    ('triglycerides', 'mg/dL'),
    ('cortisol', 'µg/dL'),
    ('homocysteine', 'µmol/L'),
    ('magnesium', 'mg/dL'),
    ('omega3_index', '%'),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final resultsAsync = ref.watch(labResultsProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Résultats de laboratoire',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () =>
                ref.read(labResultsProvider.notifier).refresh(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: colors.accent,
        foregroundColor: Colors.black,
        onPressed: () => _showAddResultBottomSheet(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('Ajouter un résultat'),
      ),
      body: resultsAsync.when(
        loading: () =>
            Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline,
                  color: colors.danger, size: 48),
              const SizedBox(height: 12),
              Text(e.toString(),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: colors.textMuted)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () =>
                    ref.read(labResultsProvider.notifier).refresh(),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (results) {
          if (results.isEmpty) {
            return _EmptyResults(
                onAdd: () => _showAddResultBottomSheet(context, ref));
          }
          return RefreshIndicator(
            color: colors.accent,
            backgroundColor: colors.surface,
            onRefresh: () =>
                ref.read(labResultsProvider.notifier).refresh(),
            child: _ResultsList(results: results),
          );
        },
      ),
    );
  }

  void _showAddResultBottomSheet(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: colors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _AddResultSheet(
        markers: _supportedMarkers,
        onSubmit: (create) =>
            ref.read(labResultsProvider.notifier).addResult(create),
      ),
    );
  }
}

// ── Liste des résultats ───────────────────────────────────────────────────────

class _ResultsList extends StatelessWidget {
  final List<LabResultItem> results;
  const _ResultsList({required this.results});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    // Group by date
    final byDate = <String, List<LabResultItem>>{};
    for (final r in results) {
      byDate.putIfAbsent(r.labDate, () => []).add(r);
    }
    final dates = byDate.keys.toList()..sort((a, b) => b.compareTo(a));

    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 96, top: 12),
      itemCount: dates.length,
      itemBuilder: (_, i) {
        final date = dates[i];
        final items = byDate[date]!;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(date,
                  style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 12,
                      fontWeight: FontWeight.w600)),
            ),
            ...items.map((r) => _ResultTile(result: r)),
          ],
        );
      },
    );
  }
}

class _ResultTile extends StatelessWidget {
  final LabResultItem result;
  const _ResultTile({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(result.displayName,
                    style: TextStyle(
                        color: colors.text, fontWeight: FontWeight.w500)),
                Text(result.markerName,
                    style: TextStyle(
                        color: colors.textMuted, fontSize: 11)),
              ],
            ),
          ),
          Text(
            '${result.value.toStringAsFixed(1)} ${result.unit}',
            style: TextStyle(
                color: colors.accent,
                fontWeight: FontWeight.bold,
                fontSize: 15),
          ),
        ],
      ),
    );
  }
}

// ── Bottom sheet ajout résultat ───────────────────────────────────────────────

class _AddResultSheet extends StatefulWidget {
  final List<(String, String)> markers;
  final void Function(LabResultCreate) onSubmit;

  const _AddResultSheet({required this.markers, required this.onSubmit});

  @override
  State<_AddResultSheet> createState() => _AddResultSheetState();
}

class _AddResultSheetState extends State<_AddResultSheet> {
  late String _selectedMarker;
  late String _selectedUnit;
  final _valueController = TextEditingController();
  final _dateController = TextEditingController();
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _selectedMarker = widget.markers.first.$1;
    _selectedUnit = widget.markers.first.$2;
    // Default to today
    final now = DateTime.now();
    _dateController.text =
        '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _valueController.dispose();
    _dateController.dispose();
    super.dispose();
  }

  String _markerDisplayName(String markerName) => switch (markerName) {
        'vitamin_d' => 'Vitamine D',
        'ferritin' => 'Ferritine',
        'crp' => 'CRP',
        'testosterone_total' => 'Testostérone totale',
        'hba1c' => 'HbA1c',
        'fasting_glucose' => 'Glycémie à jeun',
        'cholesterol_total' => 'Cholestérol total',
        'hdl' => 'HDL',
        'ldl' => 'LDL',
        'triglycerides' => 'Triglycérides',
        'cortisol' => 'Cortisol',
        'homocysteine' => 'Homocystéine',
        'magnesium' => 'Magnésium',
        'omega3_index' => 'Index Oméga-3',
        _ => markerName,
      };

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        left: 16,
        right: 16,
        top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle bar
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: colors.textMuted,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text('Ajouter un résultat',
              style: TextStyle(
                  color: colors.text,
                  fontSize: 18,
                  fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),

          // Marqueur
          DropdownButtonFormField<String>(
            value: _selectedMarker,
            dropdownColor: colors.border,
            decoration: InputDecoration(
              labelText: 'Marqueur',
              labelStyle: TextStyle(color: colors.textMuted),
              enabledBorder: OutlineInputBorder(
                borderSide: BorderSide(color: colors.textMuted),
              ),
              focusedBorder: OutlineInputBorder(
                borderSide: BorderSide(color: colors.accent),
              ),
            ),
            style: TextStyle(color: colors.text),
            items: widget.markers
                .map((m) => DropdownMenuItem(
                      value: m.$1,
                      child: Text(_markerDisplayName(m.$1)),
                    ))
                .toList(),
            onChanged: (v) {
              if (v == null) return;
              setState(() {
                _selectedMarker = v;
                _selectedUnit = widget.markers
                    .firstWhere((m) => m.$1 == v)
                    .$2;
              });
            },
          ),
          const SizedBox(height: 12),

          // Valeur + unité
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextField(
                  controller: _valueController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  style: TextStyle(color: colors.text),
                  decoration: InputDecoration(
                    labelText: 'Valeur',
                    labelStyle: TextStyle(color: colors.textMuted),
                    enabledBorder: OutlineInputBorder(
                      borderSide: BorderSide(color: colors.textMuted),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(color: colors.accent),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      vertical: 16, horizontal: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: colors.textMuted),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(_selectedUnit,
                      style: TextStyle(color: colors.text)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Date
          TextField(
            controller: _dateController,
            style: TextStyle(color: colors.text),
            decoration: InputDecoration(
              labelText: 'Date (YYYY-MM-DD)',
              labelStyle: TextStyle(color: colors.textMuted),
              enabledBorder: OutlineInputBorder(
                borderSide: BorderSide(color: colors.textMuted),
              ),
              focusedBorder: OutlineInputBorder(
                borderSide: BorderSide(color: colors.accent),
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Bouton soumettre
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
              ),
              onPressed: _submitting
                  ? null
                  : () {
                      final value = double.tryParse(
                          _valueController.text.replaceAll(',', '.'));
                      if (value == null ||
                          _dateController.text.isEmpty) {
                        return;
                      }
                      setState(() => _submitting = true);
                      widget.onSubmit(
                        LabResultCreate(
                          markerName: _selectedMarker,
                          value: value,
                          unit: _selectedUnit,
                          labDate: _dateController.text,
                        ),
                      );
                      Navigator.pop(context);
                    },
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          color: Colors.black, strokeWidth: 2),
                    )
                  : const Text('Enregistrer',
                      style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

// ── Vue vide ──────────────────────────────────────────────────────────────────

class _EmptyResults extends StatelessWidget {
  final VoidCallback onAdd;
  const _EmptyResults({required this.onAdd});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.biotech_rounded,
                color: colors.textMuted, size: 64),
            const SizedBox(height: 16),
            Text('Aucun résultat enregistré',
                style: TextStyle(color: colors.text, fontSize: 18)),
            const SizedBox(height: 8),
            Text(
              'Saisissez les valeurs de votre dernier bilan sanguin pour commencer.',
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
              label: const Text('Saisir un résultat'),
            ),
          ],
        ),
      ),
    );
  }
}
