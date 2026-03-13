"""Controle d acces par feature et plan SOMA."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status

from app.core.plans import PlanCode
from app.core.features import FeatureCode
from app.core.deps import get_current_user
from app.models.user import User


# Matrice feature -> plan minimum requis
_FEATURE_MIN_PLAN: dict[FeatureCode, PlanCode] = {
    FeatureCode.BASIC_DASHBOARD: PlanCode.FREE,
    FeatureCode.BASIC_HEALTH_METRICS: PlanCode.FREE,
    FeatureCode.LOCAL_AI_TIPS: PlanCode.FREE,
    FeatureCode.AI_COACH: PlanCode.AI,
    FeatureCode.DAILY_BRIEFING: PlanCode.AI,
    FeatureCode.ADVANCED_INSIGHTS: PlanCode.AI,
    FeatureCode.PDF_REPORTS: PlanCode.AI,
    FeatureCode.ANOMALY_DETECTION: PlanCode.AI,
    FeatureCode.BIOLOGICAL_AGE: PlanCode.AI,
    FeatureCode.READINESS_SCORE: PlanCode.PERFORMANCE,
    FeatureCode.INJURY_PREDICTION: PlanCode.PERFORMANCE,
    FeatureCode.BIOMECHANICS_VISION: PlanCode.PERFORMANCE,
    FeatureCode.ADVANCED_VO2MAX: PlanCode.PERFORMANCE,
    FeatureCode.TRAINING_LOAD: PlanCode.PERFORMANCE,
}

# Matrice plan -> set de features incluses
PLAN_FEATURES: dict[PlanCode, set[FeatureCode]] = {
    PlanCode.FREE: {
        FeatureCode.BASIC_DASHBOARD,
        FeatureCode.BASIC_HEALTH_METRICS,
        FeatureCode.LOCAL_AI_TIPS,
    },
    PlanCode.AI: {
        FeatureCode.BASIC_DASHBOARD,
        FeatureCode.BASIC_HEALTH_METRICS,
        FeatureCode.LOCAL_AI_TIPS,
        FeatureCode.AI_COACH,
        FeatureCode.DAILY_BRIEFING,
        FeatureCode.ADVANCED_INSIGHTS,
        FeatureCode.PDF_REPORTS,
        FeatureCode.ANOMALY_DETECTION,
        FeatureCode.BIOLOGICAL_AGE,
    },
    PlanCode.PERFORMANCE: {
        FeatureCode.BASIC_DASHBOARD,
        FeatureCode.BASIC_HEALTH_METRICS,
        FeatureCode.LOCAL_AI_TIPS,
        FeatureCode.AI_COACH,
        FeatureCode.DAILY_BRIEFING,
        FeatureCode.ADVANCED_INSIGHTS,
        FeatureCode.PDF_REPORTS,
        FeatureCode.ANOMALY_DETECTION,
        FeatureCode.BIOLOGICAL_AGE,
        FeatureCode.READINESS_SCORE,
        FeatureCode.INJURY_PREDICTION,
        FeatureCode.BIOMECHANICS_VISION,
        FeatureCode.ADVANCED_VO2MAX,
        FeatureCode.TRAINING_LOAD,
    },
}


def get_effective_plan(user: User) -> PlanCode:
    """
    Source de verite unique pour le plan effectif d un utilisateur.
    Regles:
      - plan_status != active -> FREE (carte expiree, annulation, paiement echoue)
      - plan_expires_at depasse -> FREE (meme si plan_code pas encore nettoye)
      - sinon: plan_code de la DB
    """
    if user.plan_status != "active":
        return PlanCode.FREE
    if user.plan_expires_at and user.plan_expires_at < datetime.now(timezone.utc):
        return PlanCode.FREE
    # Trial check: si trial expire, retour au free
    if user.trial_ends_at and user.trial_ends_at < datetime.now(timezone.utc):
        # Si plan_code = free en trial, on reste free
        if user.plan_code == PlanCode.FREE:
            return PlanCode.FREE
    try:
        return PlanCode(user.plan_code)
    except ValueError:
        return PlanCode.FREE


def user_has_feature(user: User, feature: FeatureCode) -> bool:
    """Retourne True si l utilisateur a acces a la feature selon son plan effectif."""
    effective = get_effective_plan(user)
    return feature in PLAN_FEATURES.get(effective, set())


def get_user_features(user: User) -> list[str]:
    """Retourne la liste des feature codes accessibles pour l utilisateur."""
    effective = get_effective_plan(user)
    return [f.value for f in PLAN_FEATURES.get(effective, set())]


def require_feature(feature: FeatureCode):
    """FastAPI dependency: leve HTTPException 403 si la feature n est pas dans le plan effectif."""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not user_has_feature(current_user, feature):
            effective = get_effective_plan(current_user)
            min_plan = _FEATURE_MIN_PLAN.get(feature, PlanCode.AI)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_not_available",
                    "feature": feature.value,
                    "required_plan": min_plan.value,
                    "current_plan": current_user.plan_code,
                    "effective_plan": effective.value,
                    "plan_status": current_user.plan_status,
                    "message": (
                        f"La fonctionnalite '{feature.value}' necessite le plan "
                        f"'{min_plan.value}'. Plan effectif: '{effective.value}'."
                    ),
                },
            )
        return current_user
    return checker


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: reserve aux superusers (admin)."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
