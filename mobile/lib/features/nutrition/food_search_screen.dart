/// Ecran Recherche aliment — barre de recherche + liste resultats (LOT 6).
///
/// Tape -> FoodSearchNotifier -> resultats -> selection -> pop avec FoodItem.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/nutrition.dart';
import '../../core/theme/theme_extensions.dart';
import '../../shared/widgets/soma_app_bar.dart';
import 'nutrition_notifier.dart';

class FoodSearchScreen extends ConsumerStatefulWidget {
  const FoodSearchScreen({super.key});

  @override
  ConsumerState<FoodSearchScreen> createState() => _FoodSearchScreenState();
}

class _FoodSearchScreenState extends ConsumerState<FoodSearchScreen> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(foodSearchProvider);
    final colors = context.somaColors;

    return Scaffold(
      backgroundColor: colors.background,
      appBar: const SomaAppBar(title: 'Rechercher un aliment'),
      body: Column(
        children: [
          // Barre de recherche
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchCtrl,
              autofocus: true,
              style: TextStyle(color: colors.text, fontSize: 14),
              onChanged: (q) =>
                  ref.read(foodSearchProvider.notifier).search(q),
              decoration: InputDecoration(
                hintText: 'Nom de l\'aliment...',
                hintStyle:
                    TextStyle(color: colors.textMuted),
                prefixIcon: Icon(Icons.search_rounded,
                    color: colors.textMuted),
                suffixIcon: state.query.isNotEmpty
                    ? GestureDetector(
                        onTap: () {
                          _searchCtrl.clear();
                          ref.read(foodSearchProvider.notifier).clear();
                        },
                        child: Icon(Icons.close_rounded,
                            color: colors.textMuted),
                      )
                    : null,
                filled: true,
                fillColor: colors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide:
                      const BorderSide(color: Color(0xFFFFB347)),
                ),
                contentPadding:
                    const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),

          // Resultats
          Expanded(
            child: _ResultsList(state: state),
          ),
        ],
      ),
    );
  }
}

class _ResultsList extends StatelessWidget {
  final FoodSearchState state;

  const _ResultsList({required this.state});

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    if (state.isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFFFFB347)),
      );
    }
    if (state.error != null) {
      return Center(
        child: Text(
          'Erreur : ${state.error}',
          style: TextStyle(color: colors.danger, fontSize: 13),
        ),
      );
    }
    if (state.query.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_rounded, size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Tapez pour rechercher',
              style: TextStyle(color: colors.textMuted, fontSize: 14),
            ),
          ],
        ),
      );
    }
    if (state.results.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.no_meals_rounded, size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Aucun aliment trouve',
              style: TextStyle(color: colors.textMuted, fontSize: 14),
            ),
          ],
        ),
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      itemCount: state.results.length,
      separatorBuilder: (_, __) => const SizedBox(height: 6),
      itemBuilder: (ctx, i) => _FoodItemRow(
        item: state.results[i],
        onTap: () => Navigator.of(ctx).pop(state.results[i]),
      ),
    );
  }
}

class _FoodItemRow extends StatelessWidget {
  final FoodItem item;
  final VoidCallback onTap;

  const _FoodItemRow({required this.item, required this.onTap});

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
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: colors.border),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.displayName,
                      style: TextStyle(
                        color: colors.text,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (item.foodGroup != null)
                      Text(
                        item.foodGroup!,
                        style: TextStyle(
                          color: colors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${item.caloriesPer100g.toStringAsFixed(0)} kcal',
                    style: const TextStyle(
                      color: Color(0xFFFF6B6B),
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    'pour 100g',
                    style: TextStyle(
                      color: colors.textMuted,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 8),
              const Icon(Icons.add_circle_outline_rounded,
                  color: Color(0xFFFFB347), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
