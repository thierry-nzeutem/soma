"""Panel d administration SOMA - gestion utilisateurs, plans, settings."""
import json
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.entitlements import require_superuser
from app.models.user import User

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Settings ─────────────────────────────────────────────────────────────────

class AppSetting(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    category: str = "general"
    updated_at: datetime


class AppSettingUpdate(BaseModel):
    value: Optional[str] = None


@admin_router.get("/settings", response_model=List[AppSetting])
async def get_settings(
    category: Optional[str] = Query(default=None),
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les parametres d application (admin)."""
    query = "SELECT key, value, description, category, updated_at FROM app_settings"
    params = {}
    if category:
        query += " WHERE category = :cat"
        params["cat"] = category
    query += " ORDER BY category, key"
    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [AppSetting(**dict(r)) for r in rows]


@admin_router.put("/settings/{key}", response_model=AppSetting)
async def update_setting(
    key: str,
    payload: AppSettingUpdate,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Met a jour un parametre d application (admin)."""
    result = await db.execute(
        text(
            "UPDATE app_settings SET value = :val, updated_at = now(), updated_by = :by "
            "WHERE key = :key RETURNING key, value, description, category, updated_at"
        ),
        {"val": payload.value, "by": admin.username, "key": key},
    )
    row = result.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    await db.commit()
    return AppSetting(**dict(row))


# ── Users ─────────────────────────────────────────────────────────────────────

class AdminUserView(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_superuser: bool
    plan_code: str
    plan_status: str
    stripe_customer_id: Optional[str] = None
    plan_started_at: Optional[datetime] = None
    plan_expires_at: Optional[datetime] = None
    created_at: datetime


class AdminPlanUpdate(BaseModel):
    plan_code: str
    plan_status: str = "active"
    plan_expires_at: Optional[datetime] = None


@admin_router.get("/users", response_model=List[AdminUserView])
async def list_users(
    plan_code: Optional[str] = Query(default=None),
    plan_status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Liste les utilisateurs avec leurs infos de plan (admin)."""
    query = (
        "SELECT id, username, email, is_active, is_superuser, plan_code, plan_status, "
        "stripe_customer_id, plan_started_at, plan_expires_at, created_at "
        "FROM users WHERE 1=1"
    )
    params: dict = {}
    if plan_code:
        query += " AND plan_code = :plan_code"
        params["plan_code"] = plan_code
    if plan_status:
        query += " AND plan_status = :plan_status"
        params["plan_status"] = plan_status
    if search:
        query += " AND (username ILIKE :search OR email ILIKE :search)"
        params["search"] = f"%{search}%"
    query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [AdminUserView(id=str(r["id"]), **{k: v for k, v in dict(r).items() if k != "id"}) for r in rows]


@admin_router.put("/users/{user_id}/plan", response_model=AdminUserView)
async def update_user_plan(
    user_id: str,
    payload: AdminPlanUpdate,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Met a jour le plan d un utilisateur manuellement (admin)."""
    result = await db.execute(
        text(
            "UPDATE users SET plan_code = :plan, plan_status = :status, "
            "plan_expires_at = :expires, plan_started_at = COALESCE(plan_started_at, now()) "
            "WHERE id = :uid "
            "RETURNING id, username, email, is_active, is_superuser, plan_code, plan_status, "
            "stripe_customer_id, plan_started_at, plan_expires_at, created_at"
        ),
        {
            "plan": payload.plan_code,
            "status": payload.plan_status,
            "expires": payload.plan_expires_at,
            "uid": user_id,
        }
    )
    row = result.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return AdminUserView(id=str(row["id"]), **{k: v for k, v in dict(row).items() if k != "id"})


@admin_router.get("/stats")
async def get_admin_stats(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Statistiques globales de l application (admin)."""
    results = {}

    # Plan distribution
    plan_dist = await db.execute(
        text("SELECT plan_code, plan_status, COUNT(*) as count FROM users GROUP BY plan_code, plan_status ORDER BY plan_code")
    )
    results["plan_distribution"] = [dict(r) for r in plan_dist.mappings().all()]

    # Total users
    total = await db.scalar(text("SELECT COUNT(*) FROM users"))
    results["total_users"] = total

    # Active subscriptions
    active_paid = await db.scalar(
        text("SELECT COUNT(*) FROM users WHERE plan_code != 'free' AND plan_status = 'active'")
    )
    results["active_paid_subscriptions"] = active_paid

    # Feature usage last 7 days
    usage = await db.execute(
        text(
            "SELECT event_type, COUNT(*) as count FROM feature_usage_events "
            "WHERE occurred_at >= NOW() - INTERVAL '7 days' "
            "GROUP BY event_type ORDER BY count DESC"
        )
    )
    results["feature_usage_7d"] = [dict(r) for r in usage.mappings().all()]

    return results
