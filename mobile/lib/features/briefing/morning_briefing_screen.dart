/// Morning Briefing Screen — LOT 18.
///
/// Écran principal quotidien SOMA : agrège readiness, sommeil, entraînement,
/// nutrition, hydratation, jumeau numérique, alertes et conseils coach.
///
/// Layout :
///   SomaAppBar + date
///   ReadinessGauge 140px (centré)
///   _SleepCard
///   _TrainingCard
///   _NutritionCard
///   _HydrationCard
///   _TwinCard → CTA /twin
///   AlertBanner × N
///   InsightCard (top_insight)
///   CoachTipCard → CTA /coach
///   _BottomCTAs (Journal rapide | Coach | Workout)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/daily_briefing.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/alert_banner.dart';
import '../../shared/widgets/coach_tip_card.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/insight_card.dart';
import '../../shared/widgets/readiness_gauge.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'briefing_notifier.dart';
import '../../core/subscription/plan_models.dart';
import '../../widgets/upgrade_gate.dart';
import '../../core/analytics/analytics_service.dart';  // LOT 19
import '../../core/api/api_client.dart';               // LOT 19

// ── Constantes UI ─────────────────────────────────────────────────────────────

const _kCardRadius = 16.0;
const _kPadH = 16.0;

// ── Screen ────────────────────────────────────────────────────────────────────

class MorningBriefingScreen extends ConsumerWidget {
  const MorningBriefingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return UpgradeGate(
      feature: FeatureCode.dailyBriefing,
      child: _buildBriefingContent(context, ref),
    );
  }

  Widget _buildBriefingContent(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final briefingAsync = ref.watch(briefingProvider);

    return Scaffold(
      backgroundColor: colors.navBackground,
      appBar: SomaAppBar(
        title: 'Briefing du matin',
        showBackButton: true,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: colors.textSecondary),
            tooltip: 'Rafraîchir',
            onPressed: () => ref.read(briefingProvider.notifier).refresh(),
          ),
        ],
      ),
      body: briefingAsync.when(
        loading: () => Center(
          child: CircularProgressIndicator(color: colors.accent),
        ),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.cloud_off_rounded,
                    color: colors.textSecondary, size: 48),
                const SizedBox(height: 16),
                Text(
                  'Impossible de charger le briefing',
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 17,
                      fontWeight: FontWeight.w600),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Vérifiez votre connexion et réessayez.',
                  style: TextStyle(color: colors.textSecondary, fontSize: 14),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: colors.accent,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                  onPressed: () =>
                      ref.read(briefingProvider.notifier).refresh(),
                  icon: const Icon(Icons.refresh_rounded),
                  label: const Text('Réessayer'),
                ),
              ],
            ),
          ),
        ),
        data: (briefing) {
          if (briefing == null) {
            return EmptyState(
              icon: Icons.wb_sunny_outlined,
              title: 'Briefing indisponible',
              subtitle:
                  'Commencez à logger vos données pour recevoir votre briefing personnalisé dès demain.',
              action: () => context.go('/quick-journal'),
              actionLabel: 'Journal rapide',
            );
          }
          // LOT 19 : track briefing opened (fire-and-forget, post-frame).
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (context.mounted) {
              AnalyticsService.track(
                ref.read(apiClientProvider),
                AnalyticsEvents.briefingOpened,
              );
            }
          });
          return _BriefingContent(briefing: briefing);
        },
      ),
    );
  }
}

// ── Contenu principal ─────────────────────────────────────────────────────────

class _BriefingContent extends StatelessWidget {
  const _BriefingContent({required this.briefing});

