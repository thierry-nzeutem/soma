"""SOMA Coach Platform — Invitation & Recommendation endpoints (Phase 1).
"""
from __future__ import annotations

import logging
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User, UserProfile
from app.core.deps import get_current_user
from app.core.entitlements import require_feature, user_has_feature
from app.core.features import FeatureCode

from .models import (
    CoachProfileDB,
    AthleteProfileDB,
    CoachAthleteLinkDB,
    CoachInvitationDB,
    CoachRecommendationDB,
    AthleteNoteDB,
)

logger = logging.getLogger(__name__)
coach_invite_router = APIRouter(prefix="/coach-platform", tags=["coach_platform"])

INVITE_EXPIRE_DAYS = 7

# Pydantic schemas

class InvitationCreateRequest(BaseModel):
    invitee_email: Optional[str] = None
    message: Optional[str] = None
    expire_days: int = 7


class InvitationResponse(BaseModel):
    id: str
    coach_profile_id: str
    invite_code: str
    invite_token: str
    invite_link: str
    invitee_email: Optional[str]
    status: str
    message: Optional[str]
    expires_at: str
    accepted_at: Optional[str]
    created_at: str


class AcceptInvitationResponse(BaseModel):
    success: bool
    message: str
    coach_name: str
    athlete_profile_id: str


class LinkStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class LinkStatusResponse(BaseModel):
    athlete_id: str
    coach_id: str
    status: str
    relationship_notes: Optional[str]
    linked_at: Optional[str]


class RecommendationCreateRequest(BaseModel):
    athlete_id: str
    rec_type: str = "general"
    priority: str = "normal"
    title: str
    description: str
    target_date: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: str
    coach_id: str
    athlete_id: str
    rec_type: str
    priority: str
    status: str
    title: str
    description: str
    target_date: Optional[str]
    completed_at: Optional[str]
    created_at: str
    updated_at: str


class RecommendationStatusUpdate(BaseModel):
    status: str


class AthleteFullProfile(BaseModel):
    athlete_profile_id: str
    user_id: str
    display_name: str
    sport: Optional[str]
    goal: Optional[str]
    date_of_birth: Optional[str]
    first_name: Optional[str]
    age: Optional[int]
    sex: Optional[str]
    height_cm: Optional[float]
    activity_level: Optional[str]
    fitness_level: Optional[str]
    link_status: str
    linked_at: Optional[str]
    relationship_notes: Optional[str]
    recent_notes_count: int
    pending_recommendations_count: int

# Helpers

def _generate_invite_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(36)


def _invite_link(token: str) -> str:
    return f"soma://coach-invite/{token}"


async def _require_coach(db: AsyncSession, user_id: uuid.UUID) -> CoachProfileDB:
    result = await db.execute(
        select(CoachProfileDB).where(CoachProfileDB.user_id == user_id)
    )
    coach = result.scalar_one_or_none()
    if not coach:
        raise HTTPException(
            status_code=403,
            detail="Profil coach requis. Inscrivez-vous d'abord comme coach.",
        )
    return coach


