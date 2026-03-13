"""Tracking des usages features - analytics d upgrade."""
import json
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.entitlements import require_superuser
from app.models.user import User

feature_usage_router = APIRouter(tags=["Feature Usage"])


class FeatureUsageEvent(BaseModel):
    event_type: str  # feature_used, feature_denied, upgrade_cta_clicked, checkout_started
    feature_code: Optional[str] = None
    metadata: Optional[dict] = None


class FeatureUsageStat(BaseModel):
    feature_code: str
    event_type: str
    count: int
    unique_users: int


@feature_usage_router.post("/me/feature-usage", status_code=204)
async def track_feature_usage(
    payload: FeatureUsageEvent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enregistre un event d usage feature (appele par le frontend)."""
    await db.execute(
        text(
            "INSERT INTO feature_usage_events "
            "(user_id, event_type, feature_code, plan_code, metadata) "
            "VALUES (:uid, :etype, :fcode, :plan, :meta)"
        ),
        {
            "uid": str(current_user.id),
            "etype": payload.event_type,
            "fcode": payload.feature_code,
            "plan": current_user.plan_code,
            "meta": json.dumps(payload.metadata) if payload.metadata else None,
        }
    )
    await db.commit()


@feature_usage_router.get("/admin/feature-usage", response_model=List[FeatureUsageStat])
async def get_feature_usage_stats(
    days: int = Query(default=30, ge=1, le=365),
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Stats d usage des features (admin uniquement)."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        text(
            "SELECT feature_code, event_type, COUNT(*) as count, COUNT(DISTINCT user_id) as unique_users "
            "FROM feature_usage_events "
            "WHERE occurred_at >= :since AND feature_code IS NOT NULL "
            "GROUP BY feature_code, event_type "
            "ORDER BY count DESC"
        ),
        {"since": since},
    )
    rows = result.mappings().all()
    return [
        FeatureUsageStat(
            feature_code=r["feature_code"],
            event_type=r["event_type"],
            count=r["count"],
            unique_users=r["unique_users"],
        )
        for r in rows
    ]
