/// SOMA LOT 16 — Biomarker Analysis Notifier.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:soma_mobile/core/api/api_client.dart';
import 'package:soma_mobile/core/models/biomarker.dart';

final biomarkerAnalysisProvider =
    AsyncNotifierProvider<BiomarkerAnalysisNotifier, BiomarkerAnalysis>(
  BiomarkerAnalysisNotifier.new,
);

class BiomarkerAnalysisNotifier extends AsyncNotifier<BiomarkerAnalysis> {
  @override
  Future<BiomarkerAnalysis> build() async {
    final client = ref.read(apiClientProvider);
    final response = await client.get('/labs/analysis');
    return BiomarkerAnalysis.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> addLabResult(LabResultCreate labResult) async {
    final client = ref.read(apiClientProvider);
    await client.post('/labs/result', data: labResult.toJson());
    // Refresh analysis
    state = const AsyncValue.loading();
    try {
      final response = await client.get('/labs/analysis');
      state = AsyncValue.data(
        BiomarkerAnalysis.fromJson(response.data as Map<String, dynamic>),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
