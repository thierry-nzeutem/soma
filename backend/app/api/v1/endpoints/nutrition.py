"""
Endpoints nutrition SOMA — LOT 2 + LOT 3.

Périmètre LOT 2 :
  - Bibliothèque d'aliments (FoodItem) : recherche + détail
  - Journal alimentaire (NutritionEntry) : CRUD complet
  - Résumé journalier : GET /nutrition/daily-summary
  - Pipeline photo repas : upload → analyse IA → confirmation → création entrée

Périmètre LOT 3 :
  - Cibles nutritionnelles personnalisées : GET /nutrition/targets
  - Analyse micronutritionnelle : GET /nutrition/micronutrients
  - Recommandations compléments : GET /nutrition/supplements/recommendations

Conventions :
  - Ownership strict : user_id extrait du JWT sur chaque route utilisateur
  - Soft delete : DELETE retourne 204, l'entrée reste en base avec is_deleted=True
  - Commit en endpoint, flush dans les services
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, HTTPException,
    Query, UploadFile, status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.user import User, UserProfile
from app.models.nutrition import NutritionPhoto, NutritionEntry, FoodItem
from app.core.deps import get_current_user
from app.schemas.nutrition import (
    DailyNutritionSummary,
    FoodItemListResponse, FoodItemResponse,
    NutritionEntryCreate, NutritionEntryListResponse,
    NutritionEntryResponse, NutritionEntryUpdate,
    NutritionPhotoUploadResponse, PhotoAnalysisResult,
    PhotoConfirmRequest, PhotoConfirmResponse, DetectedFoodItem,
)
from app.schemas.metrics import (
    NutritionTargetsResponse, MicronutrientDetail, MicronutrientAnalysisResponse,
)
from app.schemas.insights import SupplementRecommendationResponse, SupplementRecommendationsResponse
from app.services import nutrition_service
from app.services.vision_service import analyze_photo_background
from app.utils.storage import delete_photo, save_photo
from app.services.nutrition_engine import compute_nutrition_targets
from app.services.micronutrient_engine import analyze_micronutrients
from app.services.supplement_engine import (
    generate_supplement_recommendations,
    build_analysis_basis,
)


# ── Food Catalog ───────────────────────────────────────────────────────────────

food_router = APIRouter(prefix="/food-items", tags=["Food Catalog"])


@food_router.get("", response_model=FoodItemListResponse)
async def search_food_items(
    query: Optional[str] = Query(None, min_length=1, max_length=100, description="Recherche floue sur le nom"),
    food_group: Optional[str] = Query(None, description="Filtrer par groupe alimentaire"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),  # Authentification requise
):
    """
    Recherche dans la bibliothèque d'aliments.

    Supporte la recherche floue sur les champs `name` et `name_fr`.
    Filtrable par groupe alimentaire (protein, vegetable, fruit, grain, dairy, fat, processed).
    """
    return await nutrition_service.search_food_items(
        db=db, query=query, food_group=food_group, page=page, per_page=per_page,
    )


@food_router.get("/{food_item_id}", response_model=FoodItemResponse)
async def get_food_item(
    food_item_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Récupère le détail d'un aliment par son ID."""
    import uuid
    try:
        fid = uuid.UUID(food_item_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID invalide")

    item = await nutrition_service.get_food_item(db, fid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aliment introuvable")
    return FoodItemResponse.model_validate(item)


# ── Nutrition Entries ──────────────────────────────────────────────────────────

entries_router = APIRouter(prefix="/nutrition/entries", tags=["Nutrition Journal"])


@entries_router.post("", response_model=NutritionEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_nutrition_entry(
    data: NutritionEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crée une entrée nutritionnelle.

    Trois modes de saisie :
    - **Via food_item_id + quantity_g** : macros auto-calculées depuis la base
    - **Via photo_id** : macros pré-remplies depuis l'analyse photo
    - **Saisie directe des macros** : estimation manuelle (calories, protein_g, etc.)

    Les macros explicites ont toujours priorité sur le calcul automatique.
    """
    entry = await nutrition_service.create_entry(db, current_user.id, data)
    await db.commit()
    return NutritionEntryResponse.model_validate(entry)


@entries_router.get("", response_model=NutritionEntryListResponse)
async def list_nutrition_entries(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Filtrer par date (YYYY-MM-DD). Sans date : toutes les entrées récentes.",
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les entrées du journal alimentaire.

    Ordre chronologique ascendant. Supporte la pagination.
    """
    from datetime import date as date_type
    target_date = None
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

    return await nutrition_service.list_entries(
        db=db, user_id=current_user.id, target_date=target_date,
        page=page, per_page=per_page,
    )


@entries_router.get("/{entry_id}", response_model=NutritionEntryResponse)
async def get_nutrition_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Récupère le détail d'une entrée nutritionnelle."""
    import uuid
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID invalide")

    entry = await nutrition_service.get_entry(db, eid, current_user.id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    return NutritionEntryResponse.model_validate(entry)


@entries_router.patch("/{entry_id}", response_model=NutritionEntryResponse)
async def update_nutrition_entry(
    entry_id: str,
    data: NutritionEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Met à jour partiellement une entrée nutritionnelle.

    Seuls les champs fournis dans la requête sont modifiés (PATCH sémantique).
    """
    import uuid
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID invalide")

    entry = await nutrition_service.get_entry(db, eid, current_user.id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")

    entry = await nutrition_service.update_entry(db, entry, data)
    await db.commit()
    return NutritionEntryResponse.model_validate(entry)


@entries_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nutrition_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supprime (soft-delete) une entrée nutritionnelle.

    L'entrée est marquée `is_deleted=True` et n'est plus retournée par les autres endpoints.
    """
    import uuid
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID invalide")

    entry = await nutrition_service.get_entry(db, eid, current_user.id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")

    await nutrition_service.delete_entry(db, entry)
    await db.commit()


# ── Daily Summary ──────────────────────────────────────────────────────────────

summary_router = APIRouter(prefix="/nutrition", tags=["Nutrition Journal"])


@summary_router.get("/daily-summary", response_model=DailyNutritionSummary)
async def get_daily_nutrition_summary(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date cible (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Résumé nutritionnel du jour.

    Retourne :
    - Totaux de macros (calories, protéines, glucides, lipides, fibres)
    - Écarts par rapport aux objectifs du profil
    - Fenêtre alimentaire (premier → dernier repas)
    - Liste résumée des repas
    - Taux de complétude des données
    """
    from datetime import date as date_type
    from sqlalchemy import select
    from app.models.user import UserProfile

    target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.now(timezone.utc).date()

    # Récupère le profil pour les objectifs nutritionnels
    from sqlalchemy import and_
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    return await nutrition_service.get_daily_summary(
        db=db, user_id=current_user.id, target_date=target_date, profile=profile,
    )


# ── Photo Pipeline ─────────────────────────────────────────────────────────────

photos_router = APIRouter(prefix="/nutrition/photos", tags=["Nutrition Photos"])


@photos_router.post("", response_model=NutritionPhotoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_nutrition_photo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Photo de repas (JPEG, PNG, WebP, HEIC — max 10Mo)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload d'une photo de repas avec analyse IA asynchrone.

    **Workflow** :
    1. Upload → retourne `photo_id` immédiatement (statut `pending`)
    2. L'analyse IA est lancée en tâche de fond (Claude Vision)
    3. Sondez `GET /nutrition/photos/{photo_id}` pour suivre le statut
    4. Une fois `analyzed`, confirmez via `POST /nutrition/photos/{photo_id}/confirm`

    **Formats acceptés** : JPEG, PNG, WebP, HEIC (max 10Mo)
    """
    # Sauvegarde du fichier
    file_info = await save_photo(file, current_user.id, subdir="nutrition")

    # Création de l'enregistrement en base
    photo = NutritionPhoto(
        user_id=current_user.id,
        photo_path=file_info["path"],
        taken_at=datetime.now(timezone.utc),
        file_size_bytes=file_info["size_bytes"],
        mime_type=file_info["mime_type"],
        analysis_status="pending",
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    # Lancement de l'analyse en tâche de fond
    background_tasks.add_task(
        analyze_photo_background,
        photo.id,
        file_info["abs_path"],
        db,
    )

    return NutritionPhotoUploadResponse(
        photo_id=photo.id,
        status="pending",
        message=(
            "Photo reçue. L'analyse IA est en cours — "
            "consultez GET /nutrition/photos/{photo_id} pour le résultat."
        ),
    )


@photos_router.get("/{photo_id}", response_model=PhotoAnalysisResult)
async def get_photo_analysis(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Récupère le résultat de l'analyse IA d'une photo de repas.

    Statuts possibles :
    - `pending` : en attente de traitement
    - `analyzing` : analyse en cours
    - `analyzed` : analyse terminée, résultats disponibles
    - `failed` : échec de l'analyse (voir `error_message`)
    """
    import uuid
    try:
        pid = uuid.UUID(photo_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID invalide")

    photo = await nutrition_service.get_photo(db, pid, current_user.id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")

    # Construction de la réponse d'analyse
    identified_foods = None
    if photo.identified_foods:
        try:
            identified_foods = [DetectedFoodItem(**f) for f in photo.identified_foods]
        except Exception:
            identified_foods = None

    ai_meta = photo.ai_analysis or {}
    error_msg = ai_meta.get("error") if photo.analysis_status == "failed" else None
    analyzed_at_str = ai_meta.get("analyzed_at")
    analyzed_at = None
    if analyzed_at_str:
        try:
            analyzed_at = datetime.fromisoformat(analyzed_at_str)
        except Exception:
            pass

    return PhotoAnalysisResult(
        photo_id=photo.id,
        analysis_status=photo.analysis_status,
        identified_foods=identified_foods,
        estimated_calories=photo.estimated_calories,
        estimated_protein_g=photo.estimated_protein_g,
        estimated_carbs_g=photo.estimated_carbs_g,
        estimated_fat_g=photo.estimated_fat_g,
        overall_confidence=photo.confidence_score,
        meal_type_guess=ai_meta.get("meal_type_guess"),
        warnings=ai_meta.get("warnings"),
        assumptions=ai_meta.get("assumptions"),
        error_message=error_msg,
        created_at=photo.created_at,
        analyzed_at=analyzed_at,
    )


@photos_router.post("/{photo_id}/confirm", response_model=PhotoConfirmResponse)
async def confirm_photo(
    photo_id: str,
    data: PhotoConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirme l'analyse IA d'une photo et crée optionnellement une entrée nutritionnelle.

    L'utilisateur peut :
    - Valider les macros estimées telles quelles
    - Corriger les macros (champs `corrected_*`)
    - Corriger la liste des aliments identifiés
    - Définir le type de repas (`meal_type`) et un nom (`meal_name`)

    Si `create_entry=true` (défaut), une `NutritionEntry` est automatiquement créée.
    """
    import uuid
    try:
        pid = uuid.UUID(photo_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID invalide")

    photo = await nutrition_service.get_photo(db, pid, current_user.id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")

    if photo.analysis_status not in ("analyzed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"L'analyse n'est pas encore terminée (statut : {photo.analysis_status}). Attendez avant de confirmer.",
        )

    if photo.user_validated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette photo a déjà été validée.",
        )

    result = await nutrition_service.confirm_photo_and_create_entry(
        db=db, photo=photo, data=data, user_id=current_user.id,
    )
    await db.commit()

    return PhotoConfirmResponse(
        photo_id=result["photo_id"],
        user_validated=result["user_validated"],
        meal_type=result["meal_type"],
        entry_id=result["entry_id"],
        final_calories=result["final_calories"],
        final_protein_g=result["final_protein_g"],
        final_carbs_g=result["final_carbs_g"],
        final_fat_g=result["final_fat_g"],
    )


# ── LOT 3 : Intelligence nutritionnelle ────────────────────────────────────────


@summary_router.get("/targets", response_model=NutritionTargetsResponse)
async def get_nutrition_targets(
    workout_type: Optional[str] = Query(
        None,
        description="Type de séance du jour (strength, cardio, hiit, mobility, mixed).",
    ),
    workout_duration_minutes: Optional[float] = Query(
        None, ge=5, le=300,
        description="Durée de la séance en minutes.",
    ),
    workout_rpe: Optional[float] = Query(
        None, ge=1, le=10,
        description="Effort perçu de la séance (RPE 1-10).",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cibles nutritionnelles personnalisées pour la journée.

    Calcule les besoins en :
    - **Calories** : TDEE + ajustement objectif + bonus entraînement du jour
    - **Protéines** : selon poids, objectif et niveau (ISSN)
    - **Glucides** : résiduels (calories - protéines - lipides)
    - **Lipides** : ratio selon l'objectif (muscle_gain → 25%, weight_loss → 30%)
    - **Fibres** : 14g/1000 kcal (recommandation IOM)
    - **Hydratation** : 33ml/kg + activité + saison

    Paramètres optionnels : type, durée et intensité de la séance du jour
    pour calculer le bonus calorique entraînement.
    """
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()

    usual_wake_str: Optional[str] = None
    if profile and profile.usual_wake_time:
        try:
            usual_wake_str = str(profile.usual_wake_time)[:5]
        except Exception:
            pass

    targets = compute_nutrition_targets(
        age=profile.age if profile else None,
        sex=profile.sex if profile else None,
        height_cm=profile.height_cm if profile else None,
        weight_kg=None,
        body_fat_pct=None,
        activity_level=profile.activity_level if profile else None,
        fitness_level=profile.fitness_level if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        dietary_regime=profile.dietary_regime if profile else None,
        intermittent_fasting=profile.intermittent_fasting if profile else False,
        fasting_protocol=profile.fasting_protocol if profile else None,
        usual_wake_time=usual_wake_str,
        workout_type=workout_type,
        workout_duration_minutes=workout_duration_minutes,
        workout_rpe=workout_rpe,
    )

    return NutritionTargetsResponse(
        calories_target=targets.calories_target,
        protein_target_g=targets.protein_target_g,
        carbs_target_g=targets.carbs_target_g,
        fat_target_g=targets.fat_target_g,
        fiber_target_g=targets.fiber_target_g,
        hydration_target_ml=targets.hydration_target_ml,
        protein_pct=targets.protein_pct,
        carbs_pct=targets.carbs_pct,
        fat_pct=targets.fat_pct,
        base_tdee_kcal=targets.base_tdee_kcal,
        workout_bonus_kcal=targets.workout_bonus_kcal,
        goal_adjustment_kcal=targets.goal_adjustment_kcal,
        target_mode=targets.target_mode,
        eating_window_hours=targets.eating_window_hours,
        fasting_start_at=targets.fasting_start_at,
        reasoning=targets.reasoning,
    )


# Helper dataclass pour passer les entrées à analyze_micronutrients()
@dataclass
class _EntryForMicro:
    """Proxy léger pour les entrées nutritionnelles passées au moteur micronutriments."""
    quantity_g: Optional[float]
    food_group: Optional[str]
    food_item_micronutrients: Optional[dict]
    calories: Optional[float]


@summary_router.get("/micronutrients", response_model=MicronutrientAnalysisResponse)
async def get_micronutrient_analysis(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date d'analyse (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    days: int = Query(
        1, ge=1, le=30,
        description="Fenêtre d'analyse en jours (1-30). Défaut : 1 (aujourd'hui).",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse micronutritionnelle basée sur le journal alimentaire.

    Estime les apports en 8 micronutriments clés :
    - Vitamine D, Magnésium, Potassium, Sodium, Calcium, Fer, Zinc, Oméga-3

    **Sources de données (par fiabilité) :**
    1. Données JSONB du catalogue FoodItem (si l'entrée est liée à un aliment)
    2. Estimation par groupe alimentaire (fallback pour entrées manuelles)

    **Statuts :** sufficient (≥ 80% AJR) | low (50-79%) | deficient (< 50%) | unknown

    Les AJR sont adaptés au sexe du profil (ex: fer 8mg hommes / 18mg femmes).
    """
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()
    sex = profile.sex if profile else None

    # Fenêtre temporelle
    end_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )
    from datetime import timedelta
    start_date = end_date - timedelta(days=days - 1)

    start_dt = datetime(start_date.year, start_date.month, start_date.day,
                        tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day,
                      tzinfo=timezone.utc) + timedelta(days=1)

    # Entrées avec leur FoodItem (si lié)
    entry_res = await db.execute(
        select(NutritionEntry)
        .where(and_(
            NutritionEntry.user_id == current_user.id,
            NutritionEntry.logged_at >= start_dt,
            NutritionEntry.logged_at < end_dt,
            NutritionEntry.is_deleted.is_(False),
        ))
    )
    entries = entry_res.scalars().all()

    # Récupère les FoodItems associés pour leurs données micronutriments
    food_item_cache: dict = {}
    food_item_ids = list({e.food_item_id for e in entries if e.food_item_id})
    if food_item_ids:
        fi_res = await db.execute(
            select(FoodItem).where(FoodItem.id.in_(food_item_ids))
        )
        for fi in fi_res.scalars().all():
            food_item_cache[fi.id] = fi

    # Construction des proxies pour le moteur
    entry_proxies: List[_EntryForMicro] = []
    for e in entries:
        fi = food_item_cache.get(e.food_item_id) if e.food_item_id else None
        entry_proxies.append(_EntryForMicro(
            quantity_g=e.quantity_g,
            food_group=fi.food_group if fi else None,
            food_item_micronutrients=fi.micronutrients if fi else None,
            calories=e.calories,
        ))

    analysis = analyze_micronutrients(entry_proxies, sex=sex, days=days)

    return MicronutrientAnalysisResponse(
        date=end_date.isoformat(),
        overall_micro_score=analysis.overall_micro_score,
        micronutrients=[
            MicronutrientDetail(
                name=r.name,
                name_fr=r.name_fr,
                consumed=r.consumed,
                target=r.target,
                unit=r.unit,
                pct_of_target=r.pct_of_target,
                status=r.status,
                food_sources=r.food_sources,
            )
            for r in analysis.micronutrients
        ],
        top_deficiencies=analysis.top_deficiencies,
        data_quality=analysis.data_quality,
        entries_with_micro_data_pct=analysis.entries_with_micro_data_pct,
        analysis_note=analysis.analysis_note,
    )


@summary_router.get("/supplements/recommendations", response_model=SupplementRecommendationsResponse)
async def get_supplement_recommendations(
    days: int = Query(
        7, ge=1, le=30,
        description="Fenêtre micronutritionnelle pour l'analyse (1-30 jours). Défaut : 7.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recommandations personnalisées de compléments alimentaires.

    Basées sur des règles expertes transparentes :
    - **Vitamine D3** : si déficit détecté dans le journal alimentaire
    - **Magnésium bisglycinate** : si déficit + charge d'entraînement élevée
    - **Oméga-3** : si apport estimé insuffisant
    - **Créatine** : si objectif muscle_gain ou performance + entraînement force
    - **Protéines (whey/végétales)** : si apport protéique < 70% de la cible
    - **Fer** : pour les femmes avec déficit détecté
    - **Zinc** : si déficit détecté

    Maximum 5 suggestions, triées par niveau de confiance décroissant.

    `evidence_type` indique la base :
    - `data_observed` : données réelles du journal
    - `pattern` : pattern d'entraînement/objectif
    - `hypothesis` : estimation (données insuffisantes)

    ⚠️ Ces recommandations sont informatives. Consultez un professionnel de santé.
    """
    profile_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()

    # Analyse micronutritionnelle sur la fenêtre demandée
    end_date = datetime.now(timezone.utc).date()
    from datetime import timedelta
    start_date = end_date - timedelta(days=days - 1)
    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc) + timedelta(days=1)

    entry_res = await db.execute(
        select(NutritionEntry)
        .where(and_(
            NutritionEntry.user_id == current_user.id,
            NutritionEntry.logged_at >= start_dt,
            NutritionEntry.logged_at < end_dt,
            NutritionEntry.is_deleted.is_(False),
        ))
    )
    entries = entry_res.scalars().all()

    food_item_cache: dict = {}
    food_item_ids = list({e.food_item_id for e in entries if e.food_item_id})
    if food_item_ids:
        fi_res = await db.execute(
            select(FoodItem).where(FoodItem.id.in_(food_item_ids))
        )
        for fi in fi_res.scalars().all():
            food_item_cache[fi.id] = fi

    entry_proxies: List[_EntryForMicro] = []
    for e in entries:
        fi = food_item_cache.get(e.food_item_id) if e.food_item_id else None
        entry_proxies.append(_EntryForMicro(
            quantity_g=e.quantity_g,
            food_group=fi.food_group if fi else None,
            food_item_micronutrients=fi.micronutrients if fi else None,
            calories=e.calories,
        ))

    sex = profile.sex if profile else None
    micro_analysis = analyze_micronutrients(entry_proxies, sex=sex, days=days) if entry_proxies else None

    # Ratio protéines réel vs cible
    protein_ratio: Optional[float] = None
    if entries:
        total_protein = sum(e.protein_g or 0 for e in entries) / days
        if profile and profile.target_protein_g and profile.target_protein_g > 0:
            protein_ratio = total_protein / profile.target_protein_g

    # Charge d'entraînement récente (depuis DailyMetrics)
    from app.models.metrics import DailyMetrics
    dm_res = await db.execute(
        select(DailyMetrics)
        .where(and_(
            DailyMetrics.user_id == current_user.id,
            DailyMetrics.metrics_date >= start_date,
        ))
    )
    dm_records = dm_res.scalars().all()
    training_load = sum((r.training_load or 0) for r in dm_records) or None

    # Type d'entraînement dominant
    workout_type: Optional[str] = None
    from app.models.workout import WorkoutSession
    wt_res = await db.execute(
        select(WorkoutSession)
        .where(and_(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.started_at >= start_dt,
            WorkoutSession.is_deleted.is_(False),
        ))
        .order_by(WorkoutSession.started_at.desc())
        .limit(1)
    )
    last_session = wt_res.scalar_one_or_none()
    if last_session:
        workout_type = getattr(last_session, "workout_type", None)

    suggestions = generate_supplement_recommendations(
        primary_goal=profile.primary_goal if profile else None,
        fitness_level=profile.fitness_level if profile else None,
        sex=sex,
        dietary_regime=profile.dietary_regime if profile else None,
        workout_type=workout_type,
        training_load=training_load,
        micro_analysis=micro_analysis,
        protein_ratio=protein_ratio,
    )

    analysis_basis = build_analysis_basis(micro_analysis, training_load, profile.primary_goal if profile else None)

    return SupplementRecommendationsResponse(
        recommendations=[
            SupplementRecommendationResponse(
                supplement_name=s.supplement_name,
                goal=s.goal,
                reason=s.reason,
                observed_data_basis=s.observed_data_basis,
                confidence_level=s.confidence_level,
                evidence_type=s.evidence_type,
                suggested_dose=s.suggested_dose,
                suggested_timing=s.suggested_timing,
                trial_duration_weeks=s.trial_duration_weeks,
                precautions=s.precautions,
            )
            for s in suggestions
        ],
        total=len(suggestions),
        analysis_basis=analysis_basis,
        generated_at=datetime.now(timezone.utc),
    )
