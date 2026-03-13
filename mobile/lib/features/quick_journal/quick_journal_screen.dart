/// Quick Journal Screen — LOT 18.
///
/// Grille de 5 actions de journalisation rapide (<10 secondes chacune).
///
/// Actions :
///   🍽 Repas        → description + calories + protéines  → POST /nutrition/entries
///   💪 Workout      → type + durée + intensité            → POST /sessions
///   💧 Hydratation  → boutons rapides 250/500/750/1000 ml → POST /hydration/log
///   ⚖️ Poids        → valeur kg                          → POST /body-metrics
///   😴 Sommeil      → heures + qualité 1-5               → POST /sleep
///
/// Analytics déclenchés (LOT 18 + LOT 19) :
///   nutrition_logged, workout_logged, journal_entry (weight/sleep/hydration)
///   journal_open (LOT 19), journal_action_submitted (LOT 19)
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics/analytics_service.dart';  // LOT 19
import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';

// ── Constantes UI (non-color) ────────────────────────────────────────────────

const _kCardRadius = 16.0;
const _kSheetRadius = 24.0;

// ── Screen ────────────────────────────────────────────────────────────────────

class QuickJournalScreen extends ConsumerWidget {
  const QuickJournalScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    return Scaffold(
      backgroundColor: colors.navBackground,
      appBar: const SomaAppBar(
        title: 'Journal rapide',
        showBackButton: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Que souhaitez-vous enregistrer ?',
              style: TextStyle(
                color: colors.textSecondary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 16),

            // ── Grille 5 actions ──────────────────────────────────────────
            Expanded(
              child: _ActionsGrid(ref: ref),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Grille d'actions ──────────────────────────────────────────────────────────

class _ActionsGrid extends StatelessWidget {
  const _ActionsGrid({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    final actions = [
      _JournalAction(
        icon: Icons.restaurant_rounded,
        label: 'Repas',
        subtitle: 'Calories & protéines',
        color: const Color(0xFFFF9500),
        onTap: () => _showMealSheet(context, ref),
      ),
      _JournalAction(
        icon: Icons.fitness_center_rounded,
        label: 'Workout',
        subtitle: 'Séance entraînement',
        color: const Color(0xFF0A84FF),
        onTap: () => _showWorkoutSheet(context, ref),
      ),
      _JournalAction(
        icon: Icons.water_drop_rounded,
        label: 'Hydratation',
        subtitle: 'Eau & boissons',
        color: const Color(0xFF00B4D8),
        onTap: () => _showHydrationSheet(context, ref),
      ),
      _JournalAction(
        icon: Icons.monitor_weight_rounded,
        label: 'Poids',
        subtitle: 'Mesure corporelle',
        color: const Color(0xFF5E5CE6),
        onTap: () => _showWeightSheet(context, ref),
      ),
      _JournalAction(
        icon: Icons.bedtime_rounded,
        label: 'Sommeil',
        subtitle: 'Durée & qualité',
        color: const Color(0xFF34C759),
        onTap: () => _showSleepSheet(context, ref),
      ),
    ];

    return GridView.count(
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.1,
      physics: const NeverScrollableScrollPhysics(),
      children: actions
          .take(4)
          .map((a) => _ActionTile(action: a))
          .toList(),
    )
        .let(
          (grid) => Column(
            children: [
              Expanded(child: grid),
              // 5ème bouton centré
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: SizedBox(
                  width: double.infinity,
                  child: _ActionTile(action: actions[4], wide: true),
                ),
              ),
            ],
          ),
        );
  }

  // ── Sheets d'enregistrement ────────────────────────────────────────────────

  // LOT 19 : track journal_open + type avant chaque sheet.
  void _showMealSheet(BuildContext ctx, WidgetRef ref) {
    AnalyticsService.track(ref.read(apiClientProvider), AnalyticsEvents.journalOpen,
        props: {'type': 'meal'});
    _openSheet(ctx, child: _MealSheet(ref: ref));
  }

  void _showWorkoutSheet(BuildContext ctx, WidgetRef ref) {
    AnalyticsService.track(ref.read(apiClientProvider), AnalyticsEvents.journalOpen,
        props: {'type': 'workout'});
    _openSheet(ctx, child: _WorkoutSheet(ref: ref));
  }

  void _showHydrationSheet(BuildContext ctx, WidgetRef ref) {
    AnalyticsService.track(ref.read(apiClientProvider), AnalyticsEvents.journalOpen,
        props: {'type': 'hydration'});
    _openSheet(ctx, child: _HydrationSheet(ref: ref));
  }

  void _showWeightSheet(BuildContext ctx, WidgetRef ref) {
    AnalyticsService.track(ref.read(apiClientProvider), AnalyticsEvents.journalOpen,
        props: {'type': 'weight'});
    _openSheet(ctx, child: _WeightSheet(ref: ref));
  }

  void _showSleepSheet(BuildContext ctx, WidgetRef ref) {
    AnalyticsService.track(ref.read(apiClientProvider), AnalyticsEvents.journalOpen,
        props: {'type': 'sleep'});
    _openSheet(ctx, child: _SleepSheet(ref: ref));
  }

  static void _openSheet(BuildContext ctx, {required Widget child}) {
    final colors = ctx.somaColors;
    showModalBottomSheet(
      context: ctx,
      isScrollControlled: true,
      backgroundColor: colors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius:
            BorderRadius.vertical(top: Radius.circular(_kSheetRadius)),
      ),
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(ctx).viewInsets.bottom,
        ),
        child: child,
      ),
    );
  }
}

// ── Tuile action ──────────────────────────────────────────────────────────────

class _JournalAction {
  const _JournalAction({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({required this.action, this.wide = false});
  final _JournalAction action;
  final bool wide;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: action.onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: colors.surfaceVariant,
          borderRadius: BorderRadius.circular(_kCardRadius),
          border: Border.all(color: colors.border),
        ),
        child: wide
            ? Row(
                children: [
                  _iconBox,
                  const SizedBox(width: 14),
                  _labels(colors),
                ],
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _iconBox,
                  const SizedBox(height: 12),
                  _labels(colors),
                ],
              ),
      ),
    );
  }

  Widget get _iconBox => Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: action.color.withAlpha(30),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(action.icon, color: action.color, size: 22),
      );

  Widget _labels(dynamic colors) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            action.label,
            style: TextStyle(
              color: colors.text,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            action.subtitle,
            style: TextStyle(color: colors.textSecondary, fontSize: 12),
          ),
        ],
      );
}

