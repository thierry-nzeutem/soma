"""Schémas Pydantic v2 — module nutrition (LOT 2)."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
import uuid


# ── Food Items ─────────────────────────────────────────────────────────────────

class FoodItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    name_fr: Optional[str] = None
    barcode: Optional[str] = None
    # Macros / 100g
    calories_per_100g: Optional[float] = None
    protein_g_per_100g: Optional[float] = None
    carbs_g_per_100g: Optional[float] = None
    fat_g_per_100g: Optional[float] = None
    fiber_g_per_100g: Optional[float] = None
    sugar_g_per_100g: Optional[float] = None
    # Classification
    food_group: Optional[str] = None
    is_ultra_processed: bool = False
    nova_score: Optional[int] = None
    source: Optional[str] = None
    verified: bool = False


class FoodItemListResponse(BaseModel):
    items: List[FoodItemResponse]
    total: int
    page: int
    per_page: int


# ── Nutrition Entries ───────────────────────────────────────────────────────────

class NutritionEntryCreate(BaseModel):
    """
    Création d'une entrée nutritionnelle.

    Trois modes de saisie :
    A. Via food_item_id + quantity_g → macros auto-calculées si non fournies
    B. Via photo_id → macros pré-remplies depuis l'analyse photo
    C. Saisie directe des macros (estimation manuelle)
    """
    logged_at: Optional[datetime] = None        # défaut = now()
    meal_type: Optional[str] = Field(
        None,
        pattern="^(breakfast|lunch|dinner|snack|supplement|drink)$",
    )
    meal_name: Optional[str] = Field(None, max_length=200)

    # Source
    food_item_id: Optional[uuid.UUID] = None
    photo_id: Optional[uuid.UUID] = None
    quantity_g: Optional[float] = Field(None, ge=0.0)

    # Macros (explicites ou auto-calculées)
    calories: Optional[float] = Field(None, ge=0.0)
    protein_g: Optional[float] = Field(None, ge=0.0)
    carbs_g: Optional[float] = Field(None, ge=0.0)
    fat_g: Optional[float] = Field(None, ge=0.0)
    fiber_g: Optional[float] = Field(None, ge=0.0)

    # Qualité de la donnée
    data_quality: Optional[str] = Field(
        None, pattern="^(exact|estimated|inferred|ai_analyzed)$"
    )

    # Contexte
    hunger_before: Optional[int] = Field(None, ge=1, le=10)
    satiety_after: Optional[int] = Field(None, ge=1, le=10)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    fasting_window_broken: bool = False

    @model_validator(mode="after")
    def validate_at_least_one_source(self) -> "NutritionEntryCreate":
        """Au moins une source ou des macros explicites sont nécessaires."""
        has_source = bool(self.food_item_id or self.photo_id)
        has_macros = any([self.calories, self.protein_g, self.carbs_g, self.fat_g])
        if not has_source and not has_macros:
            raise ValueError(
                "Au moins un food_item_id, un photo_id, ou des macros explicites sont nécessaires."
            )
        return self


class NutritionEntryUpdate(BaseModel):
    meal_type: Optional[str] = Field(None, pattern="^(breakfast|lunch|dinner|snack|supplement|drink)$")
    meal_name: Optional[str] = Field(None, max_length=200)
    logged_at: Optional[datetime] = None
    quantity_g: Optional[float] = Field(None, ge=0.0)
    calories: Optional[float] = Field(None, ge=0.0)
    protein_g: Optional[float] = Field(None, ge=0.0)
    carbs_g: Optional[float] = Field(None, ge=0.0)
    fat_g: Optional[float] = Field(None, ge=0.0)
    fiber_g: Optional[float] = Field(None, ge=0.0)
    data_quality: Optional[str] = Field(None, pattern="^(exact|estimated|inferred|ai_analyzed)$")
    hunger_before: Optional[int] = Field(None, ge=1, le=10)
    satiety_after: Optional[int] = Field(None, ge=1, le=10)
    energy_after: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class NutritionEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    logged_at: datetime
    meal_type: Optional[str] = None
    meal_name: Optional[str] = None
    food_item_id: Optional[uuid.UUID] = None
    photo_id: Optional[uuid.UUID] = None
    quantity_g: Optional[float] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    data_quality: Optional[str] = None
    hunger_before: Optional[int] = None
    satiety_after: Optional[int] = None
    energy_after: Optional[int] = None
    notes: Optional[str] = None
    fasting_window_broken: bool = False
    created_at: datetime
    updated_at: datetime


class NutritionEntryListResponse(BaseModel):
    entries: List[NutritionEntryResponse]
    total: int
    date: Optional[str] = None


# ── Daily Nutrition Summary ────────────────────────────────────────────────────

class MacroGoals(BaseModel):
    """Objectifs nutritionnels du profil utilisateur."""
    calories_target: Optional[float] = None
    protein_target_g: Optional[float] = None
    carbs_target_g: Optional[float] = None
    fat_target_g: Optional[float] = None


class MacroActuals(BaseModel):
    """Totaux nutritionnels réels du jour."""
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0


class MacroBalance(BaseModel):
    """Écart entre réel et objectif (positif = surplus, négatif = déficit)."""
    calories_delta: Optional[float] = None
    protein_delta_g: Optional[float] = None
    carbs_delta_g: Optional[float] = None
    fat_delta_g: Optional[float] = None
    pct_calories_reached: Optional[float] = None
    pct_protein_reached: Optional[float] = None


class MealSummaryItem(BaseModel):
    """Résumé d'un repas dans le journal."""
    id: uuid.UUID
    meal_type: Optional[str] = None
    meal_name: Optional[str] = None
    logged_at: datetime
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    data_quality: Optional[str] = None