  final DailyBriefing briefing;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(
          horizontal: _kPadH, vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Date du briefing
          _DateHeader(dateStr: briefing.briefingDate),
          const SizedBox(height: 20),

          // ── Readiness Gauge ─────────────────────────────────────────────
          Center(
            child: ReadinessGauge(
              score: briefing.readinessScore ?? 50,
              size: 140,
              label: 'Récupération',
            ),
          ),
          const SizedBox(height: 24),

          // ── Carte Sommeil ────────────────────────────────────────────────
          if (briefing.hasSleep) ...[
            _SleepCard(briefing: briefing),
            const SizedBox(height: 12),
          ],

          // ── Carte Entraînement ────────────────────────────────────────────
          _TrainingCard(briefing: briefing),
          const SizedBox(height: 12),

          // ── Carte Nutrition ──────────────────────────────────────────────
          if (briefing.hasNutrition) ...[
            _NutritionCard(briefing: briefing),
            const SizedBox(height: 12),
          ],

          // ── Carte Hydratation ─────────────────────────────────────────────
          if (briefing.hydrationTargetMl != null) ...[
            _HydrationCard(briefing: briefing),
            const SizedBox(height: 12),
          ],

          // ── Carte Jumeau Numérique ────────────────────────────────────────
          if (briefing.twinStatus != null) ...[
            _TwinCard(briefing: briefing),
            const SizedBox(height: 12),
          ],

          // ── Alertes ───────────────────────────────────────────────────────
          if (briefing.alerts.isNotEmpty) ...[
            const SizedBox(height: 4),
            ...briefing.alerts.map(
              (alert) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: AlertBanner(
                  message: alert,
                  severity: 'warning',
                ),
              ),
            ),
            const SizedBox(height: 4),
          ],

          // ── Top Insight ───────────────────────────────────────────────────
          if (briefing.topInsight != null) ...[
            InsightCard(
              message: briefing.topInsight!,
              severity: 'info',
              category: 'Insight du jour',
            ),
            const SizedBox(height: 12),
          ],

          // ── Conseil Coach ─────────────────────────────────────────────────
          if (briefing.coachTip != null) ...[
            CoachTipCard(
              tip: briefing.coachTip!,
              ctaLabel: 'Demander au coach',
              onCta: () => context.go('/coach'),
            ),
            const SizedBox(height: 12),
          ],

          // ── CTAs bas de page ──────────────────────────────────────────────
          const SizedBox(height: 8),
          const _BottomCTAs(),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

// ── En-tête date ──────────────────────────────────────────────────────────────

class _DateHeader extends StatelessWidget {
  const _DateHeader({required this.dateStr});
  final String dateStr;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final label = _formatDate(dateStr);
    return Text(
      label,
      textAlign: TextAlign.center,
      style: TextStyle(
        color: colors.textSecondary,
        fontSize: 14,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.3,
      ),
    );
  }

  /// Formate "2026-03-08" → "Dimanche 8 mars 2026".
  static String _formatDate(String iso) {
    try {
      final date = DateTime.parse(iso);
      const weekdays = [
        'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'
      ];
      const months = [
        '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
      ];
      final day = weekdays[date.weekday - 1];
      final month = months[date.month];
      return '$day ${date.day} $month ${date.year}';
    } catch (_) {
      return iso;
    }
  }
}

// ── Carte Sommeil ─────────────────────────────────────────────────────────────

class _SleepCard extends StatelessWidget {
  const _SleepCard({required this.briefing});
  final DailyBriefing briefing;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final hours = briefing.sleepDurationH ?? 0;
    final h = hours.floor();
    final min = ((hours - h) * 60).round();
    final durationLabel = h > 0 ? '${h}h${min > 0 ? "${min}min" : ""}' : '—';

    return _SomaCard(
      child: Row(
        children: [
          _CardIcon(icon: Icons.bedtime_rounded, color: const Color(0xFF5E5CE6)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Sommeil',
                    style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 13,
                        fontWeight: FontWeight.w500)),
                const SizedBox(height: 4),
                Text(durationLabel,
                    style: TextStyle(
                        color: colors.text,
                        fontSize: 22,
                        fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          if (briefing.sleepQualityLabel != null)
            _QualityBadge(label: briefing.sleepQualityDisplayLabel),
        ],
      ),
    );
  }
}

