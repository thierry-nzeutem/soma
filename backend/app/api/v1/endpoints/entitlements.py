"""Endpoint d'entitlements - droits d'acces par plan."""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.core.entitlements import get_user_features
from app.models.user import User

entitlements_router = APIRouter(prefix="/me", tags=["Entitlements"])


class EntitlementsResponse(BaseModel):
    plan_code: str
    plan_status: str
    features: List[str]
    plan_expires_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    is_trial: bool = False
    is_expired: bool = False


@entitlements_router.get("/entitlements", response_model=EntitlementsResponse)
async def get_my_entitlements(
    current_user: User = Depends(get_current_user),
) -> EntitlementsResponse:
    """Retourne le plan actuel et la liste des features accessibles."""
    now = datetime.now(timezone.utc)
    is_expired = bool(current_user.plan_expires_at and current_user.plan_expires_at < now)
    is_trial = bool(current_user.trial_ends_at and current_user.trial_ends_at > now)

    return EntitlementsResponse(
        plan_code=current_user.plan_code,
        plan_status=current_user.plan_status,
        features=get_user_features(current_user),
        plan_expires_at=current_user.plan_expires_at,
        trial_ends_at=current_user.trial_ends_at,
        is_trial=is_trial,
        is_expired=is_expired,
    )
