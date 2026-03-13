/// Notifiers Riverpod — Nutrition (LOT 6).
///
/// NutritionSummaryNotifier : résumé journalier + CRUD entrées
/// FoodSearchNotifier       : recherche aliments dans la base
/// PhotoAnalysisNotifier    : upload photo + polling résultat
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_constants.dart';
import '../../core/models/nutrition.dart';

// ── Résumé journalier ─────────────────────────────────────────────────────────

final nutritionSummaryProvider =
    AsyncNotifierProvider<NutritionSummaryNotifier, DailyNutritionSummary>(
  NutritionSummaryNotifier.new,
);

class NutritionSummaryNotifier
    extends AsyncNotifier<DailyNutritionSummary> {
  @override
  Future<DailyNutritionSummary> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<DailyNutritionSummary> _fetch() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get<Map<String, dynamic>>(
      ApiConstants.nutritionDailySummary,
    );
    return DailyNutritionSummary.fromJson(responseJson(response));
  }

  /// Enregistre une entrée manuelle et recharge le résumé.
  Future<void> addEntry(Map<String, dynamic> payload) async {
    final client = ref.read(apiClientProvider);
    await client.post<void>(ApiConstants.nutritionEntries, data: payload);
    await refresh();
  }

  /// Supprime une entrée nutrition (soft-delete côté backend).
  Future<void> deleteEntry(String entryId) async {
    final client = ref.read(apiClientProvider);
    await client.delete<void>('${ApiConstants.nutritionEntries}/$entryId');
    await refresh();
  }
}

// ── Recherche aliments ────────────────────────────────────────────────────────

/// État de la recherche aliments.
class FoodSearchState {
  final String query;
  final bool isLoading;
  final List<FoodItem> results;
  final String? error;

  const FoodSearchState({
    this.query = '',
    this.isLoading = false,
    this.results = const [],
    this.error,
  });

  FoodSearchState copyWith({
    String? query,
    bool? isLoading,
    List<FoodItem>? results,
    String? error,
  }) =>
      FoodSearchState(
        query: query ?? this.query,
        isLoading: isLoading ?? this.isLoading,
        results: results ?? this.results,
        error: error,
      );
}

final foodSearchProvider =
    StateNotifierProvider.autoDispose<FoodSearchNotifier, FoodSearchState>(
  (ref) => FoodSearchNotifier(ref),
);

class FoodSearchNotifier extends StateNotifier<FoodSearchState> {
  final Ref _ref;

  FoodSearchNotifier(this._ref) : super(const FoodSearchState());

  Future<void> search(String query) async {
    if (query.trim().isEmpty) {
      state = state.copyWith(query: query, results: [], isLoading: false);
      return;
    }
    state = state.copyWith(query: query, isLoading: true, error: null);
    try {
      final client = _ref.read(apiClientProvider);
      final response = await client.get<Map<String, dynamic>>(
        ApiConstants.foodItems,
        queryParameters: {'q': query.trim(), 'limit': 20},
      );
      final json = responseJson(response);
      final items = (json['items'] as List<dynamic>? ?? [])
          .map((e) => FoodItem.fromJson(e as Map<String, dynamic>))
          .toList();
      state = state.copyWith(results: items, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void clear() => state = const FoodSearchState();
}

// ── Photo analyse ─────────────────────────────────────────────────────────────

/// État de l'analyse photo repas.
class PhotoAnalysisState {
  final bool isUploading;
  final NutritionPhoto? result;
  final String? error;

  const PhotoAnalysisState({
    this.isUploading = false,
    this.result,
    this.error,
  });

  PhotoAnalysisState copyWith({
    bool? isUploading,
    NutritionPhoto? result,
    String? error,
  }) =>
      PhotoAnalysisState(
        isUploading: isUploading ?? this.isUploading,
        result: result ?? this.result,
        error: error,
      );
}

final photoAnalysisProvider =
    StateNotifierProvider.autoDispose<PhotoAnalysisNotifier, PhotoAnalysisState>(
  (ref) => PhotoAnalysisNotifier(ref),
);

class PhotoAnalysisNotifier extends StateNotifier<PhotoAnalysisState> {
  final Ref _ref;

  PhotoAnalysisNotifier(this._ref) : super(const PhotoAnalysisState());

  /// Upload une photo et poll l'analyse jusqu'à completion.
  Future<void> analyzePhoto(String filePath) async {
    state = const PhotoAnalysisState(isUploading: true);
    try {
      final client = _ref.read(apiClientProvider);
      final formData = FormData.fromMap({
        'photo': await MultipartFile.fromFile(filePath),
      });
      final uploadResponse = await client.postFile<Map<String, dynamic>>(
        ApiConstants.nutritionPhotos,
        data: formData,
      );
      NutritionPhoto photo =
          NutritionPhoto.fromJson(responseJson(uploadResponse));
      state = state.copyWith(isUploading: false, result: photo);

      // Polling toutes les 2s jusqu'à analyzed|failed (max 30s)
      int attempts = 0;
      while (photo.isPending && attempts < 15) {
        await Future<void>.delayed(const Duration(seconds: 2));
        final pollResponse = await client.get<Map<String, dynamic>>(
          '${ApiConstants.nutritionPhotos}/${photo.photoId}',
        );
        photo = NutritionPhoto.fromJson(responseJson(pollResponse));
        state = state.copyWith(result: photo);
        attempts++;
      }
    } catch (e) {
      state = PhotoAnalysisState(error: e.toString());
    }
  }

  void reset() => state = const PhotoAnalysisState();
}
