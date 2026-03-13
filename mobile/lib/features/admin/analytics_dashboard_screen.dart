/// Analytics Dashboard Screen — LOT 19.
///
/// Dashboard interne pour piloter SOMA par les données.
/// Accessible via /admin/analytics (réservé aux utilisateurs admin).
///
/// Sections :
///   Résumé (DAU / WAU / MAU / ratio / onboarding rate)
///   Top Fonctionnalités (feature usage heatmap)
///   Funnel Onboarding (5 étapes avec taux de conversion)
///   Cohortes de Rétention (J1 / J7 / J30)
///   Coach IA Analytics (questions, follow-up rate)
///   Performance API (avg latence par endpoint)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';

// ── Constantes UI ─────────────────────────────────────────────────────────────

const _kCardRadius = 16.0;

// ── Providers ─────────────────────────────────────────────────────────────────

final _analyticsSummaryProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.get(
    ApiConstants.analyticsSummary,
    queryParameters: {'days': 30},
  );
  return Map<String, dynamic>.from(response.data as Map);
});

final _featureUsageProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.get(
    ApiConstants.analyticsFeatures,
    queryParameters: {'days': 30},
  );
  return Map<String, dynamic>.from(response.data as Map);
});

final _funnelProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.get(
    ApiConstants.analyticsFunnelOnboarding,
    queryParameters: {'days': 30},
  );
  return Map<String, dynamic>.from(response.data as Map);
});

final _retentionProvider =
    FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.get(
    ApiConstants.analyticsRetentionCohorts,
    queryParameters: {'max_cohorts': 6},
  );
  return List<dynamic>.from(response.data as List);
});

final _coachAnalyticsProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.get(
    ApiConstants.analyticsCoach,
    queryParameters: {'days': 30},
  );
  return Map<String, dynamic>.from(response.data as Map);
});

final _performanceProvider =
    FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.get(
    ApiConstants.analyticsPerformance,
    queryParameters: {'limit': 10},
  );
  return List<dynamic>.from(response.data as List);
});

// ── Screen ────────────────────────────────────────────────────────────────────