// ── Sheet Repas ───────────────────────────────────────────────────────────────

class _MealSheet extends StatefulWidget {
  const _MealSheet({required this.ref});
  final WidgetRef ref;

  @override
  State<_MealSheet> createState() => _MealSheetState();
}

class _MealSheetState extends State<_MealSheet> {
  final _formKey = GlobalKey<FormState>();
  final _descCtrl = TextEditingController();
  final _calCtrl = TextEditingController();
  final _protCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _descCtrl.dispose();
    _calCtrl.dispose();
    _protCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _SheetWrapper(
      title: '🍽  Repas',
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            _SheetTextField(
              controller: _descCtrl,
              label: 'Description',
              hint: 'Ex : poulet riz brocolis',
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Description requise' : null,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _SheetTextField(
                    controller: _calCtrl,
                    label: 'Calories (kcal)',
                    hint: '450',
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _SheetTextField(
                    controller: _protCtrl,
                    label: 'Protéines (g)',
                    hint: '35',
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _SubmitButton(
              loading: _loading,
              onTap: _submit,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    try {
      final client = widget.ref.read(apiClientProvider);
      await client.post(
        ApiConstants.nutritionEntries,
        data: {
          'food_name': _descCtrl.text.trim(),
          'calories': double.tryParse(_calCtrl.text) ?? 0,
          'protein_g': double.tryParse(_protCtrl.text) ?? 0,
          'logged_at': DateTime.now().toIso8601String(),
          'source': 'quick_journal',
        },
      );
      // Analytics: nutrition_logged — wired in BATCH 11
      if (mounted) {
        Navigator.of(context).pop();
        _showSuccess(context, 'Repas enregistré ✓');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loading = false);
        _showError(context, 'Impossible d\'enregistrer le repas.');
      }
    }
  }
}

// ── Sheet Workout ─────────────────────────────────────────────────────────────

class _WorkoutSheet extends StatefulWidget {
  const _WorkoutSheet({required this.ref});
  final WidgetRef ref;

  @override
  State<_WorkoutSheet> createState() => _WorkoutSheetState();
}

class _WorkoutSheetState extends State<_WorkoutSheet> {
  String _type = 'strength';
  int _duration = 45;
  String _intensity = 'moderate';
  bool _loading = false;

  static const _types = [
    ('strength', 'Force'),
    ('cardio', 'Cardio'),
    ('hiit', 'HIIT'),
    ('mobility', 'Mobilité'),
    ('recovery', 'Récupération'),
  ];

  static const _intensities = [
    ('low', 'Faible'),
    ('moderate', 'Modérée'),
    ('high', 'Élevée'),
  ];

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return _SheetWrapper(
      title: '💪  Workout',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Type
          Text('Type',
              style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _types.map((t) {
              final selected = _type == t.$1;
              return GestureDetector(
                onTap: () => setState(() => _type = t.$1),
                child: _Chip(label: t.$2, selected: selected),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),

          // Durée
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Durée',
                  style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500)),
              Text('$_duration min',
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w700)),
            ],
          ),
          Slider(
            value: _duration.toDouble(),
            min: 10,
            max: 180,
            divisions: 34,
            activeColor: colors.accent,
            inactiveColor: colors.border,
            onChanged: (v) => setState(() => _duration = v.round()),
          ),

          // Intensité
          Text('Intensité',
              style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Row(
            children: _intensities.map((i) {
              final selected = _intensity == i.$1;
              return Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: GestureDetector(
                    onTap: () => setState(() => _intensity = i.$1),
                    child: _Chip(
                        label: i.$2, selected: selected, fullWidth: true),
                  ),
                ),
              );
            }).toList(),
          ),

