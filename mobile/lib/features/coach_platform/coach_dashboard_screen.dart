/// SOMA LOT 17 — Coach Dashboard Screen.
///
/// Vue principale du coach : liste d'athlètes + alertes globales + FAB.
/// Consomme [coachDashboardProvider] (GET /api/v1/coach-platform/dashboard).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/coach_platform.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import '../../shared/widgets/risk_level_badge.dart';
import '../../shared/widgets/athlete_alert_card.dart';
import 'coach_platform_notifier.dart';

class CoachDashboardScreen extends ConsumerWidget {
  const CoachDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final dashboardAsync = ref.watch(coachDashboardProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Coach',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () =>
                ref.read(coachDashboardProvider.notifier).refresh(),
            tooltip: 'Actualiser',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: colors.accent,
        foregroundColor: Colors.black,
        onPressed: () => _showAddAthleteDialog(context, ref),
        icon: const Icon(Icons.person_add),
        label: const Text('Ajouter un athlète'),
      ),
      body: dashboardAsync.when(
        loading: () =>
            Center(child: CircularProgressIndicator(color: colors.accent)),
        error: (e, _) => _ErrorView(
          message: e.toString(),
          onRetry: () => ref.read(coachDashboardProvider.notifier).refresh(),
        ),
        data: (overview) {
          if (overview == null) {
            return _NoProfileView(ref: ref);
          }
          return _DashboardBody(overview: overview);
        },
      ),
    );
  }

  // ── Ajout athlète via dialog ───────────────────────────────────────────────

  void _showAddAthleteDialog(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final userIdController = TextEditingController();
    final nameController = TextEditingController();
    final sportController = TextEditingController();

    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: colors.surface,
        title: Text('Ajouter un athlète',
            style: TextStyle(color: colors.text)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _DialogTextField(
                controller: userIdController, label: 'ID utilisateur SOMA'),
            const SizedBox(height: 12),
            _DialogTextField(
                controller: nameController, label: 'Nom affiché'),
            const SizedBox(height: 12),
            _DialogTextField(
                controller: sportController,
                label: 'Sport (optionnel)',
                required: false),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child:
                const Text('Annuler', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: colors.accent,
              foregroundColor: Colors.black,
            ),
            onPressed: () {
              if (userIdController.text.isEmpty || nameController.text.isEmpty) {
                return;
              }
              Navigator.pop(context);
              ref.read(coachDashboardProvider.notifier).addAthlete(
                    AthleteCreate(
                      userId: userIdController.text.trim(),
                      displayName: nameController.text.trim(),
                      sport: sportController.text.trim().isEmpty
                          ? null
                          : sportController.text.trim(),
                    ),
                  );
            },
            child: const Text('Ajouter'),
          ),
        ],
      ),
    );
  }
}

// ── Corps du dashboard ────────────────────────────────────────────────────────

class _DashboardBody extends StatelessWidget {
  final CoachAthletesOverview overview;
  const _DashboardBody({required this.overview});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final atRisk = overview.athletesSummary
        .where((a) => a.isAtRisk)
        .toList();
    final allAlerts = overview.athletesSummary
        .expand((a) => a.activeAlerts.map((msg) => (a, msg)))
        .take(5)
        .toList();

    return RefreshIndicator(
      color: colors.accent,
      backgroundColor: colors.surface,
      onRefresh: () async {
        // RefreshIndicator needs a future
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Stats globales ──────────────────────────────────────────────
          _StatsRow(
            totalAthletes: overview.totalAthletes,
            athletesAtRisk: overview.athletesAtRisk,
          ),
          const SizedBox(height: 20),

          // ── Alertes actives ─────────────────────────────────────────────
          if (allAlerts.isNotEmpty) ...[
            const _SectionHeader(title: 'Alertes actives', icon: Icons.warning_amber_rounded),
            const SizedBox(height: 8),
            ...allAlerts.map(
              (entry) => AthleteAlertCard(
                athleteName: entry.$1.athleteName,
                severity: _alertSeverity(entry.$1.riskLevel),
                message: entry.$2,
                onTap: () => Navigator.pushNamed(
                  context,
                  '/coach-platform/athlete/${entry.$1.athleteId}',
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],

          // ── Athlètes à risque en premier ────────────────────────────────
          if (atRisk.isNotEmpty) ...[
            const _SectionHeader(
                title: 'Athlètes à surveiller', icon: Icons.monitor_heart_rounded),
            const SizedBox(height: 8),
            ...atRisk.map((a) => _AthleteCard(summary: a)),
            const SizedBox(height: 20),
          ],

          // ── Tous les athlètes ───────────────────────────────────────────
          const _SectionHeader(
              title: 'Tous les athlètes', icon: Icons.group_rounded),
          const SizedBox(height: 8),
          if (overview.athletesSummary.isEmpty)
            const _EmptyAthletes()
          else
            ...overview.athletesSummary.map((a) => _AthleteCard(summary: a)),
          const SizedBox(height: 80), // space for FAB
        ],
      ),
    );
  }

  String _alertSeverity(String riskLevel) => switch (riskLevel) {
        'red' => 'critical',
        'orange' => 'warning',
        'yellow' => 'warning',
        _ => 'info',
      };
}

// ── Carte athlète ─────────────────────────────────────────────────────────────

class _AthleteCard extends StatelessWidget {
  final AthleteDashboardSummary summary;
  const _AthleteCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Card(
      color: colors.surface,
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: colors.border,
          child: Text(
            summary.athleteName.isNotEmpty
                ? summary.athleteName[0].toUpperCase()
                : '?',
            style: TextStyle(
                color: colors.text, fontWeight: FontWeight.bold),
          ),
        ),
        title: Text(
          summary.athleteName,
          style: TextStyle(
              color: colors.text, fontWeight: FontWeight.w600),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (summary.readinessScore != null)
              Text(
                'Récupération : ${summary.readinessScore!.toStringAsFixed(0)}/100',
                style: TextStyle(color: colors.textMuted, fontSize: 12),
              ),
            if (summary.hasAlerts)
              Text(
                '${summary.activeAlerts.length} alerte(s)',
                style: TextStyle(color: colors.warning, fontSize: 12),
              ),
          ],
        ),
        trailing: RiskLevelBadge(riskLevel: summary.riskLevel),
        onTap: () => Navigator.pushNamed(
          context,
          '/coach-platform/athlete/${summary.athleteId}',
        ),
      ),
    );
  }
}

