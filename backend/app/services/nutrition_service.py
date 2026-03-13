"""
Service nutrition SOMA — logique métier du journal alimentaire (LOT 2).

Responsabilités :
  - Recherche dans la bibliothèque d'aliments (FoodItem)
  - CRUD NutritionEntry avec soft-delete
  - Auto-calcul des macros depuis food_item_id + quantity_g
  - Résumé journalier (totaux, écarts aux objectifs, fenêtre alimentaire)
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.nutrition import FoodItem, NutritionEntry, NutritionPhoto
from app.models.user import UserProfile
from app.schemas.nutrition import (
    FoodItemResponse, FoodItemListResponse,
    NutritionEntryCreate, NutritionEntryUpdate, NutritionEntryResponse,
    NutritionEntryListResponse,
    DailyNutritionSummary, MacroActuals, MacroGoals, MacroBalance,
    MealSummaryItem, EatingWindow,
)


# ── Helpers purs (testables sans DB) ───────────────────────────────────────────

def compute_macros_from_food_item(food_item: FoodItem, quantity_g: float) -> dict:
    """
    Calcule les macros pour une quantité donnée d'un aliment.
    Formule : valeur = (per_100g / 100) * quantity_g
    Retourne un dict avec calories, protein_g, carbs_g, fat_g, fiber_g.
    Valeurs à None si le per_100g correspondant est absent.
    """
    def _scale(per_100g: Optional[float]) -> Optional[float]:
        if per_100g is None:
            return None
        return round(per_100g * quantity_g / 100, 2)

    return {
        "calories": _scale(food_item.calories_per_100g),
        "protein_g": _scale(food_item.protein_g_per_100g),
        "carbs_g": _scale(food_item.carbs_g_per_100g),
        "fat_g": _scale(food_item.fat_g_per_100g),
        "fiber_g": _scale(food_item.fiber_g_per_100g),
    }


def compute_eating_window(entries: List[NutritionEntry]) -> EatingWindow:
    """Calcule la fenêtre alimentaire à partir d'une liste d'entrées triées."""
    if not entries:
        return EatingWindow()

    logged_times = [e.logged_at for e in entries if e.logged_at]
    if not logged_times:
        return EatingWindow()

    first = min(logged_times)
    last = max(logged_times)
    window_h = round((last - first).total_seconds() / 3600, 1) if first != last else 0.0
    fasting_compatible = window_h <= 8.0 if window_h > 0 else None

    return EatingWindow(
        first_meal_at=first,
        last_meal_at=last,
        window_hours=window_h,
        fasting_compatible=fasting_compatible,
    )


def compute_data_completeness(entries: List[NutritionEntry]) -> float:
    """Retourne la proportion d'entrées avec calories renseignées (0.0-100.0)."""
    if not entries:
        return 0.0
    with_cals = sum(1 for e in entries if e.calories is not None)
    return round(with_cals / len(entries) * 100, 1)


# ── Food Items ─────────────────────────────────────────────────────────────────

