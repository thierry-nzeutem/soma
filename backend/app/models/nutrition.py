import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import ForeignKey, String, Boolean, DateTime, func, Float, Integer, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base, UUIDMixin, TimestampMixin


class FoodItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "food_items"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    name_fr: Mapped[Optional[str]] = mapped_column(String(200))
    barcode: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Macros pour 100g
    calories_per_100g: Mapped[Optional[float]] = mapped_column(Float)
    protein_g_per_100g: Mapped[Optional[float]] = mapped_column(Float)
    carbs_g_per_100g: Mapped[Optional[float]] = mapped_column(Float)
    fat_g_per_100g: Mapped[Optional[float]] = mapped_column(Float)
    fiber_g_per_100g: Mapped[Optional[float]] = mapped_column(Float)
    sugar_g_per_100g: Mapped[Optional[float]] = mapped_column(Float)

    # Micronutriments (flexible)
    micronutrients: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Classification
    food_group: Mapped[Optional[str]] = mapped_column(String(50))
    # protein, vegetable, fruit, grain, dairy, fat, processed
    is_ultra_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    nova_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-4

    # Source
    source: Mapped[Optional[str]] = mapped_column(String(50))
    # openfoodfacts, usda, manual, ai_estimated
    external_id: Mapped[Optional[str]] = mapped_column(String(100))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class NutritionPhoto(Base, UUIDMixin):
    """
    Photo de repas avec pipeline d'analyse IA.
    Statuts : pending → analyzed | failed
    Après confirmation utilisateur : user_validated = True
    """
    __tablename__ = "nutrition_photos"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Métadonnées fichier (AJOUT LOT 2)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Liaison à une entrée nutritionnelle (AJOUT LOT 2 — nullable car la photo peut précéder l'entrée)
    entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Résultat analyse IA
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB)
    identified_foods: Mapped[Optional[dict]] = mapped_column(JSONB)
    # [{name, quantity_g, confidence, food_group}, ...]
    estimated_calories: Mapped[Optional[float]] = mapped_column(Float)
    estimated_protein_g: Mapped[Optional[float]] = mapped_column(Float)
    estimated_carbs_g: Mapped[Optional[float]] = mapped_column(Float)
    estimated_fat_g: Mapped[Optional[float]] = mapped_column(Float)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)

    # Validation utilisateur
    user_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    user_corrections: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Statut
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    # pending, analyzing, analyzed, failed

    # Soft delete (AJOUT LOT 2)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NutritionEntry(Base, UUIDMixin):
    """
    Entrée nutritionnelle (repas, collation, boisson, complément).

    Sources possibles :
    - manuelle (food_item_id + quantity_g avec macros auto-calculées)
    - photo analysée (photo_id avec macros depuis l'analyse)
    - saisie directe des macros (estimation manuelle)
    """
    __tablename__ = "nutrition_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    meal_type: Mapped[Optional[str]] = mapped_column(String(30))
    # breakfast, lunch, dinner, snack, supplement, drink
    meal_name: Mapped[Optional[str]] = mapped_column(String(200))  # AJOUT LOT 2 — ex: "Poulet rôti avec riz"

    # Source
    food_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Quantité et valeurs
    quantity_g: Mapped[Optional[float]] = mapped_column(Float)
    calories: Mapped[Optional[float]] = mapped_column(Float)
    protein_g: Mapped[Optional[float]] = mapped_column(Float)
    carbs_g: Mapped[Optional[float]] = mapped_column(Float)
    fat_g: Mapped[Optional[float]] = mapped_column(Float)
    fiber_g: Mapped[Optional[float]] = mapped_column(Float)
    micronutrients: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Qualité de la donnée
    data_quality: Mapped[Optional[str]] = mapped_column(String(20))
    # exact, estimated, inferred, ai_analyzed

    # Contexte
    hunger_before: Mapped[Optional[int]] = mapped_column(Integer)   # 1-10
    satiety_after: Mapped[Optional[int]] = mapped_column(Integer)
    energy_after: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    fasting_window_broken: Mapped[bool] = mapped_column(Boolean, default=False)

    # Soft delete (AJOUT LOT 2)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SupplementRecommendation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplement_recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    supplement_name: Mapped[str] = mapped_column(String(100), nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    observed_data_basis: Mapped[Optional[str]] = mapped_column(Text)
    confidence_level: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    evidence_type: Mapped[Optional[str]] = mapped_column(String(30))
    # data_observed, hypothesis, pattern
    suggested_dose: Mapped[Optional[str]] = mapped_column(String(100))
    suggested_timing: Mapped[Optional[str]] = mapped_column(String(100))
    trial_duration_weeks: Mapped[Optional[int]] = mapped_column(Integer)
    precautions: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
