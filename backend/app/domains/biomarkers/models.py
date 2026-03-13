"""
SOMA LOT 17 — Biomarkers DB Model.

Tables:
  - lab_results  (résultats biologiques saisies par l'utilisateur)

Pattern:
  - UUIDMixin for pk, TimestampMixin for created_at/updated_at
  - Index composite (user_id, test_date) pour requêtes temporelles
  - marker_name free-text (validé côté service / REFERENCE_RANGES)
"""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import String, Float, Date, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, UUIDMixin, TimestampMixin


class LabResultDB(Base, UUIDMixin, TimestampMixin):
    """
    Single biological lab result for a user.

    marker_name must match a key in REFERENCE_RANGES (biomarkers/service.py):
      vitamin_d, ferritin, crp, testosterone_total, hba1c, fasting_glucose,
      cholesterol_total, hdl, ldl, triglycerides, cortisol, homocysteine,
      magnesium, omega3_index

    value + unit are stored as-is (service validates interpretation).
    """
    __tablename__ = "lab_results"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    marker_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("ix_lab_results_user_date", "user_id", "test_date"),
    )
