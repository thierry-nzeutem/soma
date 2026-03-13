/// États d'authentification SOMA (LOT 5).
library;

/// État d'authentification représenté par une sealed class.
sealed class AuthState {
  const AuthState();
}

/// Pas encore déterminé (splash screen).
class AuthStateInitial extends AuthState {
  const AuthStateInitial();
}

/// Chargement en cours (login, logout).
class AuthStateLoading extends AuthState {
  const AuthStateLoading();
}

/// Utilisateur authentifié.
class AuthStateAuthenticated extends AuthState {
  final String accessToken;
  const AuthStateAuthenticated({required this.accessToken});
}

/// Non authentifié (pas de token, ou logout).
class AuthStateUnauthenticated extends AuthState {
  const AuthStateUnauthenticated();
}

/// Erreur d'authentification.
class AuthStateError extends AuthState {
  final String message;
  const AuthStateError({required this.message});
}