async def _check_coach_athlete_access(
    db: AsyncSession,
    coach_id: uuid.UUID,
    athlete_id: uuid.UUID,
) -> CoachAthleteLinkDB:
    result = await db.execute(
        select(CoachAthleteLinkDB).where(
            CoachAthleteLinkDB.coach_id == coach_id,
            CoachAthleteLinkDB.athlete_id == athlete_id,
            CoachAthleteLinkDB.status.in_(["active", "paused"]),
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=403,
            detail="Vous n'avez pas accès à cet athlète.",
        )
    return link

# Invitation endpoints

@coach_invite_router.post(
    "/invitations",
    response_model=InvitationResponse,
    status_code=201,
    summary="Créer une invitation coach",
)
async def create_invitation(
    body: InvitationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    coach = await _require_coach(db, current_user.id)

    expire_days = max(1, min(30, body.expire_days))
    expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

    invite_code = _generate_invite_code(8)
    invite_token = _generate_invite_token()

    for _ in range(5):
        r1 = await db.execute(
            select(CoachInvitationDB).where(CoachInvitationDB.invite_code == invite_code)
        )
        r2 = await db.execute(
            select(CoachInvitationDB).where(CoachInvitationDB.invite_token == invite_token)
        )
        if not r1.scalar_one_or_none() and not r2.scalar_one_or_none():
            break
        invite_code = _generate_invite_code(8)
        invite_token = _generate_invite_token()

    inv = CoachInvitationDB(
        id=uuid.uuid4(),
        coach_profile_id=coach.id,
        invite_code=invite_code,
        invite_token=invite_token,
        invitee_email=body.invitee_email,
        status="pending",
        message=body.message,
        expires_at=expires_at,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    return _inv_to_response(inv)


@coach_invite_router.get(
    "/invitations",
    response_model=list[InvitationResponse],
    summary="Lister mes invitations",
)
async def list_invitations(
    status: Optional[str] = Query(None, description="Filter: pending|accepted|expired|cancelled"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    coach = await _require_coach(db, current_user.id)

    q = select(CoachInvitationDB).where(
        CoachInvitationDB.coach_profile_id == coach.id
    ).order_by(CoachInvitationDB.created_at.desc())

    if status:
        q = q.where(CoachInvitationDB.status == status)

    result = await db.execute(q)
    invs = result.scalars().all()

    now = datetime.now(timezone.utc)
    for inv in invs:
        if inv.status == "pending" and inv.expires_at < now:
            inv.status = "expired"
    await db.commit()

    return [_inv_to_response(inv) for inv in invs]


@coach_invite_router.delete(
    "/invitations/{invite_id}",
    status_code=204,
    summary="Annuler une invitation",
)
async def cancel_invitation(
    invite_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    coach = await _require_coach(db, current_user.id)

    try:
        inv_uuid = uuid.UUID(invite_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invite_id invalide.")

    result = await db.execute(
        select(CoachInvitationDB).where(
            CoachInvitationDB.id == inv_uuid,
            CoachInvitationDB.coach_profile_id == coach.id,
        )
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation non trouvée.")
    if inv.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"L'invitation ne peut pas être annulée (statut: {inv.status}).",
        )

    inv.status = "cancelled"
    await db.commit()

@coach_invite_router.post(
    "/invitations/accept/{token}",
    response_model=AcceptInvitationResponse,
    summary="Accepter une invitation coach",
)
async def accept_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CoachInvitationDB).where(CoachInvitationDB.invite_token == token)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation non trouvée ou invalide.")

    now = datetime.now(timezone.utc)
    if inv.status == "accepted":
        raise HTTPException(status_code=409, detail="Cette invitation a déjà été acceptée.")
    if inv.status in ("cancelled", "expired") or inv.expires_at < now:
        raise HTTPException(status_code=410, detail="Cette invitation est expirée ou annulée.")

    coach_result = await db.execute(
        select(CoachProfileDB).where(CoachProfileDB.id == inv.coach_profile_id)
    )
    coach = coach_result.scalar_one_or_none()
    if not coach:
        raise HTTPException(status_code=404, detail="Profil coach non trouvé.")

    athlete_result = await db.execute(
        select(AthleteProfileDB).where(AthleteProfileDB.user_id == current_user.id)
    )
    athlete = athlete_result.scalar_one_or_none()

    if not athlete:
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        user_profile = profile_result.scalar_one_or_none()
        display_name = (
            user_profile.first_name if user_profile and user_profile.first_name
            else current_user.username
        )

        athlete = AthleteProfileDB(
            id=uuid.uuid4(),
            user_id=current_user.id,
            display_name=display_name,
            is_active=True,
        )
        db.add(athlete)
        await db.flush()

    link_result = await db.execute(
        select(CoachAthleteLinkDB).where(
            CoachAthleteLinkDB.coach_id == coach.id,
            CoachAthleteLinkDB.athlete_id == athlete.id,
        )
    )
    existing_link = link_result.scalar_one_or_none()

    if existing_link:
        if existing_link.status in ("active", "paused"):
            raise HTTPException(
                status_code=409,
                detail="Vous êtes déjà lié à ce coach.",
            )
        existing_link.status = "active"
        existing_link.is_active = True
    else:
        link = CoachAthleteLinkDB(
            id=uuid.uuid4(),
            coach_id=coach.id,
            athlete_id=athlete.id,
            is_active=True,
            status="active",
            role="primary",
            linked_at=now,
        )
        db.add(link)

    inv.status = "accepted"
    inv.accepted_at = now
    inv.invitee_user_id = current_user.id

    coach_user_result = await db.execute(
        select(User).where(User.id == coach.user_id)
    )
    coach_user = coach_user_result.scalar_one_or_none()
    if coach_user:
        coach_user.is_coach = True

    await db.commit()

    return AcceptInvitationResponse(
        success=True,
        message=f"Vous êtes maintenant lié à votre coach {coach.name}.",
        coach_name=coach.name,
        athlete_profile_id=str(athlete.id),
    )


def _inv_to_response(inv: CoachInvitationDB) -> InvitationResponse:
    return InvitationResponse(
        id=str(inv.id),
        coach_profile_id=str(inv.coach_profile_id),
        invite_code=inv.invite_code,
        invite_token=inv.invite_token,
        invite_link=_invite_link(inv.invite_token),
        invitee_email=inv.invitee_email,
        status=inv.status,
        message=inv.message,
        expires_at=inv.expires_at.isoformat(),
        accepted_at=inv.accepted_at.isoformat() if inv.accepted_at else None,
        created_at=inv.created_at.isoformat(),
    )

# Relationship status management

@coach_invite_router.patch(
    "/athlete/{athlete_id}/status",
    response_model=LinkStatusResponse,
    summary="Mettre à jour le statut de la relation coach-athlète",
)
async def update_link_status(
    athlete_id: str,
    body: LinkStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    valid_statuses = {"active", "paused", "archived", "revoked"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Statut invalide. Valeurs acceptées: {valid_statuses}",
        )

    coach = await _require_coach(db, current_user.id)

    try:
        athlete_uuid = uuid.UUID(athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    result = await db.execute(
        select(CoachAthleteLinkDB).where(
            CoachAthleteLinkDB.coach_id == coach.id,
            CoachAthleteLinkDB.athlete_id == athlete_uuid,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Relation non trouvée.")

    link.status = body.status
    link.is_active = body.status in ("active", "paused")
    if body.notes is not None:
        link.relationship_notes = body.notes

    await db.commit()
    await db.refresh(link)

    return LinkStatusResponse(
        athlete_id=str(link.athlete_id),
        coach_id=str(link.coach_id),
        status=link.status,
        relationship_notes=link.relationship_notes,
        linked_at=link.linked_at.isoformat() if link.linked_at else None,
    )

# Full athlete profile

@coach_invite_router.get(
    "/athlete/{athlete_id}/profile",
    response_model=AthleteFullProfile,
    summary="Fiche complète d'un athlète",
)
async def get_athlete_full_profile(
    athlete_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    coach = await _require_coach(db, current_user.id)

    try:
        athlete_uuid = uuid.UUID(athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    link = await _check_coach_athlete_access(db, coach.id, athlete_uuid)

    athlete_result = await db.execute(
        select(AthleteProfileDB).where(AthleteProfileDB.id == athlete_uuid)
    )
    athlete = athlete_result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Profil athlète non trouvé.")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == athlete.user_id)
    )
    user_profile = profile_result.scalar_one_or_none()

    notes_result = await db.execute(
        select(AthleteNoteDB).where(
            AthleteNoteDB.coach_id == coach.id,
            AthleteNoteDB.athlete_id == athlete_uuid,
        )
    )
    notes_count = len(notes_result.scalars().all())

    recs_result = await db.execute(
        select(CoachRecommendationDB).where(
            CoachRecommendationDB.coach_id == coach.id,
            CoachRecommendationDB.athlete_id == athlete_uuid,
            CoachRecommendationDB.status.in_(["pending", "in_progress"]),
        )
    )
    pending_recs = len(recs_result.scalars().all())

    return AthleteFullProfile(
        athlete_profile_id=str(athlete.id),
        user_id=str(athlete.user_id),
        display_name=athlete.display_name,
        sport=athlete.sport,
        goal=athlete.goal,
        date_of_birth=athlete.date_of_birth.isoformat() if athlete.date_of_birth else None,
        first_name=user_profile.first_name if user_profile else None,
        age=user_profile.age if user_profile else None,
        sex=user_profile.sex if user_profile else None,
        height_cm=user_profile.height_cm if user_profile else None,
        activity_level=user_profile.activity_level if user_profile else None,
        fitness_level=user_profile.fitness_level if user_profile else None,
        link_status=link.status,
        linked_at=link.linked_at.isoformat() if link.linked_at else None,
        relationship_notes=link.relationship_notes,
        recent_notes_count=notes_count,
        pending_recommendations_count=pending_recs,
    )

# Recommendations

@coach_invite_router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=201,
    summary="Créer une recommandation",
)
async def create_recommendation(
    body: RecommendationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    valid_types = {"training", "nutrition", "recovery", "medical", "lifestyle", "mental", "general"}
    valid_priorities = {"low", "normal", "high", "urgent"}

    if body.rec_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"Type invalide. Valeurs: {valid_types}")
    if body.priority not in valid_priorities:
        raise HTTPException(status_code=422, detail=f"Priorité invalide. Valeurs: {valid_priorities}")

    coach = await _require_coach(db, current_user.id)

    try:
        athlete_uuid = uuid.UUID(body.athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    await _check_coach_athlete_access(db, coach.id, athlete_uuid)

    target_date = None
    if body.target_date:
        from datetime import date as date_type
        try:
            target_date = date_type.fromisoformat(body.target_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="target_date invalide (format: YYYY-MM-DD).")

    rec = CoachRecommendationDB(
        id=uuid.uuid4(),
        coach_id=coach.id,
        athlete_id=athlete_uuid,
        rec_type=body.rec_type,
        priority=body.priority,
        status="pending",
        title=body.title,
        description=body.description,
        target_date=target_date,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    return _rec_to_response(rec)


@coach_invite_router.get(
    "/athlete/{athlete_id}/recommendations",
    response_model=list[RecommendationResponse],
    summary="Recommandations pour un athlète",
)
async def get_athlete_recommendations(
    athlete_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    coach = await _require_coach(db, current_user.id)

    try:
        athlete_uuid = uuid.UUID(athlete_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="athlete_id invalide.")

    await _check_coach_athlete_access(db, coach.id, athlete_uuid)

    q = select(CoachRecommendationDB).where(
        CoachRecommendationDB.coach_id == coach.id,
        CoachRecommendationDB.athlete_id == athlete_uuid,
    ).order_by(CoachRecommendationDB.created_at.desc())

    if status:
        q = q.where(CoachRecommendationDB.status == status)

    result = await db.execute(q)
    recs = result.scalars().all()

    return [_rec_to_response(r) for r in recs]


@coach_invite_router.patch(
    "/recommendations/{rec_id}",
    response_model=RecommendationResponse,
    summary="Mettre à jour le statut d'une recommandation",
)
async def update_recommendation(
    rec_id: str,
    body: RecommendationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.COACH_MODULE)),
):
    valid_statuses = {"pending", "in_progress", "completed", "dismissed"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Statut invalide. Valeurs: {valid_statuses}",
        )

    coach = await _require_coach(db, current_user.id)

    try:
        rec_uuid = uuid.UUID(rec_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="rec_id invalide.")

    result = await db.execute(
        select(CoachRecommendationDB).where(
            CoachRecommendationDB.id == rec_uuid,
            CoachRecommendationDB.coach_id == coach.id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée.")

    rec.status = body.status
    if body.status == "completed" and not rec.completed_at:
        rec.completed_at = datetime.now(timezone.utc)
    rec.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(rec)

    return _rec_to_response(rec)


def _rec_to_response(rec: CoachRecommendationDB) -> RecommendationResponse:
    return RecommendationResponse(
        id=str(rec.id),
        coach_id=str(rec.coach_id),
        athlete_id=str(rec.athlete_id),
        rec_type=rec.rec_type,
        priority=rec.priority,
        status=rec.status,
        title=rec.title,
        description=rec.description,
        target_date=rec.target_date.isoformat() if rec.target_date else None,
        completed_at=rec.completed_at.isoformat() if rec.completed_at else None,
        created_at=rec.created_at.isoformat(),
        updated_at=rec.updated_at.isoformat(),
    )
