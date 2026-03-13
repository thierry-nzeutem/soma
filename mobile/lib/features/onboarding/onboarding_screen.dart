/// Écran Onboarding SOMA — LOT 18.
///
/// Flow en 7 pages via PageView :
///   0. Welcome     — titre + CTA Commencer
///   1. Goal        — 4 objectifs (performance, health, weight_loss, longevity)
///   2. Baseline    — âge, sexe, taille, poids
///   3. Activity    — niveau activité + fréquence sport
///   4. Sleep       — heures + qualité
///   5. Bio         — accès biomarqueurs
///   6. Summary     — récapitulatif + "Lancer SOMA"
///
/// Le bouton "Suivant" est désactivé si les champs requis ne sont pas remplis.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'onboarding_notifier.dart';
import '../../core/models/onboarding.dart';
import '../../core/theme/theme_extensions.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _controller = PageController();
  int _currentPage = 0;
  bool _isSubmitting = false;

  static const _totalPages = 7;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _nextPage() {
    if (_currentPage < _totalPages - 1) {
      _controller.nextPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
      );
    }
  }

  void _prevPage() {
    if (_currentPage > 0) {
      _controller.previousPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeInOut,
      );
    }
  }

  Future<void> _submit() async {
    if (_isSubmitting) return;
    setState(() => _isSubmitting = true);

    try {
      final result = await ref.read(onboardingProvider.notifier).submit();
      if (!mounted) return;
      // Naviguer vers le briefing avec le message de bienvenue
      context.go('/briefing', extra: result.coachWelcomeMessage);
    } catch (e) {
      if (!mounted) return;
      final colors = context.somaColors;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur : ${e.toString()}'),
          backgroundColor: colors.danger,
        ),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(onboardingProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          children: [
            // ── Barre de progression ─────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Row(
                children: [
                  if (_currentPage > 0)
                    GestureDetector(
                      onTap: _prevPage,
                      child: Icon(
                        Icons.arrow_back_ios_new_rounded,
                        color: colors.text,
                        size: 20,
                      ),
                    ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: LinearProgressIndicator(
                      value: (_currentPage + 1) / _totalPages,
                      backgroundColor: colors.border,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        colors.accent,
                      ),
                      minHeight: 3,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${_currentPage + 1}/$_totalPages',
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),

            // ── Pages ────────────────────────────────────────────────────
            Expanded(
              child: PageView(
                controller: _controller,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (i) => setState(() => _currentPage = i),
                children: [
                  _WelcomePage(onNext: _nextPage),
                  _GoalPage(data: data, onNext: _nextPage),
                  _BaselinePage(data: data, onNext: _nextPage),
                  _ActivityPage(data: data, onNext: _nextPage),
                  _SleepPage(data: data, onNext: _nextPage),
                  _BioPage(data: data, onNext: _nextPage),
                  _SummaryPage(
                    data: data,
                    isSubmitting: _isSubmitting,
                    onSubmit: _submit,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── PAGE 0 : Welcome ──────────────────────────────────────────────────────────

class _WelcomePage extends StatelessWidget {
  final VoidCallback onNext;

  const _WelcomePage({required this.onNext});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.monitor_heart_outlined,
              color: colors.accent, size: 80),
          const SizedBox(height: 32),
          Text(
            'Bienvenue dans SOMA',
            style: TextStyle(
              color: colors.text,
              fontSize: 28,
              fontWeight: FontWeight.w700,
              height: 1.2,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            'Votre coach santé IA personnel.\nQuelques questions pour personnaliser votre expérience.',
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 16,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 48),
          _PrimaryButton(label: 'Commencer', onTap: onNext),
        ],
      ),
    );
  }
}

// ── PAGE 1 : Goal ─────────────────────────────────────────────────────────────

class _GoalPage extends ConsumerWidget {
  final OnboardingData data;
  final VoidCallback onNext;

  const _GoalPage({required this.data, required this.onNext});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goals = [
      ('performance', '🏆', 'Performance', 'Maximiser vos capacités'),
      ('health', '❤️', 'Santé globale', 'Équilibre et bien-être'),
      ('weight_loss', '⚖️', 'Transformation', 'Perte de poids intelligente'),
      ('longevity', '🌱', 'Longévité', 'Vieillir en pleine santé'),
    ];

    return _PageWrapper(
      title: 'Votre objectif principal',
      subtitle: 'SOMA adaptera vos recommandations à cet objectif.',
      child: Column(
        children: [
          ...goals.map((g) => _SelectionTile(
                emoji: g.$2,
                title: g.$3,
                subtitle: g.$4,
                selected: data.primaryGoal == g.$1,
                onTap: () {
                  ref.read(onboardingProvider.notifier).setPrimaryGoal(g.$1);
                },
              )),
          const SizedBox(height: 24),
          _PrimaryButton(label: 'Continuer', onTap: onNext),
        ],
      ),
    );
  }
}

// ── PAGE 2 : Baseline ─────────────────────────────────────────────────────────

class _BaselinePage extends ConsumerStatefulWidget {
  final OnboardingData data;
  final VoidCallback onNext;

  const _BaselinePage({required this.data, required this.onNext});

  @override
  ConsumerState<_BaselinePage> createState() => _BaselinePageState();
}

class _BaselinePageState extends ConsumerState<_BaselinePage> {
  late final _ageCtrl = TextEditingController(
      text: widget.data.age.toString());
  late final _heightCtrl = TextEditingController(
      text: widget.data.heightCm.toStringAsFixed(0));
  late final _weightCtrl = TextEditingController(
      text: widget.data.weightKg.toStringAsFixed(1));
  late final _firstNameCtrl = TextEditingController(
      text: widget.data.firstName ?? '');

  final _sexes = [
    ('male', 'Homme'),
    ('female', 'Femme'),
    ('other', 'Autre'),
  ];

  @override
  void dispose() {
    _ageCtrl.dispose();
    _heightCtrl.dispose();
    _weightCtrl.dispose();
    _firstNameCtrl.dispose();
    super.dispose();
  }

  void _save() {
    final n = ref.read(onboardingProvider.notifier);
    final name = _firstNameCtrl.text.trim();
    if (name.isNotEmpty) n.setFirstName(name);
    final age = int.tryParse(_ageCtrl.text);
    if (age != null && age >= 13 && age <= 120) n.setAge(age);
    final h = double.tryParse(_heightCtrl.text);
    if (h != null && h >= 100 && h <= 250) n.setHeightCm(h);
    final w = double.tryParse(_weightCtrl.text);
    if (w != null && w >= 30 && w <= 300) n.setWeightKg(w);
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(onboardingProvider);
    final colors = context.somaColors;

    return _PageWrapper(
      title: 'Votre profil',
      subtitle: 'Pour calculer vos objectifs personnalisés.',
      child: Column(
        children: [
          _TextField(controller: _firstNameCtrl, label: 'Prénom (optionnel)'),
          const SizedBox(height: 12),
          _TextField(
            controller: _ageCtrl,
            label: 'Âge',
            keyboardType: TextInputType.number,
            suffix: 'ans',
          ),
          const SizedBox(height: 12),
          // Sexe
          Text('Sexe',
              style: TextStyle(color: colors.textMuted, fontSize: 13)),
          const SizedBox(height: 6),
          Row(
            children: _sexes.map((s) => Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: _ToggleButton(
                  label: s.$2,
                  selected: data.sex == s.$1,
                  onTap: () => ref.read(onboardingProvider.notifier).setSex(s.$1),
                ),
              ),
            )).toList(),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _TextField(
                  controller: _heightCtrl,
                  label: 'Taille',
                  keyboardType: TextInputType.number,
                  suffix: 'cm',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _TextField(
                  controller: _weightCtrl,
                  label: 'Poids',
                  keyboardType: TextInputType.number,
                  suffix: 'kg',
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _PrimaryButton(label: 'Continuer', onTap: _save),
        ],
      ),
    );
  }
}

// ── PAGE 3 : Activity ─────────────────────────────────────────────────────────

class _ActivityPage extends ConsumerWidget {
  final OnboardingData data;
  final VoidCallback onNext;

  const _ActivityPage({required this.data, required this.onNext});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final levels = [
      ('sedentary', '🪑', 'Sédentaire', '< 3 séances / semaine'),
      ('moderate', '🚶', 'Modéré', '3-5 séances / semaine'),
      ('athlete', '🏃', 'Athlète', '6+ séances / semaine'),
    ];

    return _PageWrapper(
      title: 'Niveau d\'activité',
      subtitle: 'Votre niveau physique habituel.',
      child: Column(
        children: [
          ...levels.map((l) => _SelectionTile(
                emoji: l.$2,
                title: l.$3,
                subtitle: l.$4,
                selected: data.activityLevel == l.$1,
                onTap: () =>
                    ref.read(onboardingProvider.notifier).setActivityLevel(l.$1),
              )),
          const SizedBox(height: 16),
          // Fréquence sport
          Text(
            'Séances par semaine : ${data.sportFrequencyPerWeek}',
            style: TextStyle(color: colors.text, fontSize: 14),
          ),
          Slider(
            value: data.sportFrequencyPerWeek.toDouble(),
            min: 0,
            max: 14,
            divisions: 14,
            activeColor: colors.accent,
            inactiveColor: colors.border,
            label: '${data.sportFrequencyPerWeek}',
            onChanged: (v) => ref
                .read(onboardingProvider.notifier)
                .setSportFrequency(v.round()),
          ),
          const SizedBox(height: 24),
          _PrimaryButton(label: 'Continuer', onTap: onNext),
        ],
      ),
    );
  }
}

// ── PAGE 4 : Sleep ────────────────────────────────────────────────────────────

class _SleepPage extends ConsumerWidget {
  final OnboardingData data;
  final VoidCallback onNext;

  const _SleepPage({required this.data, required this.onNext});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final qualities = [
      ('poor', '😫', 'Mauvais'),
      ('fair', '😐', 'Moyen'),
      ('good', '😊', 'Bon'),
      ('excellent', '😴', 'Excellent'),
    ];

    return _PageWrapper(
      title: 'Votre sommeil',
      subtitle: 'Le sommeil est le fondement de la récupération.',
      child: Column(
        children: [
          Text(
            '${data.sleepHoursPerNight.toStringAsFixed(1)}h par nuit',
            style: TextStyle(
              color: colors.text,
              fontSize: 22,
              fontWeight: FontWeight.w600,
            ),
          ),
          Slider(
            value: data.sleepHoursPerNight,
            min: 4.0,
            max: 11.0,
            divisions: 14,
            activeColor: colors.accent,
            inactiveColor: colors.border,
            label: '${data.sleepHoursPerNight.toStringAsFixed(1)}h',
            onChanged: (v) =>
                ref.read(onboardingProvider.notifier).setSleepHours(v),
          ),
          const SizedBox(height: 16),
          Text(
            'Qualité perçue',
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: qualities.map((q) {
              final selected = data.estimatedSleepQuality == q.$1;
              return GestureDetector(
                onTap: () => ref
                    .read(onboardingProvider.notifier)
                    .setSleepQuality(q.$1),
                child: Column(
                  children: [
                    Text(q.$2, style: const TextStyle(fontSize: 28)),
                    const SizedBox(height: 4),
                    Text(
                      q.$3,
                      style: TextStyle(
                        color: selected
                            ? colors.accent
                            : colors.textMuted,
                        fontSize: 11,
                        fontWeight:
                            selected ? FontWeight.w600 : FontWeight.w400,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          _PrimaryButton(label: 'Continuer', onTap: onNext),
        ],
      ),
    );
  }
}

// ── PAGE 5 : Bio ──────────────────────────────────────────────────────────────

class _BioPage extends ConsumerWidget {
  final OnboardingData data;
  final VoidCallback onNext;

  const _BioPage({required this.data, required this.onNext});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    return _PageWrapper(
      title: 'Biomarqueurs',
      subtitle: 'Optionnel — enrichit considérablement les analyses.',
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: colors.surfaceVariant,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(Icons.biotech_outlined,
                    color: colors.info, size: 32),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Résultats d\'analyse sanguine',
                        style: TextStyle(
                          color: colors.text,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Bilan sanguin, vitamines, hormones...',
                        style: TextStyle(
                          color: colors.textMuted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                Switch(
                  value: data.hasBiomarkerAccess,
                  activeColor: colors.accent,
                  onChanged: (v) =>
                      ref.read(onboardingProvider.notifier).setHasBiomarkerAccess(v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _PrimaryButton(label: 'Continuer', onTap: onNext),
        ],
      ),
    );
  }
}

// ── PAGE 6 : Summary ──────────────────────────────────────────────────────────

class _SummaryPage extends StatelessWidget {
  final OnboardingData data;
  final bool isSubmitting;
  final VoidCallback onSubmit;

  const _SummaryPage({
    required this.data,
    required this.isSubmitting,
    required this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return _PageWrapper(
      title: 'Votre profil',
      subtitle: 'Vérifiez et lancez SOMA.',
      child: Column(
        children: [
          // Récapitulatif
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: colors.surfaceVariant,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                _SummaryRow(
                  label: 'Objectif',
                  value: _goalLabel(data.primaryGoal),
                ),
                _SummaryRow(label: 'Âge', value: '${data.age} ans'),
                _SummaryRow(
                  label: 'Profil',
                  value:
                      '${data.heightCm.toStringAsFixed(0)}cm · ${data.weightKg.toStringAsFixed(1)}kg',
                ),
                _SummaryRow(
                  label: 'Activité',
                  value: _activityLabel(data.activityLevel),
                ),
                _SummaryRow(
                  label: 'Sommeil',
                  value: '${data.sleepHoursPerNight.toStringAsFixed(1)}h',
                ),
                _SummaryRow(
                  label: 'Biomarqueurs',
                  value: data.hasBiomarkerAccess ? 'Activés' : 'Non',
                  isLast: true,
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          // Bouton principal
          isSubmitting
              ? Center(
                  child: CircularProgressIndicator(
                    color: colors.accent,
                  ),
                )
              : _PrimaryButton(label: '🚀 Lancer SOMA', onTap: onSubmit),
        ],
      ),
    );
  }

  static String _goalLabel(String goal) {
    return switch (goal) {
      'performance' => 'Performance',
      'weight_loss' => 'Transformation',
      'longevity' => 'Longévité',
      _ => 'Santé globale',
    };
  }

  static String _activityLabel(String level) {
    return switch (level) {
      'athlete' => 'Athlète',
      'moderate' => 'Modéré',
      _ => 'Sédentaire',
    };
  }
}

class _SummaryRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isLast;

  const _SummaryRow({
    required this.label,
    required this.value,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: TextStyle(
                    color: colors.textMuted, fontSize: 13),
              ),
              Text(
                value,
                style: TextStyle(
                  color: colors.text,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        if (!isLast)
          Divider(color: colors.border, height: 1),
      ],
    );
  }
}

// ── Widgets helpers ───────────────────────────────────────────────────────────

/// Wrapper commun pour les pages (titre + sous-titre + contenu scrollable).
class _PageWrapper extends StatelessWidget {
  final String title;
  final String subtitle;
  final Widget child;

  const _PageWrapper({
    required this.title,
    required this.subtitle,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),
          Text(
            title,
            style: TextStyle(
              color: colors.text,
              fontSize: 24,
              fontWeight: FontWeight.w700,
              height: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 14,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 28),
          child,
        ],
      ),
    );
  }
}

/// Bouton principal vert SOMA.
class _PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _PrimaryButton({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: colors.accent,
          foregroundColor: Colors.black,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        child: Text(label),
      ),
    );
  }
}

/// Tuile de sélection (objectif, activité).
class _SelectionTile extends StatelessWidget {
  final String emoji;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  const _SelectionTile({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected
              ? colors.accent.withAlpha(20)
              : colors.surfaceVariant,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected
                ? colors.accent
                : colors.border,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 28)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color:
                          selected ? colors.accent : colors.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            if (selected)
              Icon(Icons.check_circle_rounded,
                  color: colors.accent, size: 20),
          ],
        ),
      ),
    );
  }
}

/// Bouton toggle pour la sélection de sexe.
class _ToggleButton extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ToggleButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: selected
              ? colors.accent.withAlpha(20)
              : colors.surfaceVariant,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected
                ? colors.accent
                : colors.border,
          ),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            color: selected ? colors.accent : colors.text,
            fontSize: 13,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}

/// Champ de texte stylé SOMA.
class _TextField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final TextInputType? keyboardType;
  final String? suffix;

  const _TextField({
    required this.controller,
    required this.label,
    this.keyboardType,
    this.suffix,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      style: TextStyle(color: colors.text),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: colors.textMuted),
        suffixText: suffix,
        suffixStyle: TextStyle(color: colors.textMuted),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: colors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: colors.accent),
        ),
        filled: true,
        fillColor: colors.surfaceVariant,
      ),
    );
  }
}