async def search_food_items(
    db: AsyncSession,
    query: Optional[str] = None,
    food_group: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> FoodItemListResponse:
    """
    Recherche floue dans la bibliothèque d'aliments.
    Utilise ILIKE pour compatibilité SQLite en test, trigram index en PostgreSQL.
    """
    q = select(FoodItem)

    if query:
        pattern = f"%{query}%"
        q = q.where(
            FoodItem.name.ilike(pattern) | FoodItem.name_fr.ilike(pattern)
        )
    if food_group:
        q = q.where(FoodItem.food_group == food_group)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    q = q.order_by(FoodItem.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return FoodItemListResponse(
        items=[FoodItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


async def get_food_item(db: AsyncSession, food_item_id: uuid.UUID) -> Optional[FoodItem]:
    result = await db.execute(select(FoodItem).where(FoodItem.id == food_item_id))
    return result.scalar_one_or_none()


# ── Nutrition Entries ──────────────────────────────────────────────────────────

async def create_entry(
    db: AsyncSession, user_id: uuid.UUID, data: NutritionEntryCreate,
) -> NutritionEntry:
    """
    Crée une entrée nutritionnelle.
    Si food_item_id + quantity_g fournis, calcule automatiquement les macros
    sauf si des macros explicites sont déjà présentes.
    """
    macros: dict = {}

    # Auto-calcul des macros depuis food_item_id
    if data.food_item_id and data.quantity_g:
        food_item = await get_food_item(db, data.food_item_id)
        if food_item:
            macros = compute_macros_from_food_item(food_item, data.quantity_g)

    # Les macros explicites ont priorité sur le calcul automatique
    entry = NutritionEntry(
        user_id=user_id,
        logged_at=data.logged_at or datetime.now(timezone.utc),
        meal_type=data.meal_type,
        meal_name=data.meal_name,
        food_item_id=data.food_item_id,
        photo_id=data.photo_id,
        quantity_g=data.quantity_g,
        calories=data.calories if data.calories is not None else macros.get("calories"),
        protein_g=data.protein_g if data.protein_g is not None else macros.get("protein_g"),
        carbs_g=data.carbs_g if data.carbs_g is not None else macros.get("carbs_g"),
        fat_g=data.fat_g if data.fat_g is not None else macros.get("fat_g"),
        fiber_g=data.fiber_g if data.fiber_g is not None else macros.get("fiber_g"),
        data_quality=data.data_quality or ("exact" if data.food_item_id else "estimated"),
        hunger_before=data.hunger_before,
        satiety_after=data.satiety_after,
        energy_after=data.energy_after,
        notes=data.notes,
        fasting_window_broken=data.fasting_window_broken,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def get_entry(
    db: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID,
) -> Optional[NutritionEntry]:
    """Récupère une entrée par ID avec vérification d'ownership et soft-delete."""
    result = await db.execute(
        select(NutritionEntry).where(and_(
            NutritionEntry.id == entry_id,
            NutritionEntry.user_id == user_id,
            NutritionEntry.is_deleted.is_(False),
        ))
    )
    return result.scalar_one_or_none()


async def list_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: Optional[date] = None,
    page: int = 1,
    per_page: int = 50,
) -> NutritionEntryListResponse:
    """
    Liste les entrées de l'utilisateur, filtrées par date si fournie.
    Ordre chronologique ascendant.
    """
    q = select(NutritionEntry).where(and_(
        NutritionEntry.user_id == user_id,
        NutritionEntry.is_deleted.is_(False),
    ))

    if target_date:
        # Bornes de la journée en UTC
        day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        q = q.where(and_(
            NutritionEntry.logged_at >= day_start,
            NutritionEntry.logged_at < day_end,
        ))

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    q = q.order_by(NutritionEntry.logged_at.asc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    entries = result.scalars().all()

    return NutritionEntryListResponse(
        entries=[NutritionEntryResponse.model_validate(e) for e in entries],
        total=total,
        date=str(target_date) if target_date else None,
    )


async def update_entry(
    db: AsyncSession, entry: NutritionEntry, data: NutritionEntryUpdate,
) -> NutritionEntry:
    """Met à jour une entrée nutritionnelle (PATCH partiel)."""
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(entry, field, value)
    await db.flush()
    await db.refresh(entry)
    return entry


async def delete_entry(db: AsyncSession, entry: NutritionEntry) -> None:
    """Soft-delete d'une entrée."""
    entry.is_deleted = True
    await db.flush()


# ── Daily Summary ──────────────────────────────────────────────────────────────

async def get_daily_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
    profile: Optional[UserProfile] = None,
) -> DailyNutritionSummary:
    """
    Calcule le résumé nutritionnel du jour.
    Agrège les macros, calcule la fenêtre alimentaire et les écarts aux objectifs.
    """
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    result = await db.execute(
        select(NutritionEntry)
        .where(and_(
            NutritionEntry.user_id == user_id,
            NutritionEntry.is_deleted.is_(False),
            NutritionEntry.logged_at >= day_start,
            NutritionEntry.logged_at < day_end,
        ))
        .order_by(NutritionEntry.logged_at.asc())
    )
    entries = result.scalars().all()

    # Totaux
    totals = MacroActuals(
        calories=round(sum(e.calories or 0 for e in entries), 1),
        protein_g=round(sum(e.protein_g or 0 for e in entries), 1),
        carbs_g=round(sum(e.carbs_g or 0 for e in entries), 1),
        fat_g=round(sum(e.fat_g or 0 for e in entries), 1),
        fiber_g=round(sum(e.fiber_g or 0 for e in entries), 1),
    )

    # Objectifs depuis le profil
    goals = None
    balance = None
    if profile:
        goals = MacroGoals(
            calories_target=profile.target_calories_kcal,
            protein_target_g=profile.target_protein_g,
        )
        if goals.calories_target:
            cal_delta = round(totals.calories - goals.calories_target, 1)
            pct_cal = round(totals.calories / goals.calories_target * 100, 1) if goals.calories_target else None
        else:
            cal_delta = None
            pct_cal = None

        prot_delta = None
        pct_prot = None
        if goals.protein_target_g:
            prot_delta = round(totals.protein_g - goals.protein_target_g, 1)
            pct_prot = round(totals.protein_g / goals.protein_target_g * 100, 1)

        balance = MacroBalance(
            calories_delta=cal_delta,
            protein_delta_g=prot_delta,
            pct_calories_reached=pct_cal,
            pct_protein_reached=pct_prot,
        )

    # Repas résumés
    meals = [
        MealSummaryItem(
            id=e.id,
            meal_type=e.meal_type,
            meal_name=e.meal_name,
            logged_at=e.logged_at,
            calories=e.calories,
            protein_g=e.protein_g,
            data_quality=e.data_quality,
        )
        for e in entries
    ]

    # Fenêtre alimentaire
    eating_window = compute_eating_window(list(entries))

    # Qualité des données
    completeness = compute_data_completeness(list(entries))
    has_photos = any(e.photo_id is not None for e in entries)

    return DailyNutritionSummary(
        date=str(target_date),
        meal_count=len(entries),
        totals=totals,
        goals=goals,
        balance=balance,
        eating_window=eating_window,
        meals=meals,
        data_completeness_pct=completeness,
        has_photo_entries=has_photos,
    )


# ── Photo pipeline (logic side) ────────────────────────────────────────────────

async def get_photo(
    db: AsyncSession, photo_id: uuid.UUID, user_id: uuid.UUID,
) -> Optional[NutritionPhoto]:
    """Récupère une photo avec vérification d'ownership."""
    result = await db.execute(
        select(NutritionPhoto).where(and_(
            NutritionPhoto.id == photo_id,
            NutritionPhoto.user_id == user_id,
            NutritionPhoto.is_deleted.is_(False),
        ))
    )
    return result.scalar_one_or_none()


async def confirm_photo_and_create_entry(
    db: AsyncSession,
    photo: NutritionPhoto,
    data,  # PhotoConfirmRequest
    user_id: uuid.UUID,
) -> dict:
    """
    Valide la photo et crée optionnellement une NutritionEntry.
    Retourne un dict avec photo_id, entry_id (si créée), et macros finales.
    """
    # Corrections utilisateur sur la photo
    photo.user_validated = True
    if data.corrected_foods:
        photo.user_corrections = {"corrected_foods": [f.model_dump() for f in data.corrected_foods]}

    # Macros finales (corrections > analyse IA)
    final_calories = data.corrected_calories if data.corrected_calories is not None else photo.estimated_calories
    final_protein = data.corrected_protein_g if data.corrected_protein_g is not None else photo.estimated_protein_g
    final_carbs = data.corrected_carbs_g if data.corrected_carbs_g is not None else photo.estimated_carbs_g
    final_fat = data.corrected_fat_g if data.corrected_fat_g is not None else photo.estimated_fat_g

    await db.flush()

    entry_id = None
    if data.create_entry:
        # Créer l'entrée nutritionnelle
        entry_data = NutritionEntryCreate(
            meal_type=data.meal_type,
            meal_name=data.meal_name,
            photo_id=photo.id,
            calories=final_calories,
            protein_g=final_protein,
            carbs_g=final_carbs,
            fat_g=final_fat,
            notes=data.notes,
            data_quality="ai_analyzed",
        )
        entry = await create_entry(db, user_id, entry_data)
        # Lier la photo à l'entrée
        photo.entry_id = entry.id
        await db.flush()
        entry_id = entry.id

    return {
        "photo_id": photo.id,
        "user_validated": True,
        "meal_type": data.meal_type,
        "entry_id": entry_id,
        "final_calories": final_calories,
        "final_protein_g": final_protein,
        "final_carbs_g": final_carbs,
        "final_fat_g": final_fat,
    }
