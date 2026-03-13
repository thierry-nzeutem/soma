/// Écran Sommeil — saisie session + historique récent (LOT 6).
///
/// Formulaire : heure coucher, heure réveil, qualité perçue (1–5).
/// Liste des 14 dernières sessions.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/sleep_log.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'sleep_notifier.dart';

class SleepScreen extends ConsumerStatefulWidget {
  const SleepScreen({super.key});

  @override
  ConsumerState<SleepScreen> createState() => _SleepScreenState();
}

class _SleepScreenState extends ConsumerState<SleepScreen> {
  TimeOfDay? _bedtime;
  TimeOfDay? _wakeTime;
  int _quality = 3;
  final _notesController = TextEditingController();
  bool _isSaving = false;

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    final sessionsState = ref.watch(sleepProvider);

    return Scaffold(
      backgroundColor: colors.background,
      appBar: SomaAppBar(
        title: 'Sommeil',
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.accent),
            onPressed: () => ref.read(sleepProvider.notifier).refresh(),
            tooltip: 'Actualiser',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // ── Formulaire saisie ──
          _SectionHeader(
            icon: Icons.add_circle_outline_rounded,
            label: 'Enregistrer une nuit',
          ),
          const SizedBox(height: 12),
          _TimePickerRow(
            label: 'Coucher',
            icon: Icons.bedtime_rounded,
            time: _bedtime,
            onTap: () => _pickTime(context, isBedtime: true),
          ),
          const SizedBox(height: 8),
          _TimePickerRow(
            label: 'Réveil',
            icon: Icons.wb_sunny_rounded,
            time: _wakeTime,
            onTap: () => _pickTime(context, isBedtime: false),
          ),
          const SizedBox(height: 16),

          // Qualité
          Row(
            children: [
              const Icon(Icons.star_rounded, color: Color(0xFF9B72CF), size: 18),
              const SizedBox(width: 8),
              Text(
                'Qualité perçue',
                style: TextStyle(color: colors.textMuted, fontSize: 13),
              ),
              const Spacer(),
              _QualitySelector(
                value: _quality,
                onChanged: (v) => setState(() => _quality = v),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Notes
          TextField(
            controller: _notesController,
            style: TextStyle(color: colors.text, fontSize: 14),
            decoration: InputDecoration(
              hintText: 'Notes (optionnel)',
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
                borderSide: const BorderSide(color: Color(0xFF9B72CF)),
              ),
            ),
            maxLines: 2,
          ),
          const SizedBox(height: 16),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _canSave && !_isSaving ? _save : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF9B72CF),
                foregroundColor: Colors.white,
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
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Enregistrer',
                      style: TextStyle(fontSize: 15)),
            ),
          ),
          const SizedBox(height: 32),

          // ── Historique ──
          _SectionHeader(
            icon: Icons.history_rounded,
            label: 'Historique récent',
          ),
          const SizedBox(height: 12),
          sessionsState.when(
            loading: () => const Center(
              child:
                  CircularProgressIndicator(color: Color(0xFF9B72CF)),
            ),
            error: (err, _) => Text(
              'Erreur : $err',
              style: TextStyle(color: colors.danger),
            ),
            data: (sessions) => sessions.isEmpty
                ? const _EmptyState()
                : Column(
                    children:
                        sessions.map((s) => _SleepSessionRow(s)).toList(),
                  ),
          ),
        ],
      ),
    );
  }

  bool get _canSave => _bedtime != null && _wakeTime != null;

  Future<void> _pickTime(
    BuildContext context, {
    required bool isBedtime,
  }) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: isBedtime
          ? const TimeOfDay(hour: 22, minute: 30)
          : const TimeOfDay(hour: 7, minute: 0),
      builder: (ctx, child) => Theme(
        data: ThemeData.dark().copyWith(
          colorScheme: const ColorScheme.dark(
            primary: Color(0xFF9B72CF),
            surface: Color(0xFF141414),
          ),
        ),
        child: child!,
      ),
    );
    if (picked != null) {
      setState(() {
        if (isBedtime) {
          _bedtime = picked;
        } else {
          _wakeTime = picked;
        }
      });
    }
  }

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      final now = DateTime.now();
      // Construire les DateTimes pour coucher et réveil
      final bedDate = DateTime(now.year, now.month, now.day - 1,
          _bedtime!.hour, _bedtime!.minute);
      final wakeDate = DateTime(
          now.year, now.month, now.day, _wakeTime!.hour, _wakeTime!.minute);
      // Si l'heure de réveil est avant le coucher (nuit passée)
      final start = bedDate.toIso8601String();
      final end = wakeDate.isBefore(bedDate)
          ? wakeDate.add(const Duration(days: 1)).toIso8601String()
          : wakeDate.toIso8601String();

      await ref.read(sleepProvider.notifier).logSleep(
            startAt: start,
            endAt: end,
            perceivedQuality: _quality,
            notes: _notesController.text.trim(),
          );
      if (mounted) {
        setState(() {
          _bedtime = null;
          _wakeTime = null;
          _quality = 3;
          _notesController.clear();
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Nuit enregistrée'),
            backgroundColor: Color(0xFF9B72CF),
          ),
        );
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

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String label;

  const _SectionHeader({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: [
        Icon(icon, size: 16, color: const Color(0xFF9B72CF)),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            color: colors.textMuted,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _TimePickerRow extends StatelessWidget {
  final String label;
  final IconData icon;
  final TimeOfDay? time;
  final VoidCallback onTap;

  const _TimePickerRow({
    required this.label,
    required this.icon,
    required this.time,
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
              Icon(icon, color: const Color(0xFF9B72CF), size: 20),
              const SizedBox(width: 12),
              Text(
                label,
                style: TextStyle(color: colors.textMuted, fontSize: 14),
              ),
              const Spacer(),
              Text(
                time != null
                    ? '${time!.hour.toString().padLeft(2, '0')}:${time!.minute.toString().padLeft(2, '0')}'
                    : 'Choisir',
                style: TextStyle(
                  color: time != null
                      ? colors.text
                      : colors.textMuted,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 8),
              Icon(Icons.access_time_rounded,
                  size: 16, color: colors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}

class _QualitySelector extends StatelessWidget {
  final int value;
  final ValueChanged<int> onChanged;

  const _QualitySelector({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Row(
      children: List.generate(5, (i) {
        final star = i + 1;
        return GestureDetector(
          onTap: () => onChanged(star),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2),
            child: Icon(
              Icons.star_rounded,
              size: 26,
              color: star <= value
                  ? const Color(0xFF9B72CF)
                  : colors.border,
            ),
          ),
        );
      }),
    );
  }
}

class _SleepSessionRow extends StatelessWidget {
  final SleepSession session;

  const _SleepSessionRow(this.session);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Text(session.qualityEmoji, style: const TextStyle(fontSize: 22)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  session.durationLabel,
                  style: TextStyle(
                    color: colors.text,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  session.qualityLabel,
                  style: TextStyle(
                    color: colors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Text(
            session.startAt.substring(0, 10),
            style: TextStyle(color: colors.textMuted, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.bedtime_outlined, size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Aucune session enregistrée',
              style: TextStyle(color: colors.textSecondary, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