          const SizedBox(height: 20),
          _SubmitButton(loading: _loading, onTap: _submit),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    setState(() => _loading = true);
    try {
      final client = widget.ref.read(apiClientProvider);
      await client.post(
        ApiConstants.sessions,
        data: {
          'exercise_type': _type,
          'duration_minutes': _duration,
          'intensity': _intensity,
          'started_at': DateTime.now().toIso8601String(),
          'source': 'quick_journal',
        },
      );
      // Analytics: workout_logged — wired in BATCH 11
      if (mounted) {
        Navigator.of(context).pop();
        _showSuccess(context, 'Workout enregistré ✓');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loading = false);
        _showError(context, 'Impossible d\'enregistrer le workout.');
      }
    }
  }
}

// ── Sheet Hydratation ─────────────────────────────────────────────────────────

class _HydrationSheet extends StatefulWidget {
  const _HydrationSheet({required this.ref});
  final WidgetRef ref;

  @override
  State<_HydrationSheet> createState() => _HydrationSheetState();
}

class _HydrationSheetState extends State<_HydrationSheet> {
  int? _selected;
  bool _loading = false;

  static const _quickAmounts = [250, 500, 750, 1000];

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return _SheetWrapper(
      title: '💧  Hydratation',
      child: Column(
        children: [
          // Boutons rapides
          GridView.count(
            crossAxisCount: 2,
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            shrinkWrap: true,
            childAspectRatio: 2.5,
            physics: const NeverScrollableScrollPhysics(),
            children: _quickAmounts.map((ml) {
              final selected = _selected == ml;
              return GestureDetector(
                onTap: () => setState(() => _selected = ml),
                child: Container(
                  decoration: BoxDecoration(
                    color: selected
                        ? colors.info.withAlpha(40)
                        : colors.surfaceVariant,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: selected
                          ? colors.info
                          : colors.border,
                    ),
                  ),
                  child: Center(
                    child: Text(
                      ml < 1000 ? '$ml mL' : '${ml / 1000} L',
                      style: TextStyle(
                        color: selected
                            ? colors.info
                            : colors.text,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          _SubmitButton(
            loading: _loading,
            enabled: _selected != null,
            onTap: _submit,
          ),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    if (_selected == null) return;
    setState(() => _loading = true);
    try {
      final client = widget.ref.read(apiClientProvider);
      await client.post(
        ApiConstants.hydrationLog,
        data: {
          'amount_ml': _selected,
          'logged_at': DateTime.now().toIso8601String(),
          'source': 'quick_journal',
        },
      );
      // Analytics: journal_entry — wired in BATCH 11
      if (mounted) {
        Navigator.of(context).pop();
        _showSuccess(context, '$_selected mL enregistrés ✓');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loading = false);
        _showError(context, 'Impossible d\'enregistrer l\'hydratation.');
      }
    }
  }
}

// ── Sheet Poids ───────────────────────────────────────────────────────────────

class _WeightSheet extends StatefulWidget {
  const _WeightSheet({required this.ref});
  final WidgetRef ref;

  @override
  State<_WeightSheet> createState() => _WeightSheetState();
}

class _WeightSheetState extends State<_WeightSheet> {
  final _ctrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _SheetWrapper(
      title: '⚖️  Poids',
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            _SheetTextField(
              controller: _ctrl,
              label: 'Poids (kg)',
              hint: '75.5',
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Valeur requise';
                final n = double.tryParse(v.replaceAll(',', '.'));
                if (n == null || n < 20 || n > 300) return 'Valeur invalide';
                return null;
              },
            ),
            const SizedBox(height: 20),
            _SubmitButton(loading: _loading, onTap: _submit),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final client = widget.ref.read(apiClientProvider);
      final weight =
          double.parse(_ctrl.text.trim().replaceAll(',', '.'));
      await client.post(
        ApiConstants.bodyMetrics,
        data: {
          'weight_kg': weight,
          'measured_at': DateTime.now().toIso8601String(),
          'source': 'quick_journal',
        },
      );
      // Analytics: journal_entry — wired in BATCH 11
      if (mounted) {
        Navigator.of(context).pop();
        _showSuccess(context, 'Poids enregistré ✓');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loading = false);
        _showError(context, 'Impossible d\'enregistrer le poids.');
      }
    }
  }
}

// ── Sheet Sommeil ─────────────────────────────────────────────────────────────

class _SleepSheet extends StatefulWidget {
  const _SleepSheet({required this.ref});
  final WidgetRef ref;

  @override
  State<_SleepSheet> createState() => _SleepSheetState();
}

class _SleepSheetState extends State<_SleepSheet> {
  double _hours = 7.5;
  int _quality = 3; // 1-5
  bool _loading = false;

  static const _qualityEmojis = ['😞', '😐', '😊', '😀', '🌟'];
  static const _qualityLabels = [
    'Mauvais', 'Passable', 'Correct', 'Bon', 'Excellent'
  ];

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return _SheetWrapper(
      title: '😴  Sommeil',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Durée
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Durée',
                  style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500)),
              Text(
                '${_hours.toStringAsFixed(1)} h',
                style: TextStyle(
                    color: colors.text,
                    fontSize: 15,
                    fontWeight: FontWeight.w700),
              ),
            ],
          ),
          Slider(
            value: _hours,
            min: 3,
            max: 12,
            divisions: 18,
            activeColor: colors.success,
            inactiveColor: colors.border,
            onChanged: (v) => setState(() => _hours = v),
          ),

          const SizedBox(height: 8),

          // Qualité
          Text('Qualité',
              style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(5, (i) {
              final q = i + 1;
              final selected = _quality == q;
              return GestureDetector(
                onTap: () => setState(() => _quality = q),
                child: Column(
                  children: [
                    Text(
                      _qualityEmojis[i],
                      style: TextStyle(
                          fontSize: selected ? 32 : 24),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _qualityLabels[i],
                      style: TextStyle(
                        color:
                            selected ? colors.text : colors.textSecondary,
                        fontSize: 11,
                        fontWeight: selected
                            ? FontWeight.w600
                            : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ),

          const SizedBox(height: 20),
          _SubmitButton(loading: _loading, onTap: _submit),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    setState(() => _loading = true);

    // Calcule heure coucher estimée (maintenant - durée)
    final now = DateTime.now();
    final sleepEnd = now;
    final sleepStart = now.subtract(
        Duration(minutes: (_hours * 60).round()));

    // Qualité → texte
    final qualityMap = {
      1: 'poor', 2: 'poor', 3: 'fair', 4: 'good', 5: 'excellent'
    };

    try {
      final client = widget.ref.read(apiClientProvider);
      await client.post(
        ApiConstants.sleepLog,
        data: {
          'sleep_start': sleepStart.toIso8601String(),
          'sleep_end': sleepEnd.toIso8601String(),
          'quality_score': _quality,
          'quality_label': qualityMap[_quality],
          'source': 'quick_journal',
        },
      );
      // Analytics: journal_entry — wired in BATCH 11
      if (mounted) {
        Navigator.of(context).pop();
        _showSuccess(context, 'Sommeil enregistré ✓');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loading = false);
        _showError(context, 'Impossible d\'enregistrer le sommeil.');
      }
    }
  }
}

// ── Widgets réutilisables ─────────────────────────────────────────────────────

/// Conteneur commun pour les BottomSheets.
class _SheetWrapper extends StatelessWidget {
  const _SheetWrapper({required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Barre de drag
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: colors.textMuted,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            // Titre
            Text(
              title,
              style: TextStyle(
                color: colors.text,
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 20),
            child,
          ],
        ),
      ),
    );
  }
}

/// Champ texte uniforme pour les sheets.
class _SheetTextField extends StatelessWidget {
  const _SheetTextField({
    required this.controller,
    required this.label,
    required this.hint,
    this.keyboardType = TextInputType.text,
    this.inputFormatters,
    this.validator,
  });

  final TextEditingController controller;
  final String label;
  final String hint;
  final TextInputType keyboardType;
  final List<TextInputFormatter>? inputFormatters;
  final FormFieldValidator<String>? validator;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: TextStyle(
                color: colors.textSecondary,
                fontSize: 13,
                fontWeight: FontWeight.w500)),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          keyboardType: keyboardType,
          inputFormatters: inputFormatters,
          validator: validator,
          style: TextStyle(color: colors.text, fontSize: 15),
          cursorColor: colors.accent,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle:
                TextStyle(color: colors.textSecondary, fontSize: 15),
            filled: true,
            fillColor: colors.surfaceVariant,
            contentPadding: const EdgeInsets.symmetric(
                horizontal: 14, vertical: 12),
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
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: colors.danger),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: colors.danger),
            ),
          ),
        ),
      ],
    );
  }
}

