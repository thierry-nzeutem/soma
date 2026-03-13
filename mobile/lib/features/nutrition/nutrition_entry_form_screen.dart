/// Ecran saisie repas — formulaire macros + recherche aliment + photo (LOT 6).
///
/// Deux modes : saisie manuelle (macros libres) ou aliment de la base (search).
/// Bouton photo -> PhotoReviewScreen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'nutrition_notifier.dart';

class NutritionEntryFormScreen extends ConsumerStatefulWidget {
  const NutritionEntryFormScreen({super.key});

  @override
  ConsumerState<NutritionEntryFormScreen> createState() =>
      _NutritionEntryFormScreenState();
}

class _NutritionEntryFormScreenState
    extends ConsumerState<NutritionEntryFormScreen> {
  String _mealType = 'lunch';
  final _mealNameCtrl = TextEditingController();
  final _calCtrl = TextEditingController();
  final _protCtrl = TextEditingController();
  final _carbCtrl = TextEditingController();
  final _fatCtrl = TextEditingController();
  final _qtyCtrl = TextEditingController();
  bool _isSaving = false;

  static const _mealTypes = [
    ('breakfast', 'Petit-dejeuner'),
    ('lunch', 'Dejeuner'),
    ('dinner', 'Diner'),
    ('snack', 'En-cas'),
  ];

  @override
  void dispose() {
    _mealNameCtrl.dispose();
    _calCtrl.dispose();
    _protCtrl.dispose();
    _carbCtrl.dispose();
    _fatCtrl.dispose();
    _qtyCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Ajouter un repas'),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // -- Type de repas --
          const _Label('Type de repas'),
          _MealTypeSelector(
            selected: _mealType,
            onChanged: (v) => setState(() => _mealType = v),
          ),
          const SizedBox(height: 16),

          // -- Nom --
          const _Label('Nom du plat (optionnel)'),
          _Field(controller: _mealNameCtrl, hint: 'ex. Omelette 3 oeufs'),
          const SizedBox(height: 16),

          // -- Macros --
          const _Label('Valeurs nutritionnelles'),
          Row(
            children: [
              Expanded(
                  child: _MacroField(
                      ctrl: _calCtrl, label: 'Calories', unit: 'kcal')),
              const SizedBox(width: 8),
              Expanded(
                  child: _MacroField(
                      ctrl: _qtyCtrl, label: 'Quantite', unit: 'g')),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                  child: _MacroField(
                      ctrl: _protCtrl, label: 'Proteines', unit: 'g')),
              const SizedBox(width: 8),
              Expanded(
                  child: _MacroField(
                      ctrl: _carbCtrl, label: 'Glucides', unit: 'g')),
              const SizedBox(width: 8),
              Expanded(
                  child: _MacroField(
                      ctrl: _fatCtrl, label: 'Lipides', unit: 'g')),
            ],
          ),
          const SizedBox(height: 24),

          // -- Recherche aliment --
          OutlinedButton.icon(
            icon: const Icon(Icons.search_rounded),
            label: const Text('Rechercher un aliment'),
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0xFFFFB347),
              side: const BorderSide(color: Color(0xFFFFB347)),
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => context.push('/journal/nutrition/search'),
          ),
          const SizedBox(height: 10),

          // -- Photo --
          OutlinedButton.icon(
            icon: const Icon(Icons.photo_camera_rounded),
            label: const Text('Analyser une photo'),
            style: OutlinedButton.styleFrom(
              foregroundColor: colors.info,
              side: BorderSide(color: colors.info),
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: _pickAndAnalyzePhoto,
          ),
          const SizedBox(height: 32),

          // -- Enregistrer --
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _canSave && !_isSaving ? _save : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFF6B6B),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
              child: _isSaving
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Enregistrer',
                      style: TextStyle(fontSize: 15)),
            ),
          ),
        ],
      ),
    );
  }

  bool get _canSave => _calCtrl.text.isNotEmpty || _mealNameCtrl.text.isNotEmpty;

  Future<void> _pickAndAnalyzePhoto() async {
    final picker = ImagePicker();
    final image = await picker.pickImage(source: ImageSource.camera);
    if (image != null && mounted) {
      // Lance l'analyse en amont puis navigue vers l'ecran de review
      ref.read(photoAnalysisProvider.notifier).analyzePhoto(image.path);
      context.push('/journal/nutrition/photo');
    }
  }

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      final payload = <String, dynamic>{
        'meal_type': _mealType,
        if (_mealNameCtrl.text.trim().isNotEmpty)
          'meal_name': _mealNameCtrl.text.trim(),
        if (_calCtrl.text.isNotEmpty)
          'calories': double.tryParse(_calCtrl.text),
        if (_protCtrl.text.isNotEmpty)
          'protein_g': double.tryParse(_protCtrl.text),
        if (_carbCtrl.text.isNotEmpty)
          'carbs_g': double.tryParse(_carbCtrl.text),
        if (_fatCtrl.text.isNotEmpty)
          'fat_g': double.tryParse(_fatCtrl.text),
        if (_qtyCtrl.text.isNotEmpty)
          'quantity_g': double.tryParse(_qtyCtrl.text),
        'data_quality': 'manual',
        'logged_at': DateTime.now().toIso8601String(),
      };
      await ref.read(nutritionSummaryProvider.notifier).addEntry(payload);
      if (mounted) {
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: const Color(0xFFFF6B6B),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }
}

// -- Widgets -------------------------------------------------------------------

class _Label extends StatelessWidget {
  final String text;

  const _Label(this.text);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: TextStyle(
          color: colors.textMuted,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final TextInputType? keyboardType;

  const _Field({
    required this.controller,
    required this.hint,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      style: TextStyle(color: colors.text, fontSize: 14),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(color: colors.textMuted),
        filled: true,
        fillColor: colors.surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFFF6B6B)),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
    );
  }
}

class _MacroField extends StatelessWidget {
  final TextEditingController ctrl;
  final String label;
  final String unit;

  const _MacroField({
    required this.ctrl,
    required this.label,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$label ($unit)',
          style: TextStyle(color: colors.textSecondary, fontSize: 11),
        ),
        const SizedBox(height: 4),
        TextField(
          controller: ctrl,
          keyboardType:
              const TextInputType.numberWithOptions(decimal: true),
          style: TextStyle(color: colors.text, fontSize: 14),
          decoration: InputDecoration(
            hintText: '0',
            hintStyle: TextStyle(color: colors.textMuted),
            filled: true,
            fillColor: colors.surface,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFFFF6B6B)),
            ),
            contentPadding: const EdgeInsets.symmetric(
                horizontal: 10, vertical: 10),
          ),
        ),
      ],
    );
  }
}

class _MealTypeSelector extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;

  const _MealTypeSelector(
      {required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return Wrap(
      spacing: 8,
      children: [
        ('breakfast', 'Petit-dej'),
        ('lunch', 'Dejeuner'),
        ('dinner', 'Diner'),
        ('snack', 'En-cas'),
      ].map((t) {
        final isSelected = t.$1 == selected;
        return GestureDetector(
          onTap: () => onChanged(t.$1),
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: isSelected
                  ? const Color(0xFFFF6B6B).withOpacity(0.15)
                  : colors.surface,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isSelected
                    ? const Color(0xFFFF6B6B)
                    : const Color(0xFF2A2A2A),
              ),
            ),
            child: Text(
              t.$2,
              style: TextStyle(
                color: isSelected
                    ? const Color(0xFFFF6B6B)
                    : colors.textMuted,
                fontSize: 13,
                fontWeight: isSelected
                    ? FontWeight.w600
                    : FontWeight.normal,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
