/// Client HTTP SOMA — Dio configuré avec intercepteur JWT.
///
/// Gestion automatique des tokens :
///   - Injection du header Authorization sur chaque requête
///   - Refresh automatique sur 401 (token expiré)
///   - Redirection vers /login si refresh échoue
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/token_storage.dart';
import 'api_constants.dart';

// ── Provider Riverpod ─────────────────────────────────────────────────────────

/// Provider global du client HTTP Dio.
/// Utiliser via `ref.read(apiClientProvider)` dans les notifiers.
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

// ── Client principal ──────────────────────────────────────────────────────────

/// Client HTTP SOMA encapsulant Dio.
///
/// Usage :
/// ```dart
/// final client = ref.read(apiClientProvider);
/// final data = await client.get('/api/v1/metrics/daily');
/// ```
class ApiClient {
  late final Dio _dio;
  final TokenStorage _tokens = TokenStorage.instance;

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      sendTimeout: ApiConstants.sendTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.addAll([
      _AuthInterceptor(_tokens, _dio),
      LogInterceptor(
        request: false,
        requestBody: false,
        responseBody: false,
        error: true,
      ),
    ]);
  }

  // ── Méthodes HTTP ─────────────────────────────────────────────────────────

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.get<T>(path, queryParameters: queryParameters);

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.post<T>(path, data: data, queryParameters: queryParameters);

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
  }) =>
      _dio.put<T>(path, data: data);

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
  }) =>
      _dio.patch<T>(path, data: data);

  Future<Response<T>> delete<T>(String path) => _dio.delete<T>(path);

  /// Upload multipart (photo repas). Dio gère Content-Type automatiquement.
  Future<Response<T>> postFile<T>(
    String path, {
    required FormData data,
  }) =>
      _dio.post<T>(path, data: data);
}

// ── Intercepteur JWT ──────────────────────────────────────────────────────────

class _AuthInterceptor extends Interceptor {
  final TokenStorage _tokens;
  final Dio _dio;
  bool _isRefreshing = false;

  _AuthInterceptor(this._tokens, this._dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) {
    final token = _tokens.accessToken;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Refresh automatique sur 401
    if (err.response?.statusCode == 401 &&
        !_isRefreshing &&
        _tokens.refreshToken != null) {
      _isRefreshing = true;
      try {
        final refreshResponse = await _dio.post(
          ApiConstants.refresh,
          data: {'refresh_token': _tokens.refreshToken},
        );
        final newToken =
            refreshResponse.data['access_token'] as String?;
        if (newToken != null) {
          await _tokens.setAccessToken(newToken);
          // Relance la requête originale avec le nouveau token
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          final retryResponse = await _dio.fetch(err.requestOptions);
          handler.resolve(retryResponse);
          return;
        }
      } catch (_) {
        // Refresh échoué → déconnexion
        await _tokens.clear();
      } finally {
        _isRefreshing = false;
      }
    }
    handler.next(err);
  }
}

// ── Helpers de désérialisation ────────────────────────────────────────────────

/// Extrait le corps JSON d'une réponse Dio.
Map<String, dynamic> responseJson(Response<dynamic> response) {
  final data = response.data;
  if (data is Map<String, dynamic>) return data;
  throw const FormatException('Unexpected response format');
}
