/// Écran Profil — lecture du profil utilisateur (LOT 6).
///
/// Affiche les données du profil + métriques calculées.
/// Liens vers édition, historique, longevity, paramètres.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/profile.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'profile_notifier.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final state = ref.watch(profileProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Profil',
        actions: [
          IconButton(
            icon: Icon(Icons.edit_rounded, color: colors.accent),
            onPressed: () => context.push('/profile/edit'),
            tooltip: 'Modifier',
          ),
        ],
      ),
      body: state.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (err, _) => _ErrorView(
          message: err.toString(),
          onRetry: () => ref.read(profileProvider.notifier).refresh(),
        ),
        data: (profile) => RefreshIndicator(
          color: colors.accent,
          backgroundColor: colors.surface,
          onRefresh: () => ref.read(profileProvider.notifier).refresh(),
          child: _ProfileBody(profile: profile),
        ),
      ),
    );
  }
}

class _ProfileBody extends StatelessWidget {
  final UserProfile profile;

  const _ProfileBody({required this.profile});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        // Avatar + nom
        Center(
          child: Column(
            children: [
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: colors.accent.withOpacity(0.12),
                  shape: BoxShape.circle,
                  border: Border.all(
                      color: colors.accent.withOpacity(0.3),
                      width: 2),
                ),
                child: Icon(Icons.person_rounded,
                    size: 40, color: colors.accent),
              ),
              const SizedBox(height: 12),
              Text(
                profile.displayName,
                style: TextStyle(
                  color: colors.text,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              if (profile.profileCompletenessScore > 0)
                Text(
                  'Profil complété à ${profile.profileCompletenessScore.toStringAsFixed(0)}%',
                  style: TextStyle(
                    color: colors.textSecondary,
                    fontSize: 13,
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 28),

        // Infos personnelles
        const _SectionTitle('Informations personnelles'),
        _ProfileRow('Âge', profile.age != null ? '${profile.age} ans' : '—'),
        _ProfileRow('Sexe', profile.sex ?? '—'),
        _ProfileRow(
            'Taille',
            profile.heightCm != null
                ? '${profile.heightCm!.toStringAsFixed(0)} cm'
                : '—'),
        _ProfileRow(
            'Poids actuel',
            profile.currentWeightKg != null
                ? '${profile.currentWeightKg!.toStringAsFixed(1)} kg'
                : '—'),
        _ProfileRow(
            'Poids objectif',
            profile.goalWeightKg != null
                ? '${profile.goalWeightKg!.toStringAsFixed(1)} kg'
                : '—'),
        const SizedBox(height: 20),

        // Objectif & activité
        const _SectionTitle('Objectifs & Activité'),
        _ProfileRow('Objectif', profile.goalLabel ?? '—'),
        _ProfileRow("Niveau d'activité", profile.activityLabel ?? '—'),
        _ProfileRow('Forme physique', profile.fitnessLabel ?? '—'),
        _ProfileRow('Régime', profile.dietaryRegime ?? '—'),
        if (profile.intermittentFasting)
          _ProfileRow('Jeûne', profile.fastingProtocol ?? 'Activé'),
        if (profile.mealsPerDay != null)
          _ProfileRow('Repas / jour', '${profile.mealsPerDay}'),
        const SizedBox(height: 20),

        // Métriques calculées
        const _SectionTitle('Métriques calculées'),
        _ProfileRow(
            'IMC',
            profile.computed.bmi != null
                ? profile.computed.bmi!.toStringAsFixed(1)
                : '—'),
        _ProfileRow(
            'BMR (Mifflin)',
            profile.computed.bmrKcal != null
                ? '${profile.computed.bmrKcal!.toStringAsFixed(0)} kcal'
                : '—'),
        _ProfileRow(
            'TDEE',
            profile.computed.tdeeKcal != null
                ? '${profile.computed.tdeeKcal!.toStringAsFixed(0)} kcal'
                : '—'),
        _ProfileRow(
            'Objectif calories',
            profile.computed.targetCaloriesKcal != null
                ? '${profile.computed.targetCaloriesKcal!.toStringAsFixed(0)} kcal'
                : '—'),
        _ProfileRow(
            'Objectif protéines',
            profile.computed.targetProteinG != null
                ? '${profile.computed.targetProteinG!.toStringAsFixed(0)} g'
                : '—'),
        _ProfileRow(
            'Objectif hydratation',
            profile.computed.targetHydrationMl != null
                ? '${(profile.computed.targetHydrationMl! / 1000).toStringAsFixed(1)} L'
                : '—'),
        const SizedBox(height: 28),

        // Actions
        const _SectionTitle('Accès rapide'),
        _ActionTile(
          icon: Icons.timeline_rounded,
          label: 'Historique métriques',
          accentColor: colors.accent,
          onTap: () => context.push('/profile/history'),
        ),
        const SizedBox(height: 8),
        _ActionTile(
          icon: Icons.biotech_rounded,
          label: 'Score Longévité',
          accentColor: const Color(0xFF9B72CF),
          onTap: () => context.go('/longevity'),
        ),
        const SizedBox(height: 8),
        _ActionTile(
          icon: Icons.science_rounded,
          label: 'Biomarqueurs',
          accentColor: colors.info,
          onTap: () => context.push('/biomarkers'),
        ),
        const SizedBox(height: 8),
        _ActionTile(
          icon: Icons.sports_rounded,
          label: 'Coach Platform',
          accentColor: colors.accent,
          onTap: () => context.push('/coach-platform'),
        ),
        const SizedBox(height: 8),
        _ActionTile(
          icon: Icons.settings_rounded,
          label: 'Paramètres',
          accentColor: colors.textSecondary,
          onTap: () => context.push('/settings'),
        ),
        const SizedBox(height: 32),
      ],
    );
  }
}

// ── Widgets ───────────────────────────────────────────────────────────────────

class _SectionTitle extends StatelessWidget {
  final String label;

  const _SectionTitle(this.label);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          color: colors.textMuted,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _ProfileRow extends StatelessWidget {
  final String label;
  final String value;

  const _ProfileRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Text(
            label,
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
          const Spacer(),
          Text(
            value,
            style: TextStyle(
              color: colors.text,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color accentColor;
  final VoidCallback onTap;

  const _ActionTile({
    required this.icon,
    required this.label,
    required this.accentColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Material(
      color: colors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: colors.border),
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: accentColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(9),
                ),
                child: Icon(icon, color: accentColor, size: 18),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(color: colors.text, fontSize: 14),
                ),
              ),
              Icon(Icons.chevron_right_rounded,
                  color: colors.textMuted, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.person_off_rounded,
                size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Impossible de charger le profil',
              style: TextStyle(color: colors.text, fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(color: colors.textSecondary, fontSize: 12),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