/// Bouton "Enregistrer" uniforme.
class _SubmitButton extends StatelessWidget {
  const _SubmitButton({
    required this.onTap,
    required this.loading,
    this.enabled = true,
  });

  final VoidCallback onTap;
  final bool loading;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton(
        onPressed: (enabled && !loading) ? onTap : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: colors.accent,
          foregroundColor: Colors.black,
          disabledBackgroundColor: colors.border,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14)),
        ),
        child: loading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  color: Colors.black,
                  strokeWidth: 2,
                ),
              )
            : const Text(
                'Enregistrer',
                style: TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700),
              ),
      ),
    );
  }
}

/// Chip de sélection.
class _Chip extends StatelessWidget {
  const _Chip({
    required this.label,
    required this.selected,
    this.fullWidth = false,
  });

  final String label;
  final bool selected;
  final bool fullWidth;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: EdgeInsets.symmetric(
          horizontal: fullWidth ? 0 : 14, vertical: 8),
      width: fullWidth ? double.infinity : null,
      decoration: BoxDecoration(
        color: selected ? colors.accent.withAlpha(30) : colors.surfaceVariant,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: selected ? colors.accent : colors.border,
        ),
      ),
      child: Center(
        child: Text(
          label,
          style: TextStyle(
            color: selected ? colors.accent : colors.text,
            fontSize: 13,
            fontWeight:
                selected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

// ── Helpers globaux ───────────────────────────────────────────────────────────

void _showSuccess(BuildContext context, String msg) {
  final colors = context.somaColors;
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(msg,
          style: const TextStyle(
              color: Colors.black, fontWeight: FontWeight.w600)),
      backgroundColor: colors.accent,
      duration: const Duration(seconds: 2),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  );
}

void _showError(BuildContext context, String msg) {
  final colors = context.somaColors;
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(msg, style: TextStyle(color: colors.text)),
      backgroundColor: colors.danger,
      duration: const Duration(seconds: 3),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  );
}

// ── Extension helper ──────────────────────────────────────────────────────────

extension _WidgetLet<T extends Widget> on T {
  R let<R>(R Function(T) fn) => fn(this);
}
