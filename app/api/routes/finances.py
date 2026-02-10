"""
Finance Routes
Income, taxes, and expense tracking endpoints.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.models.finance import (
    FinanceEntryInput,
    FinanceEntryResponse,
    FinanceSummary,
)

router = APIRouter()


@router.post("/", response_model=FinanceEntryResponse)
async def create_finance_entry(
    entry: FinanceEntryInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new finance entry (ingreso, impuesto, or gasto)."""

    data = {
        "type": entry.type,
        "category": entry.category,
        "description": entry.description,
        "amount": entry.amount,
        "date": entry.date or date.today(),
    }

    result = await crud.create_finance_entry(db, current_user.id, data)
    return FinanceEntryResponse.model_validate(result)


@router.get("/", response_model=List[FinanceEntryResponse])
async def list_finance_entries(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """List finance entries for a given month/year. Defaults to current month."""

    today = date.today()
    m = month or today.month
    y = year or today.year

    entries = await crud.get_finance_entries(db, current_user.id, m, y)
    return [FinanceEntryResponse.model_validate(e) for e in entries]


@router.get("/summary", response_model=FinanceSummary)
async def get_finance_summary(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get aggregated finance summary for a month."""

    today = date.today()
    m = month or today.month
    y = year or today.year

    summary = await crud.get_finance_summary(db, current_user.id, m, y)
    return FinanceSummary(**summary)


@router.delete("/{entry_id}")
async def delete_finance_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a finance entry."""

    deleted = await crud.delete_finance_entry(db, entry_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrada no encontrada",
        )

    return {"detail": "Entrada eliminada"}
