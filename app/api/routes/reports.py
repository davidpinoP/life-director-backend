"""
Reports Routes
Endpoints for Daily Reports and Weekly Post-Mortems.
"""

from typing import Optional, Dict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.models.report import (
    DailyReportInput, DailyReportResponse,
    PostMortemInput, PostMortemResponse
)
from app.services.report_service import ReportService

router = APIRouter()

# --- Daily Report ---

@router.get("/report/today", response_model=Optional[DailyReportResponse])
async def check_daily_report(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Check if daily report submitted today."""
    report = await crud.get_daily_report_by_date(db, current_user.id, date.today())
    if not report:
        return None
    return DailyReportResponse.model_validate(report)


@router.post("/report", response_model=DailyReportResponse)
async def submit_daily_report(
    data: DailyReportInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Submit factual daily report and get decision."""
    # Check duplicate
    existing = await crud.get_daily_report_by_date(db, current_user.id, date.today())
    if existing:
        raise HTTPException(status_code=400, detail="Ya enviaste tu informe hoy.")
        
    onboarding = await crud.get_user_onboarding(db, current_user.id)
    if not onboarding:
        raise HTTPException(status_code=400, detail="Completa onboarding primero.")

    # Call AI
    service = ReportService()
    decision = await service.analyze_daily_report(data.content, onboarding.primary_goal)
    
    # Store
    report = await crud.create_daily_report(
        db,
        current_user.id,
        data.content,
        decision
    )
    
    return DailyReportResponse.model_validate(report)


# --- Post Mortem ---

@router.get("/post-mortem/status")
async def check_post_mortem_status(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Check eligibility for Post-Mortem.
    Returns { "is_eligible": bool, "reason": str, "week_start": date }
    """
    if not current_user.is_elite:
        return {"is_eligible": False, "reason": "Requiere Nivel Élite"}
        
    today = date.today()
    # Assuming Post-Mortem is allowed on Sunday (6) or Monday (0)
    # We define "Week Start" as the *previous* Monday.
    
    weekday = today.weekday() # 0=Mon, 6=Sun
    
    if weekday != 6 and weekday != 0: # Only allowed Sun/Mon
        return {"is_eligible": False, "reason": "Solo disponible Domingo o Lunes"}
        
    # Calculate week start date (previous Monday)
    if weekday == 0: # Monday: week start was 7 days ago
        week_start = today - timedelta(days=7)
    else: # Sunday: week start was 6 days ago
        week_start = today - timedelta(days=6)
        
    # Check if already submitted
    existing = await crud.get_post_mortem_by_week(db, current_user.id, week_start)
    if existing:
        return {
            "is_eligible": False, 
            "reason": "Ya enviaste tu Post-Mortem de esta semana",
            "week_start": week_start
        }
        
    return {
        "is_eligible": True, 
        "reason": "Disponible",
        "week_start": week_start
    }


@router.post("/post-mortem", response_model=PostMortemResponse)
async def submit_post_mortem(
    data: PostMortemInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Submit weekly post-mortem."""
    # Security check is implicitly handled by status check logic, but we enforce it here
    if not current_user.is_elite:
        raise HTTPException(status_code=403, detail="Requiere Nivel Élite")
        
    # Check duplicate
    existing = await crud.get_post_mortem_by_week(db, current_user.id, data.week_start_date)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe reporte para esta semana")

    onboarding = await crud.get_user_onboarding(db, current_user.id)
    
    # Call AI
    service = ReportService()
    result = await service.analyze_post_mortem(
        data.content_good,
        data.content_bad,
        data.content_delusion,
        onboarding.primary_goal
    )
    
    # Store
    pm = await crud.create_post_mortem(
        db,
        current_user.id,
        data.week_start_date,
        {
            "content_good": data.content_good,
            "content_bad": data.content_bad,
            "content_delusion": data.content_delusion,
            "response_adjustments": result["adjustments"],
            "response_cuts": result["cuts"],
            "response_rules": result["rules"]
        }
    )
    
    return PostMortemResponse.model_validate(pm)
