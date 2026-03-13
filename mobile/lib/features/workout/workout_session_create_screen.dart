/// Écran Création Session — formulaire type/lieu/datetime (LOT 6).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'workout_notifier.dart';

class WorkoutSessionCreateScreen extends ConsumerStatefulWidget {
  const WorkoutSessionCreateScreen({super.key});

  @override
  ConsumerState<WorkoutSessionCreateScreen> createState() =>
      _WorkoutSessionCreateScreenState();
}

class _WorkoutSessionCreateScreenState
    extends ConsumerState<WorkoutSessionCreateScreen> {
  String _sessionType = 'strength';
  String _location = 'gym';
  DateTime _startedAt = DateTime.now();
  bool _isSaving = false;

  static const _types = [
    ('strength', 'Force', Icons.fitness_center_rounded),
    ('cardio', 'Cardio', Icons.directions_run_rounded),
    ('hiit', 'HIIT', Icons.flash_on_rounded),
    ('flexibility', 'Flexibilité', Icons.self_improvement_rounded),
    ('sport', 'Sport', Icons.sports_rounded),
    ('other', 'Autre', Icons.more_horiz_rounded),
  ];

  static const _locations = [
    ('gym', 'Salle'),
    ('home', 'Maison'),
    ('outdoor', 'Extérieur'),
  ];

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Nouvelle séance'),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Type
          _Label('Type de séance'),
          const SizedBox(height: 10),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            childAspectRatio: 1.4,
            children: _types.map((t) {
              final isSelected = t.$1 == _sessionType;
              return GestureDetector(
                onTap: () => setState(() => _sessionType = t.$1),
                child: Container(
                  decoration: BoxDecoration(
                    color: isSelected
                        ? const Color(0xFFFFB347).withOpacity(0.12)
                        : colors.surface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isSelected
                          ? const Color(0xFFFFB347)
                          : colors.border,
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        t.$3,
                        color: isSelected
                            ? const Color(0xFFFFB347)
                            : colors.textMuted,
                        size: 22,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        t.$2,
                        style: TextStyle(
                          color: isSelected
                              ? const Color(0xFFFFB347)
                              : colors.textMuted,
                          fontSize: 12,
                          fontWeight: isSelected
                              ? FontWeight.w600
                              : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),

          // Lieu
          _Label('Lieu'),
          const SizedBox(height: 10),
          Row(
            children: _locations.map((l) {
              final isSelected = l.$1 == _location;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _location = l.$1),
                  child: Container(
                    margin:
                        const EdgeInsets.symmetric(horizontal: 4),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? const Color(0xFFFFB347).withOpacity(0.12)
                          : colors.surface,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: isSelected
                            ? const Color(0xFFFFB347)
                            : colors.border,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        l.$2,
                        style: TextStyle(
                          color: isSelected
                              ? const Color(0xFFFFB347)
                              : colors.textMuted,
                          fontSize: 13,
                          fontWeight: isSelected
                              ? FontWeight.w600
                              : FontWeight.normal,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),

          // Date/heure
          _Label("Date et heure de début"),
          Material(
            color: colors.surface,
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              onTap: _pickDateTime,
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: colors.border),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.schedule_rounded,
                        color: Color(0xFFFFB347), size: 20),
                    const SizedBox(width: 12),
                    Text(
                      _formatDateTime(_startedAt),
                      style: TextStyle(
                          color: colors.text, fontSize: 14),
                    ),
                    const Spacer(),
                    Icon(Icons.chevron_right_rounded,
                        color: colors.textMuted, size: 18),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 36),

          // Bouton créer
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _create,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFFB347),
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
              child: _isSaving
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.black),
                    )
                  : const Text('Démarrer la séance',
                      style: TextStyle(
                          fontSize: 15, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    final date = '${dt.day.toString().padLeft(2, '0')}/'
        '${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    final time = '${dt.hour.toString().padLeft(2, '0')}:'
        '${dt.minute.toString().padLeft(2, '0')}';
    return '$date · $time';
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _startedAt,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now().add(const Duration(days: 1)),
      builder: (ctx, child) => Theme(
        data: ThemeData.dark().copyWith(
          colorScheme: const ColorScheme.dark(
              primary: Color(0xFFFFB347),
              surface: Color(0xFF141414)),
        ),
        child: child!,
      ),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_startedAt),
      builder: (ctx, child) => Theme(
        data: ThemeData.dark().copyWith(
          colorScheme: const ColorScheme.dark(
              primary: Color(0xFFFFB347),
              surface: Color(0xFF141414)),
        ),
        child: child!,
      ),
    );
    if (time == null || !mounted) return;
    setState(() {
      _startedAt = DateTime(
          date.year, date.month, date.day, time.hour, time.minute);
    });
  }

  Future<void> _create() async {
    setState(() => _isSaving = true);
    try {
      final sessionId = await ref
          .read(workoutSessionsProvider.notifier)
          .createSession({
        'session_type': _sessionType,
        'location': _location,
        'started_at': _startedAt.toIso8601String(),
        'status': 'in_progress',
      });
      if (sessionId != null && mounted) {
        context.pushReplacement('/journal/workout/$sessionId');
      } else if (mounted) {
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: context.somaColors.danger,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }
}

class _Label extends StatelessWidget {
  final String text;

  const _Label(this.text);

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;
    return Text(
      text,
      style: TextStyle(
        color: colors.textMuted,
        fontSize: 12,
        fontWeight: FontWeight.w600,
      ),
    );
  }
}
