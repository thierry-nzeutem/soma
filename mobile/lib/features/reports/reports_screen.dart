/// ReportsScreen - Telechargement de rapport PDF de sante SOMA.
///
/// Permet de selectionner une periode et de telecharger un rapport PDF.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import '../../core/subscription/plan_models.dart';
import '../../widgets/upgrade_gate.dart';

// -- Period options ---------------------------------------------------------

const _kPeriods = <(String, String)>[
  ('Last week', 'last_week'),
  ('Last month', 'last_month'),
  ('Last quarter', 'last_quarter'),
];

// -- Screen -----------------------------------------------------------------

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  int _periodIndex = 0;
  bool _loading = false;

  String get _period => _kPeriods[_periodIndex].$2;

  Future<void> _downloadReport() async {
    setState(() => _loading = true);
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.get<dynamic>(
        ApiConstants.healthReport,
        queryParameters: {'period': _period},
      );
      final raw = response.data;
      final List<int> bytes;
      if (raw is List<int>) {
        bytes = raw;
      } else if (raw is List) {
        bytes = raw.cast<int>();
      } else {
        bytes = [];
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Report downloaded (${bytes.length} bytes)'),
          backgroundColor: const Color(0xFF34C759),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: const Color(0xFFFF3B30),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return UpgradeGate(
      feature: FeatureCode.pdfReports,
      child: _buildReportsContent(context),
    );
  }

  Widget _buildReportsContent(BuildContext context) {
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(title: 'Health Report'),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
        children: [
          // -- Info text -----------------------------------------------------
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: colors.info.withOpacity(0.08),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: colors.info.withOpacity(0.25)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline_rounded,
                    color: colors.info, size: 22),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Your personalized health report includes body composition, '
                    'sleep, hydration, and activity data for the selected period.',
                    style: TextStyle(
                      color: colors.text,
                      fontSize: 13,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 28),

          // -- Period selector -----------------------------------------------
          Text(
            'Select period',
            style: TextStyle(
              color: colors.textMuted,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          ..._kPeriods.asMap().entries.map((entry) {
            final i = entry.key;
            final label = entry.value.$1;
            final isSelected = i == _periodIndex;
            return GestureDetector(
              onTap: () => setState(() => _periodIndex = i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 160),
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: isSelected
                      ? colors.accent.withOpacity(0.1)
                      : colors.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected ? colors.accent : colors.border,
                    width: isSelected ? 1.5 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      isSelected
                          ? Icons.radio_button_checked_rounded
                          : Icons.radio_button_off_rounded,
                      color: isSelected ? colors.accent : colors.textMuted,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Text(
                      label,
                      style: TextStyle(
                        color: isSelected
                            ? colors.text
                            : colors.textSecondary,
                        fontSize: 15,
                        fontWeight: isSelected
                            ? FontWeight.w600
                            : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
          const SizedBox(height: 32),

          // -- Download button -----------------------------------------------
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _loading ? null : _downloadReport,
              icon: _loading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.black,
                      ),
                    )
                  : const Icon(Icons.download_rounded, size: 22),
              label: Text(
                _loading ? 'Downloading...' : 'Download PDF',
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: Colors.black,
                disabledBackgroundColor: colors.accent.withOpacity(0.5),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                elevation: 0,
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