class EatingWindow(BaseModel):
    """Fenêtre alimentaire estimée (premier repas → dernier repas)."""
    first_meal_at: Optional[datetime] = None
    last_meal_at: Optional[datetime] = None
    window_hours: Optional[float] = None
    fasting_compatible: Optional[bool] = None  # window ≤ 8h si jeûne 16:8


class DailyNutritionSummary(BaseModel):
    date: str
    meal_count: int
    totals: MacroActuals
    goals: Optional[MacroGoals] = None
    balance: Optional[MacroBalance] = None
    eating_window: EatingWindow
    meals: List[MealSummaryItem] = []
    data_completeness_pct: float     # % d'entrées avec calories renseignées
    has_photo_entries: bool = False


# ── Photo Upload & Analysis Pipeline ──────────────────────────────────────────

class NutritionPhotoUploadResponse(BaseModel):
    """Réponse immédiate après upload (analyse asynchrone)."""
    photo_id: uuid.UUID
    status: str  # "pending" ou "analyzing"
    message: str


class DetectedFoodItem(BaseModel):
    """Aliment détecté par Claude Vision."""
    name: str
    name_fr: Optional[str] = None
    quantity_g: Optional[float] = None
    calories_estimated: Optional[float] = None
    protein_g_estimated: Optional[float] = None
    carbs_g_estimated: Optional[float] = None
    fat_g_estimated: Optional[float] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    food_group: Optional[str] = None
    notes: Optional[str] = None


class PhotoAnalysisResult(BaseModel):
    """Résultat structuré de l'analyse IA."""
    photo_id: uuid.UUID
    analysis_status: str       # pending, analyzing, analyzed, failed
    identified_foods: Optional[List[DetectedFoodItem]] = None
    estimated_calories: Optional[float] = None
    estimated_protein_g: Optional[float] = None
    estimated_carbs_g: Optional[float] = None
    estimated_fat_g: Optional[float] = None
    overall_confidence: Optional[float] = None
    meal_type_guess: Optional[str] = None
    warnings: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None


class PhotoConfirmRequest(BaseModel):
    """
    Confirmation par l'utilisateur de l'analyse photo.
    Peut inclure des corrections sur les aliments ou les macros.
    """
    meal_type: Optional[str] = Field(None, pattern="^(breakfast|lunch|dinner|snack|supplement|drink)$")
    meal_name: Optional[str] = Field(None, max_length=200)
    # Corrections optionnelles (remplacent les valeurs IA)
    corrected_calories: Optional[float] = Field(None, ge=0.0)
    corrected_protein_g: Optional[float] = Field(None, ge=0.0)
    corrected_carbs_g: Optional[float] = Field(None, ge=0.0)
    corrected_fat_g: Optional[float] = Field(None, ge=0.0)
    corrected_foods: Optional[List[DetectedFoodItem]] = None
    notes: Optional[str] = None
    # Si True, crée automatiquement une NutritionEntry après confirmation
    create_entry: bool = True


class PhotoConfirmResponse(BaseModel):
    photo_id: uuid.UUID
    user_validated: bool
    meal_type: Optional[str]
    # Si create_entry=True
    entry_id: Optional[uuid.UUID] = None
    final_calories: Optional[float] = None
    final_protein_g: Optional[float] = None
    final_carbs_g: Optional[float] = None
    final_fat_g: Optional[float] = None