// ── Stats globales ────────────────────────────────────────────────────────────

class _StatsRow extends StatelessWidget {
  final int totalAthletes;
  final int athletesAtRisk;
  const _StatsRow(
      {required this.totalAthletes, required this.athletesAtRisk});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            label: 'Athlètes',
            value: totalAthletes.toString(),
            icon: Icons.group_rounded,
            color: colors.accent,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            label: 'À surveiller',
            value: athletesAtRisk.toString(),
            icon: Icons.warning_rounded,
            color: athletesAtRisk > 0
                ? colors.warning
                : colors.success,
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  const _StatCard(
      {required this.label,
      required this.value,
      required this.icon,
      required this.color});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value,
                  style: TextStyle(
                      color: color,
                      fontSize: 24,
                      fontWeight: FontWeight.bold)),
              Text(label,
                  style: TextStyle(
                      color: colors.textMuted, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Section header ────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;
  const _SectionHeader({required this.title, required this.icon});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: [
        Icon(icon, color: colors.accent, size: 18),
        const SizedBox(width: 8),
        Text(title,
            style: TextStyle(
                color: colors.text,
                fontWeight: FontWeight.w600,
                fontSize: 16)),
      ],
    );
  }
}

// ── État vide athlètes ────────────────────────────────────────────────────────

class _EmptyAthletes extends StatelessWidget {
  const _EmptyAthletes();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(Icons.group_off_rounded, color: colors.textMuted, size: 48),
          const SizedBox(height: 12),
          Text('Aucun athlète',
              style: TextStyle(color: colors.text, fontSize: 16)),
          const SizedBox(height: 4),
          Text(
            'Appuyez sur + pour ajouter votre premier athlète.',
            textAlign: TextAlign.center,
            style: TextStyle(color: colors.textMuted, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

// ── Vue pas de profil coach ───────────────────────────────────────────────────

class _NoProfileView extends StatelessWidget {
  final WidgetRef ref;
  const _NoProfileView({required this.ref});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final nameController = TextEditingController();

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.sports_rounded,
                color: colors.accent, size: 64),
            const SizedBox(height: 16),
            Text('Créer votre profil coach',
                style: TextStyle(
                    color: colors.text,
                    fontSize: 20,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(
              'Définissez votre profil pour accéder au dashboard coach et suivre vos athlètes.',
              textAlign: TextAlign.center,
              style: TextStyle(color: colors.textMuted, fontSize: 14),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: nameController,
              style: TextStyle(color: colors.text),
              decoration: InputDecoration(
                labelText: 'Votre nom',
                labelStyle: TextStyle(color: colors.textMuted),
                enabledBorder: OutlineInputBorder(
                  borderSide: BorderSide(color: colors.textMuted),
                ),
                focusedBorder: OutlineInputBorder(
                  borderSide: BorderSide(color: colors.accent),
                ),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                  backgroundColor: colors.accent,
                  foregroundColor: Colors.black,
                  minimumSize: const Size(double.infinity, 48)),
              onPressed: () {
                if (nameController.text.trim().isEmpty) return;
                ref.read(coachDashboardProvider.notifier).createOrUpdateCoachProfile(
                      CoachProfileCreate(name: nameController.text.trim()),
                    );
              },
              child: const Text('Créer mon profil'),
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
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, color: colors.danger, size: 48),
            const SizedBox(height: 12),
            Text('Impossible de charger le dashboard',
                style: TextStyle(color: colors.text, fontSize: 16)),
            const SizedBox(height: 8),
            Text(message,
                style: TextStyle(
                    color: colors.textMuted, fontSize: 12),
                textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRetry,
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}

// ── TextField dialogue ────────────────────────────────────────────────────────

class _DialogTextField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final bool required;
  const _DialogTextField({
    required this.controller,
    required this.label,
    this.required = true,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return TextField(
      controller: controller,
      style: TextStyle(color: colors.text),
      decoration: InputDecoration(
        labelText: required ? label : '$label (optionnel)',
        labelStyle: TextStyle(color: colors.textMuted),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(color: colors.textMuted),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: BorderSide(color: colors.accent),
        ),
      ),
    );
  }
}
