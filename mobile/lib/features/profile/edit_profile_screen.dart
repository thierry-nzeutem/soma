/// Écran Édition Profil — formulaire PATCH /api/v1/profile (LOT 6).
///
/// Champs : prénom, poids actuel, poids objectif, régime, IF, repas/jour.
/// N'expose pas les champs calculés (BMR/TDEE) — lecture seule.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'profile_notifier.dart';

class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _firstNameCtrl;
  late TextEditingController _currentWeightCtrl;
  late TextEditingController _goalWeightCtrl;
  late TextEditingController _mealsCtrl;
  String? _selectedDiet;
  bool _intermittentFasting = false;
  String? _fastingProtocol;
  bool _initialized = false;
  bool _isSaving = false;

  static const _diets = [
    ('', 'Standard'),
    ('vegetarian', 'Végétarien'),
    ('vegan', 'Vegan'),
    ('keto', 'Keto'),
    ('paleo', 'Paléo'),
    ('mediterranean', 'Méditerranéen'),
  ];

  static const _fastingProtocols = [
    ('16:8', '16:8'),
    ('18:6', '18:6'),
    ('20:4', '20:4'),
    ('5:2', '5:2'),
    ('OMAD', 'OMAD'),
  ];

  @override
  void initState() {
    super.initState();
    _firstNameCtrl = TextEditingController();
    _currentWeightCtrl = TextEditingController();
    _goalWeightCtrl = TextEditingController();
    _mealsCtrl = TextEditingController();
  }

  @override
  void dispose() {
    _firstNameCtrl.dispose();
    _currentWeightCtrl.dispose();
    _goalWeightCtrl.dispose();
    _mealsCtrl.dispose();
    super.dispose();
  }

  void _initFromProfile() {
    if (_initialized) return;
    final profileState = ref.read(profileProvider);
    profileState.whenData((profile) {
      _firstNameCtrl.text = profile.firstName ?? '';
      _currentWeightCtrl.text =
          profile.currentWeightKg?.toStringAsFixed(1) ?? '';
      _goalWeightCtrl.text = profile.goalWeightKg?.toStringAsFixed(1) ?? '';
      _mealsCtrl.text = profile.mealsPerDay?.toString() ?? '';
      _selectedDiet = profile.dietaryRegime;
      _intermittentFasting = profile.intermittentFasting;
      _fastingProtocol = profile.fastingProtocol;
    });
    _initialized = true;
  }

  @override
  Widget build(BuildContext context) {
    _initFromProfile();
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Modifier le profil'),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const _FieldLabel('Prénom'),
            _SomaTextField(
              controller: _firstNameCtrl,
              hint: 'Votre prénom',
            ),
            const SizedBox(height: 16),

            const _FieldLabel('Poids actuel (kg)'),
            _SomaTextField(
              controller: _currentWeightCtrl,
              hint: 'ex. 75.0',
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
            const SizedBox(height: 16),

            const _FieldLabel('Poids objectif (kg)'),
            _SomaTextField(
              controller: _goalWeightCtrl,
              hint: 'ex. 70.0',
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
            const SizedBox(height: 16),

            const _FieldLabel('Régime alimentaire'),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: colors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: colors.border),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedDiet,
                  dropdownColor: colors.surfaceVariant,
                  style: TextStyle(color: colors.text, fontSize: 14),
                  hint: Text('Choisir',
                      style: TextStyle(color: colors.textMuted)),
                  items: _diets
                      .map((d) => DropdownMenuItem(
                            value: d.$1.isEmpty ? null : d.$1,
                            child: Text(d.$2),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _selectedDiet = v),
                ),
              ),
            ),
            const SizedBox(height: 16),

            const _FieldLabel('Repas par jour'),
            _SomaTextField(
              controller: _mealsCtrl,
              hint: 'ex. 3',
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 20),

            // Jeûne intermittent
            Row(
              children: [
                Switch(
                  value: _intermittentFasting,
                  onChanged: (v) =>
                      setState(() => _intermittentFasting = v),
                  activeColor: colors.accent,
                ),
                const SizedBox(width: 10),
                Text(
                  'Jeûne intermittent',
                  style: TextStyle(color: colors.text, fontSize: 14),
                ),
              ],
            ),
            if (_intermittentFasting) ...[
              const SizedBox(height: 12),
              const _FieldLabel('Protocole'),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(
                  color: colors.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: colors.border),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _fastingProtocol,
                    dropdownColor: colors.surfaceVariant,
                    style: TextStyle(color: colors.text, fontSize: 14),
                    hint: Text('Choisir protocole',
                        style: TextStyle(color: colors.textMuted)),
                    items: _fastingProtocols
                        .map((p) => DropdownMenuItem(
                              value: p.$1,
                              child: Text(p.$2),
                            ))
                        .toList(),
                    onChanged: (v) => setState(() => _fastingProtocol = v),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 32),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isSaving ? null : _save,
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.accent,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isSaving
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.black),
                      )
                    : const Text('Enregistrer',
                        style: TextStyle(
                            fontSize: 15, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      final fields = <String, dynamic>{};
      if (_firstNameCtrl.text.trim().isNotEmpty) {
        fields['first_name'] = _firstNameCtrl.text.trim();
      }
      final cw = double.tryParse(_currentWeightCtrl.text);
      if (cw != null) fields['current_weight_kg'] = cw;
      final gw = double.tryParse(_goalWeightCtrl.text);
      if (gw != null) fields['goal_weight_kg'] = gw;
      if (_selectedDiet != null) fields['dietary_regime'] = _selectedDiet;
      final meals = int.tryParse(_mealsCtrl.text);
      if (meals != null) fields['meals_per_day'] = meals;
      fields['intermittent_fasting'] = _intermittentFasting;
      if (_intermittentFasting && _fastingProtocol != null) {
        fields['fasting_protocol'] = _fastingProtocol;
      }

      await ref.read(profileProvider.notifier).updateProfile(fields);
      if (mounted) {
        final colors = context.somaColors;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Profil mis à jour'),
            backgroundColor: colors.accent,
          ),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        final colors = context.somaColors;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: colors.danger,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }
}

// ── Widgets ───────────────────────────────────────────────────────────────────

class _FieldLabel extends StatelessWidget {
  final String label;

  const _FieldLabel(this.label);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        label,
        style: TextStyle(
          color: colors.textMuted,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _SomaTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final TextInputType? keyboardType;

  const _SomaTextField({
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
          borderSide: BorderSide(color: colors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: colors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: colors.accent),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
    );
  }
}