class AnalyticsDashboardScreen extends ConsumerWidget {
  const AnalyticsDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.navBackground,
      appBar: const SomaAppBar(
        title: 'Analytics Dashboard',
        showBackButton: true,
      ),
      body: RefreshIndicator(
        color: colors.accent,
        backgroundColor: colors.surfaceVariant,
        onRefresh: () async {
          ref.invalidate(_analyticsSummaryProvider);
          ref.invalidate(_featureUsageProvider);
          ref.invalidate(_funnelProvider);
          ref.invalidate(_retentionProvider);
          ref.invalidate(_coachAnalyticsProvider);
          ref.invalidate(_performanceProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: const [
            _SummarySection(),
            SizedBox(height: 20),
            _FeatureUsageSection(),
            SizedBox(height: 20),
            _FunnelSection(),
            SizedBox(height: 20),
            _RetentionSection(),
            SizedBox(height: 20),
            _CoachSection(),
            SizedBox(height: 20),
            _PerformanceSection(),
            SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

// ── Section helpers ───────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.icon, required this.title});
  final String icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        '$icon  $title',
        style: TextStyle(
          color: colors.text,
          fontSize: 16,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _DashCard extends StatelessWidget {
  const _DashCard({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      width: double.infinity,
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

class _MetricRow extends StatelessWidget {
  const _MetricRow({required this.label, required this.value, this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(color: colors.textSecondary, fontSize: 14)),
          Text(
            value,
            style: TextStyle(
              color: color ?? colors.text,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

Widget _buildError(BuildContext context, String label) {
  final colors = context.somaColors;
  return Center(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Text('Erreur: $label',
          style: TextStyle(color: colors.danger, fontSize: 13)),
    ),
  );
}

Widget _buildLoading(BuildContext context) {
  final colors = context.somaColors;
  return Center(
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: CircularProgressIndicator(color: colors.accent, strokeWidth: 2),
    ),
  );
}

// ── Résumé ─────────────────────────────────────────────────────────────────────

class _SummarySection extends ConsumerWidget {
  const _SummarySection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final summaryAsync = ref.watch(_analyticsSummaryProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: '📊', title: 'Résumé Produit (30j)'),
        _DashCard(
          child: summaryAsync.when(
            loading: () => _buildLoading(context),
            error: (e, _) => _buildError(context, e.toString()),
            data: (data) => Column(
              children: [
                // Row DAU / WAU / MAU
                Row(
                  children: [
                    _StatBox(
                        label: 'DAU', value: '${data['dau'] ?? 0}',
                        color: colors.accent),
                    _StatBox(
                        label: 'WAU', value: '${data['wau'] ?? 0}',
                        color: colors.info),
                    _StatBox(
                        label: 'MAU', value: '${data['mau'] ?? 0}',
                        color: const Color(0xFF5E5CE6)),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: colors.border, height: 1),
                const SizedBox(height: 12),
                _MetricRow(
                  label: 'Ratio DAU/MAU',
                  value: '${((data['dau_mau_ratio'] as num? ?? 0) * 100).toStringAsFixed(1)}%',
                  color: colors.accent,
                ),
                _MetricRow(
                  label: 'Utilisateurs total',
                  value: '${data['total_users'] ?? 0}',
                ),
                _MetricRow(
                  label: 'Nouveaux (30j)',
                  value: '${data['new_users'] ?? 0}',
                  color: colors.accent,
                ),
                _MetricRow(
                  label: 'Onboarding complété',
                  value: '${data['onboarding_completion_rate'] ?? 0}%',
                  color: (data['onboarding_completion_rate'] as num? ?? 0) >= 70
                      ? colors.accent
                      : colors.warning,
                ),
                _MetricRow(
                  label: 'Briefings ouverts',
                  value: '${data['briefing_opens'] ?? 0}',
                ),
                _MetricRow(
                  label: 'Questions coach',
                  value: '${data['coach_questions'] ?? 0}',
                ),
                _MetricRow(
                  label: 'Entrées journal',
                  value: '${data['journal_entries'] ?? 0}',
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _StatBox extends StatelessWidget {
  const _StatBox({required this.label, required this.value, required this.color});
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
                color: color,
                fontSize: 28,
                fontWeight: FontWeight.w800),
          ),
          Text(label,
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 12)),
        ],
      ),
    );
  }
}

// ── Feature Usage ─────────────────────────────────────────────────────────────

class _FeatureUsageSection extends ConsumerWidget {
  const _FeatureUsageSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final usageAsync = ref.watch(_featureUsageProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: '🔥', title: 'Usage Fonctionnalités (30j)'),
        _DashCard(
          child: usageAsync.when(
            loading: () => _buildLoading(context),
            error: (e, _) => _buildError(context, e.toString()),
            data: (data) {
              final items = [
                ('Briefing matin', data['briefing_views'] ?? 0),
                ('Journal entries', data['journal_entries'] ?? 0),
                ('Questions coach', data['coach_questions'] ?? 0),
                ('Workouts loggés', data['workout_logs'] ?? 0),
                ('Nutrition loggée', data['nutrition_logs'] ?? 0),
                ('Quick advice', data['quick_advice_requests'] ?? 0),
                ('Jumeau numérique', data['twin_views'] ?? 0),
                ('Biomarqueurs', data['biomarker_logs'] ?? 0),
              ];
              final maxVal = items
                  .map((e) => e.$2 as int)
                  .fold(1, (a, b) => a > b ? a : b);

              return Column(
                children: items
                    .map((item) => _FeatureBar(
                          label: item.$1,
                          count: item.$2 as int,
                          max: maxVal,
                        ))
                    .toList(),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _FeatureBar extends StatelessWidget {
  const _FeatureBar({
    required this.label,
    required this.count,
    required this.max,
  });
  final String label;
  final int count;
  final int max;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final ratio = max > 0 ? count / max : 0.0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                  style:
                      TextStyle(color: colors.textSecondary, fontSize: 13)),
              Text('$count',
                  style: TextStyle(
                      color: colors.text,
                      fontSize: 13,
                      fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: ratio.toDouble(),
              backgroundColor: colors.border,
              valueColor: AlwaysStoppedAnimation<Color>(
                ratio > 0.6
                    ? colors.accent
                    : ratio > 0.3
                        ? colors.warning
                        : colors.textSecondary,
              ),
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Funnel ────────────────────────────────────────────────────────────────────

class _FunnelSection extends ConsumerWidget {
  const _FunnelSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final funnelAsync = ref.watch(_funnelProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: '🎯', title: 'Funnel Onboarding'),
        _DashCard(
          child: funnelAsync.when(
            loading: () => _buildLoading(context),
            error: (e, _) => _buildError(context, e.toString()),
            data: (data) {
              final steps = (data['steps'] as List?) ?? [];
              final overall = data['overall_conversion_rate'] as num? ?? 0;
              return Column(
                children: [
                  ...steps.map((step) {
                    final s = step as Map;
                    final conv = s['conversion_from_previous'] as num? ?? 0;
                    return _FunnelStepRow(
                      index: s['step_index'] as int? ?? 0,
                      name: s['step_name']?.toString() ?? '',
                      count: s['users_count'] as int? ?? 0,
                      conversion: conv.toDouble(),
                    );
                  }),
                  Divider(color: colors.border, height: 24),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Conversion globale',
                          style: TextStyle(
                              color: colors.textSecondary,
                              fontWeight: FontWeight.w600,
                              fontSize: 14)),
                      Text(
                        '${overall.toStringAsFixed(1)}%',
                        style: TextStyle(
                          color: overall >= 30 ? colors.accent : colors.danger,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

class _FunnelStepRow extends StatelessWidget {
  const _FunnelStepRow({
    required this.index,
    required this.name,
    required this.count,
    required this.conversion,
  });
  final int index;
  final String name;
  final int count;
  final double conversion;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: colors.accent.withAlpha(30),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Center(
              child: Text('$index',
                  style: TextStyle(
                      color: colors.accent,
                      fontSize: 12,
                      fontWeight: FontWeight.w700)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(name,
                style: TextStyle(color: colors.text, fontSize: 13)),
          ),
          Text('$count users',
              style: TextStyle(color: colors.textSecondary, fontSize: 12)),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: (index == 1
                      ? colors.accent
                      : conversion >= 70
                          ? colors.accent
                          : conversion >= 40
                              ? colors.warning
                              : colors.danger)
                  .withAlpha(30),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              index == 1 ? '—' : '${conversion.toStringAsFixed(1)}%',
              style: TextStyle(
                color: index == 1
                    ? colors.textSecondary
                    : conversion >= 70
                        ? colors.accent
                        : conversion >= 40
                            ? colors.warning
                            : colors.danger,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Rétention ─────────────────────────────────────────────────────────────────

class _RetentionSection extends ConsumerWidget {
  const _RetentionSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final retAsync = ref.watch(_retentionProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: '👥', title: 'Cohortes de Rétention'),
        _DashCard(
          child: retAsync.when(
            loading: () => _buildLoading(context),
            error: (e, _) => _buildError(context, e.toString()),
            data: (cohorts) {
              if (cohorts.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text('Pas encore de données de rétention.',
                        style: TextStyle(
                            color: colors.textSecondary, fontSize: 14)),
                  ),
                );
              }
              return Column(
                children: [
                  // En-tête
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        Expanded(
                            flex: 3,
                            child: Text('Semaine',
                                style: TextStyle(
                                    color: colors.textSecondary,
                                    fontSize: 12))),
                        Expanded(
                            child: Text('J+1',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                    color: colors.textSecondary, fontSize: 12))),
                        Expanded(
                            child: Text('J+7',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                    color: colors.textSecondary, fontSize: 12))),
                        Expanded(
                            child: Text('J+30',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                    color: colors.textSecondary, fontSize: 12))),
                      ],
                    ),
                  ),
                  Divider(color: colors.border, height: 1),
                  ...cohorts.map((c) {
                    final cohort = c as Map;
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Row(
                        children: [
                          Expanded(
                              flex: 3,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    cohort['cohort_week']?.toString() ?? '',
                                    style: TextStyle(
                                        color: colors.text,
                                        fontSize: 13,
                                        fontWeight: FontWeight.w600),
                                  ),
                                  Text(
                                    '${cohort['users_count'] ?? 0} users',
                                    style: TextStyle(
                                        color: colors.textSecondary,
                                        fontSize: 11),
                                  ),
                                ],
                              )),
                          _RetCell(
                              value: (cohort['retention_day1'] as num? ?? 0)
                                  .toDouble()),
                          _RetCell(
                              value: (cohort['retention_day7'] as num? ?? 0)
                                  .toDouble()),
                          _RetCell(
                              value: (cohort['retention_day30'] as num? ?? 0)
                                  .toDouble()),
                        ],
                      ),
                    );
                  }),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

class _RetCell extends StatelessWidget {
  const _RetCell({required this.value});
  final double value;

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final cellColor =
        value >= 40 ? colors.accent : value >= 20 ? colors.warning : colors.danger;

    return Expanded(
      child: Text(
        '${value.toStringAsFixed(0)}%',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: cellColor,
          fontSize: 13,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

// ── Coach IA ──────────────────────────────────────────────────────────────────

class _CoachSection extends ConsumerWidget {
  const _CoachSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final coachAsync = ref.watch(_coachAnalyticsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: '🤖', title: 'Coach IA (30j)'),
        _DashCard(
          child: coachAsync.when(
            loading: () => _buildLoading(context),
            error: (e, _) => _buildError(context, e.toString()),
            data: (data) => Column(
              children: [
                _MetricRow(
                  label: 'Questions totales',
                  value: '${data['total_questions'] ?? 0}',
                ),
                _MetricRow(
                  label: 'Quick-advice',
                  value: '${data['total_quick_advice'] ?? 0}',
                ),
                _MetricRow(
                  label: 'Utilisateurs uniques',
                  value: '${data['unique_users_asking'] ?? 0}',
                ),
                _MetricRow(
                  label: 'Questions / utilisateur',
                  value:
                      '${(data['questions_per_active_user'] as num? ?? 0).toStringAsFixed(1)}',
                  color: colors.accent,
                ),
                _MetricRow(
                  label: 'Taux follow-up',
                  value:
                      '${(data['follow_up_rate'] as num? ?? 0).toStringAsFixed(1)}%',
                  color: (data['follow_up_rate'] as num? ?? 0) >= 30
                      ? colors.accent
                      : colors.warning,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

// ── Performance API ───────────────────────────────────────────────────────────

class _PerformanceSection extends ConsumerWidget {
  const _PerformanceSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.somaColors;
    final perfAsync = ref.watch(_performanceProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(icon: '⚡', title: 'Performance API'),
        _DashCard(
          child: perfAsync.when(
            loading: () => _buildLoading(context),
            error: (e, _) => _buildError(context, e.toString()),
            data: (stats) {
              if (stats.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                        'Buffer vide — faites quelques requêtes d\'abord.',
                        style: TextStyle(
                            color: colors.textSecondary, fontSize: 13),
                        textAlign: TextAlign.center),
                  ),
                );
              }
              return Column(
                children: stats.map((s) {
                  final stat = s as Map;
                  final avg = (stat['avg_response_ms'] as num? ?? 0).toDouble();
                  final errorRate =
                      (stat['error_rate'] as num? ?? 0).toDouble();
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                stat['endpoint']?.toString() ?? '',
                                style: TextStyle(
                                    color: colors.text,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500),
                                overflow: TextOverflow.ellipsis,
                              ),
                              Text(
                                '${stat['method']} · ${stat['total_calls']} appels',
                                style: TextStyle(
                                    color: colors.textSecondary, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              '${avg.toStringAsFixed(0)}ms',
                              style: TextStyle(
                                color: avg < 200
                                    ? colors.accent
                                    : avg < 500
                                        ? colors.warning
                                        : colors.danger,
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            if (errorRate > 0)
                              Text(
                                '${errorRate.toStringAsFixed(1)}% err',
                                style:
                                    TextStyle(color: colors.danger, fontSize: 11),
                              ),
                          ],
                        ),
                      ],
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ),
      ],
    );
  }
}
