/// Gestion structurée des erreurs API SOMA (LOT 5).
///
/// Convertit les DioException en messages utilisateur lisibles.
/// Catégorise les erreurs pour permettre un handling adapté.
library;

import 'package:dio/dio.dart';

/// Catégories d'erreur API.
enum ApiErrorType {
  /// Problème de connexion réseau (pas d'internet, timeout).
  network,
  /// Authentification invalide (token expiré, non autorisé).
  unauthorized,
  /// Ressource introuvable.
  notFound,
  /// Erreur de validation des données envoyées.
  validation,
  /// Erreur serveur interne (5xx).
  server,
  /// Erreur inattendue.
  unknown,
}

/// Erreur API structurée.
class ApiError implements Exception {
  final ApiErrorType type;
  final String message;
  final int? statusCode;
  final dynamic originalError;

  const ApiError({
    required this.type,
    required this.message,
    this.statusCode,
    this.originalError,
  });

  /// Crée un ApiError depuis une exception Dio.
  factory ApiError.fromDioException(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiError(
          type: ApiErrorType.network,
          message: 'La connexion a expiré. Vérifiez votre réseau.',
          originalError: e,
        );

      case DioExceptionType.connectionError:
        return ApiError(
          type: ApiErrorType.network,
          message: 'Impossible de contacter le serveur. Vérifiez votre connexion.',
          originalError: e,
        );

      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final detail = _extractDetail(e.response?.data);
        switch (statusCode) {
          case 401:
            return ApiError(
              type: ApiErrorType.unauthorized,
              message: 'Session expirée. Veuillez vous reconnecter.',
              statusCode: statusCode,
              originalError: e,
            );
          case 403:
            return ApiError(
              type: ApiErrorType.unauthorized,
              message: 'Accès refusé.',
              statusCode: statusCode,
              originalError: e,
            );
          case 404:
            return ApiError(
              type: ApiErrorType.notFound,
              message: detail ?? 'Ressource introuvable.',
              statusCode: statusCode,
              originalError: e,
            );
          case 422:
            return ApiError(
              type: ApiErrorType.validation,
              message: detail ?? 'Données invalides.',
              statusCode: statusCode,
              originalError: e,
            );
          default:
            if (statusCode != null && statusCode >= 500) {
              return ApiError(
                type: ApiErrorType.server,
                message: 'Erreur serveur. Veuillez réessayer plus tard.',
                statusCode: statusCode,
                originalError: e,
              );
            }
            return ApiError(
              type: ApiErrorType.unknown,
              message: detail ?? 'Une erreur est survenue.',
              statusCode: statusCode,
              originalError: e,
            );
        }

      default:
        return ApiError(
          type: ApiErrorType.unknown,
          message: 'Une erreur inattendue est survenue.',
          originalError: e,
        );
    }
  }

  /// Crée un ApiError depuis n'importe quelle exception.
  factory ApiError.fromException(Object e) {
    if (e is ApiError) return e;
    if (e is DioException) return ApiError.fromDioException(e);
    return ApiError(
      type: ApiErrorType.unknown,
      message: 'Une erreur inattendue est survenue.',
      originalError: e,
    );
  }

  static String? _extractDetail(dynamic data) {
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map && first['msg'] != null) return first['msg'] as String;
      }
    }
    return null;
  }

  bool get isNetwork => type == ApiErrorType.network;
  bool get isUnauthorized => type == ApiErrorType.unauthorized;

  @override
  String toString() => 'ApiError($type): $message';
}
