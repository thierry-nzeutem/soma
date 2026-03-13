/// Sync Models — modèles pour la file d'actions offline.
///
/// Une [SyncAction] représente une action utilisateur réalisée hors ligne
/// qui doit être rejouée sur le serveur à la reconnexion.
library;

import 'package:flutter/foundation.dart';

// ── Types d'actions ───────────────────────────────────────────────────────────

/// Catégories d'actions qui peuvent être mises en attente hors ligne.
enum SyncActionType {
  /// Ajout d'une entrée nutrition.
  addNutritionEntry,

  /// Ajout d'un log hydratation.
  addHydrationLog,

  /// Ajout d'un log sommeil.
  addSleepLog,

  /// Création d'une session workout.
  createWorkoutSession,

  /// Ajout d'une série à une session.
  addWorkoutSet,

  /// Complétion d'une session workout.
  completeWorkoutSession,

  /// Marquer un insight comme lu.
  markInsightRead,

  /// Ignorer un insight.
  dismissInsight,

  /// Sauvegarde d'une session vision.
  saveVisionSession,
}

// ── Statut de synchronisation ─────────────────────────────────────────────────

/// Statut d'une action dans la queue.
enum SyncStatus {
  /// En attente d'une connexion réseau.
  pending,

  /// En cours d'envoi au serveur.
  syncing,

  /// Action envoyée avec succès.
  synced,

  /// Échec après [SyncAction.maxRetries] tentatives.
  failed,
}

// ── Modèle SyncAction ─────────────────────────────────────────────────────────

/// Action utilisateur en attente de synchronisation.
@immutable
class SyncAction {
  /// Identifiant unique (UUID v4 généré localement).
  final String id;

  /// Type de l'action.
  final SyncActionType type;

  /// Données de l'action (payload à envoyer au serveur).
  final Map<String, dynamic> payload;

  /// Date de mise en file d'attente.
  final DateTime queuedAt;

  /// Nombre de tentatives échouées.
  final int retryCount;

  /// Statut courant.
  final SyncStatus status;

  /// Message d'erreur de la dernière tentative (si status == failed).
  final String? lastError;

  static const int maxRetries = 3;

  const SyncAction({
    required this.id,
    required this.type,
    required this.payload,
    required this.queuedAt,
    this.retryCount = 0,
    this.status = SyncStatus.pending,
    this.lastError,
  });

  bool get isPending => status == SyncStatus.pending;
  bool get isSyncing => status == SyncStatus.syncing;
  bool get isSynced => status == SyncStatus.synced;
  bool get isFailed => status == SyncStatus.failed;
  bool get canRetry => retryCount < maxRetries;

  SyncAction copyWith({
    SyncStatus? status,
    int? retryCount,
    String? lastError,
  }) =>
      SyncAction(
        id: id,
        type: type,
        payload: payload,
        queuedAt: queuedAt,
        retryCount: retryCount ?? this.retryCount,
        status: status ?? this.status,
        lastError: lastError ?? this.lastError,
      );

  // ── Sérialisation ──────────────────────────────────────────────────────────

  factory SyncAction.fromJson(Map<String, dynamic> json) => SyncAction(
        id: json['id'] as String,
        type: SyncActionType.values.firstWhere(
          (t) => t.name == json['type'],
          orElse: () => SyncActionType.addHydrationLog,
        ),
        payload: (json['payload'] as Map<String, dynamic>?) ?? {},
        queuedAt: DateTime.parse(json['queued_at'] as String),
        retryCount: (json['retry_count'] as int?) ?? 0,
        status: SyncStatus.values.firstWhere(
          (s) => s.name == json['status'],
          orElse: () => SyncStatus.pending,
        ),
        lastError: json['last_error'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type.name,
        'payload': payload,
        'queued_at': queuedAt.toIso8601String(),
        'retry_count': retryCount,
        'status': status.name,
        if (lastError != null) 'last_error': lastError,
      };
}

// ── Résultat de synchronisation ───────────────────────────────────────────────

/// Résultat d'un cycle de synchronisation.
class SyncResult {
  final int synced;
  final int failed;
  final int pending;
  final List<String> errors;

  const SyncResult({
    required this.synced,
    required this.failed,
    required this.pending,
    this.errors = const [],
  });

  bool get hasErrors => errors.isNotEmpty;
  bool get allSynced => failed == 0 && pending == 0;
}
