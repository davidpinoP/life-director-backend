"""
Finance Model
Income, taxes, and expense tracking.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import Column, String, DateTime, Float, Date, ForeignKey
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin


# =============================================================================
# SQLAlchemy Model
# =============================================================================

class FinanceEntry(Base, TimestampMixin):
    """Finance entry database model."""

    __tablename__ = "finance_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, default=date.today)

    # Type: ingreso, impuesto, gasto
    type = Column(String(20), nullable=False)

    # Category: proveedor, material, servicio, suscripcion, otro
    category = Column(String(50), nullable=False, default="otro")

    description = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)


# =============================================================================
# Pydantic Schemas
# =============================================================================

class FinanceEntryInput(BaseModel):
    """Input schema for creating a finance entry."""

    type: str = Field(..., pattern="^(ingreso|impuesto|gasto)$")
    category: str = Field(
        "otro",
        pattern="^(proveedor|material|servicio|suscripcion|nomina|freelance|otro)$"
    )
    description: str = Field(..., max_length=200)
    amount: float = Field(..., gt=0)
    date: Optional[date] = None  # defaults to today


class FinanceEntryResponse(BaseModel):
    """Response schema for a finance entry."""

    id: str
    user_id: str
    date: date
    type: str
    category: str
    description: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class FinanceSummary(BaseModel):
    """Summary of finances for a given period."""

    month: int
    year: int
    total_ingresos: float = 0.0
    total_impuestos: float = 0.0
    total_gastos: float = 0.0
    balance_neto: float = 0.0
    num_entries: int = 0
