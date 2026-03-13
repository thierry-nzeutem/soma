"""Endpoint consolide user + subscription + entitlements."""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.core.entitlements import get_user_features, get_effective_plan
from app.models.user import User

profile_full_router = APIRouter(tags=["Profile"])


class SubscriptionInfo(BaseModel):
    plan_code: str
    effective_plan: str
    plan_status: str
    plan_expires_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    is_trial: bool = False
    is_expired: bool = False
    is_active: bool = True


class MeResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_superuser: bool = False
    subscription: SubscriptionInfo
    entitlements: List[str]


@profile_full_router.get("/me/profile", response_model=MeResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """
    Endpoint consolide: user + plan + entitlements en un seul appel.
    Evite les appels multiples depuis les frontends.
    """
    now = datetime.now(timezone.utc)
    effective = get_effective_plan(current_user)
    is_expired = bool(current_user.plan_expires_at and current_user.plan_expires_at < now)
    is_trial = bool(current_user.trial_ends_at and current_user.trial_ends_at > now)

    subscription = SubscriptionInfo(
        plan_code=current_user.plan_code,
        effective_plan=effective.value,
        plan_status=current_user.plan_status,
        plan_expires_at=current_user.plan_expires_at,
        trial_ends_at=current_user.trial_ends_at,
        is_trial=is_trial,
        is_expired=is_expired,
        is_active=(current_user.plan_status == "active" and not is_expired),
    )

    return MeResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        is_superuser=getattr(current_user, "is_superuser", False),
        subscription=subscription,
        entitlements=get_user_features(current_user),
    )