// ── Carte Entraînement ────────────────────────────────────────────────────────

class _TrainingCard extends StatelessWidget {
  const _TrainingCard({required this.briefing});
  final DailyBriefing briefing;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final isRest = briefing.trainingType == 'rest' ||
        briefing.trainingType == null;

    return _SomaCard(
      child: Row(
        children: [
          _CardIcon(
            icon: isRest
                ? Icons.self_improvement_rounded
                : Icons.fitness_center_rounded,
            color: isRest
                ? colors.success
                : colors.warning,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Entraînement recommandé',
                    style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 13,
                        fontWeight: FontWeight.w500)),
                const SizedBox(height: 4),
                Text(
                  briefing.trainingTypeLabel,
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 18,
                      fontWeight: FontWeight.w700),
                ),
                if (!isRest && briefing.trainingIntensity != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    '${briefing.intensityLabel}'
                    '${briefing.trainingDurationMin != null ? " · ${briefing.trainingDurationMin} min" : ""}',
                    style: TextStyle(
                        color: colors.textSecondary, fontSize: 13),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Carte Nutrition ───────────────────────────────────────────────────────────

class _NutritionCard extends StatelessWidget {
  const _NutritionCard({required this.briefing});
  final DailyBriefing briefing;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return _SomaCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _CardIcon(
                  icon: Icons.restaurant_rounded,
                  color: colors.warning),
              const SizedBox(width: 12),
              Text('Nutrition',
                  style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _MacroItem(
                label: 'Calories',
                value: briefing.calorieTarget != null
                    ? '${briefing.calorieTarget!.toStringAsFixed(0)} kcal'
                    : '—',
                color: colors.warning,
              ),
              _MacroItem(
                label: 'Protéines',
                value: briefing.proteinTargetG != null
                    ? '${briefing.proteinTargetG!.toStringAsFixed(0)} g'
                    : '—',
                color: const Color(0xFF0A84FF),
              ),
              _MacroItem(
                label: 'Glucides',
                value: briefing.carbTargetG != null
                    ? '${briefing.carbTargetG!.toStringAsFixed(0)} g'
                    : '—',
                color: const Color(0xFF30D158),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Carte Hydratation ─────────────────────────────────────────────────────────

class _HydrationCard extends StatelessWidget {
  const _HydrationCard({required this.briefing});
  final DailyBriefing briefing;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final ml = briefing.hydrationTargetMl ?? 0;
    final liters = ml / 1000;

    return _SomaCard(
      child: Row(
        children: [
          _CardIcon(
              icon: Icons.water_drop_rounded,
              color: const Color(0xFF0A84FF)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Hydratation',
                    style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 13,
                        fontWeight: FontWeight.w500)),
                const SizedBox(height: 4),
                Text(
                  '${liters.toStringAsFixed(1)} L  /  $ml mL',
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 18,
                      fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
          const Icon(Icons.local_drink_rounded,
              color: Color(0xFF0A84FF), size: 24),
        ],
      ),
    );
  }
}

// ── Carte Jumeau Numérique ────────────────────────────────────────────────────

class _TwinCard extends StatelessWidget {
  const _TwinCard({required this.briefing});
  final DailyBriefing briefing;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final statusColor = _twinColor(context, briefing.twinStatus);

    return GestureDetector(
      onTap: () => context.go('/twin'),
      child: _SomaCard(
        child: Row(
          children: [
            _CardIcon(
                icon: Icons.bubble_chart_rounded,
                color: statusColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Jumeau Numérique',
                      style: TextStyle(
                          color: colors.textSecondary,
                          fontSize: 13,
                          fontWeight: FontWeight.w500)),
                  const SizedBox(height: 4),
                  Text(
                    briefing.twinStatusLabel,
                    style: TextStyle(
                        color: statusColor,
                        fontSize: 18,
                        fontWeight: FontWeight.w700),
                  ),
                  if (briefing.twinPrimaryConcern != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      briefing.twinPrimaryConcern!,
                      style: TextStyle(
                          color: colors.textSecondary, fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded,
                color: colors.textSecondary, size: 20),
          ],
        ),
      ),
    );
  }

  static Color _twinColor(BuildContext context, String? status) {
    final colors = context.somaColors;
    return switch (status) {
      'fresh' => colors.success,
      'good' => const Color(0xFF30D158),
      'moderate' => colors.warning,
      'tired' => const Color(0xFFFF6B35),
      'critical' => colors.danger,
      _ => colors.textSecondary,
    };
  }
}

// ── CTAs bas de page ──────────────────────────────────────────────────────────

// LOT 19 : converti en ConsumerWidget pour tracker les clics CTA.
class _BottomCTAs extends ConsumerWidget {
  const _BottomCTAs();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final client = ref.read(apiClientProvider);
    return Column(
      children: [
        Divider(color: colors.border, height: 1),
        const SizedBox(height: 16),
        Text(
          'Actions rapides',
          style: TextStyle(
              color: colors.textSecondary,
              fontSize: 13,
              fontWeight: FontWeight.w500),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _CtaButton(
                icon: Icons.bolt_rounded,
                label: 'Journal',
                onTap: () {
                  AnalyticsService.track(
                    client, AnalyticsEvents.briefingCtaClick,
                    props: {'cta': 'journal'},
                  );
                  context.go('/quick-journal');
                },
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _CtaButton(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'Coach',
                onTap: () {
                  AnalyticsService.track(
                    client, AnalyticsEvents.briefingCtaClick,
                    props: {'cta': 'coach'},
                  );
                  context.go('/coach');
                },
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _CtaButton(
                icon: Icons.fitness_center_rounded,
                label: 'Workout',
                onTap: () {
                  AnalyticsService.track(
                    client, AnalyticsEvents.briefingCtaClick,
                    props: {'cta': 'workout'},
                  );
                  context.go('/journal/workout');
                },
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _CtaButton extends StatelessWidget {
  const _CtaButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: colors.surfaceVariant,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: colors.border),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: colors.accent, size: 22),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                  color: colors.text,
                  fontSize: 12,
                  fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Widgets helpers ───────────────────────────────────────────────────────────

/// Conteneur carte SOMA uniforme.
class _SomaCard extends StatelessWidget {
  const _SomaCard({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surfaceVariant,
        borderRadius: BorderRadius.circular(_kCardRadius),
        border: Border.all(color: colors.border),
      ),
      child: child,
    );
  }
}

/// Icône ronde colorée dans une carte.
class _CardIcon extends StatelessWidget {
  const _CardIcon({required this.icon, required this.color});
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }
}

/// Badge qualité (Excellent/Bon/Correct/Mauvais).
class _QualityBadge extends StatelessWidget {
  const _QualityBadge({required this.label});
  final String label;

  Color _color(BuildContext context) {
    final colors = context.somaColors;
    return switch (label.toLowerCase()) {
      'excellente' => colors.success,
      'bonne' => const Color(0xFF30D158),
      'correcte' => colors.warning,
      'mauvaise' => colors.danger,
      _ => colors.textSecondary,
    };
  }

  @override
  Widget build(BuildContext context) {
    final c = _color(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: c.withAlpha(30),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: c.withAlpha(80)),
      ),
      child: Text(
        label,
        style: TextStyle(color: c, fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }
}

/// Item macro-nutriment (label + valeur + barre de couleur).
class _MacroItem extends StatelessWidget {
  const _MacroItem({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 4,
          height: 24,
          margin: const EdgeInsets.only(bottom: 8),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        Text(
          value,
          style: TextStyle(
              color: colors.text, fontSize: 15, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(color: colors.textSecondary, fontSize: 12),
        ),
      ],
    );
  }
}
