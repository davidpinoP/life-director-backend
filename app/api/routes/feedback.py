"""
Feedback Routes
Additional feedback endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.models.feedback import FeedbackResponse, FeedbackAnalysis
from app.services.anti_block_engine import AntiBlockEngine


router = APIRouter()


@router.get("/history", response_model=List[FeedbackResponse])
async def get_feedback_history(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get feedback history.
    """
    
    feedback_list = await crud.get_user_feedback_history(
        db, 
        current_user.id, 
        limit=min(limit, 100)
    )
    
    return [FeedbackResponse.model_validate(f) for f in feedback_list]


@router.get("/analysis", response_model=FeedbackAnalysis)
async def analyze_feedback(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get analysis of user feedback patterns.
    Now accounts for missed days (plans without feedback).
    """
    
    # 1. Get recent history (plans & feedback)
    recent_plans = await crud.get_recent_plans(db, current_user.id, days=30)
    feedback_history = await crud.get_user_feedback_history(db, current_user.id, limit=30)
    
    if not recent_plans:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos suficientes",
        )
    
    # 2. Map Feedback to Plans
    feedback_map = {f.plan_id: f for f in feedback_history}
    
    stats_data = []
    
    for plan in recent_plans:
        fb = feedback_map.get(plan.id)
        if fb:
            stats_data.append({
                "completion_rate": fb.completion_rate,
                "had_blockers": fb.had_blockers,
                "blocker_type": fb.blocker_type,
                "sleep_hours": fb.sleep_hours,
                "energy_at_start": fb.energy_at_start,
                "energy_at_end": fb.energy_at_end,
                "reported": True
            })
        else:
            # Plan exists but NO feedback -> 0% completion (Missed day)
            # Only count as missed if the plan is from BEFORE today (don't penalize today if incomplete)
            from datetime import date
            if plan.date < date.today():
                stats_data.append({
                    "completion_rate": 0.0,
                    "had_blockers": False,
                    "blocker_type": None,
                    "sleep_hours": None,
                    "energy_at_start": None,
                    "energy_at_end": None,
                    "reported": False
                })
            # If plan is TODAY, we ignore it for stats if not reported yet
    
    if not stats_data:
        # Edge case: only plan is today and no feedback yet
        return FeedbackAnalysis(
            average_completion=0.0,
            total_plans=0,
            recommendation="Completa tu primer día"
        )

    # 3. Calculate Stats
    avg_completion = sum(d["completion_rate"] for d in stats_data) / len(stats_data)
    
    # Analyze blockers (only from reported days)
    reported_data = [d for d in stats_data if d["reported"]]
    
    if reported_data:
        blocker = AntiBlockEngine.get_primary_blocker(reported_data)
        most_common = blocker.blocker_type.value if blocker else None
        blocker_freq = blocker.frequency if blocker else 0.0
        
        # Sleep analysis
        sleep_hours = [d["sleep_hours"] for d in reported_data if d["sleep_hours"]]
        avg_sleep = sum(sleep_hours) / len(sleep_hours) if sleep_hours else None
        
        # Trend analysis
        trend_result = AntiBlockEngine.detect_completion_trend(reported_data)
        
        # Energy pattern
        energy_start = [d["energy_at_start"] for d in reported_data if d["energy_at_start"]]
        energy_end = [d["energy_at_end"] for d in reported_data if d["energy_at_end"]]
        
        if energy_start and energy_end:
            avg_start = sum(energy_start) / len(energy_start)
            avg_end = sum(energy_end) / len(energy_end)
            if avg_start > 6 and avg_end > 6:
                energy_pattern = "consistent"
            elif avg_start > avg_end + 2:
                energy_pattern = "depleting"
            else:
                energy_pattern = "variable"
        else:
            energy_pattern = None
            
    else:
        most_common = None
        blocker_freq = 0.0
        avg_sleep = None
        trend_result = {"trend": "stable", "intervention": None}
        energy_pattern = None

    # 4. Build recommendation
    if avg_completion < 0.5:
        recommendation = "Reduce carga diaria 50% (Muchos días fallidos)"
    elif blocker_freq > 0.3:
        recommendation = blocker.intervention if blocker else "Identifica bloqueos"
    elif trend_result["trend"] == "declining":
        recommendation = trend_result["intervention"] or "Ajusta objetivos"
    else:
        recommendation = "Mantén consistencia"
    
    return FeedbackAnalysis(
        average_completion=avg_completion,
        total_plans=len(stats_data),
        most_common_blocker=most_common,
        blocker_frequency=blocker_freq,
        average_sleep=avg_sleep,
        sleep_trend=trend_result["trend"] if avg_sleep else None,
        energy_pattern=energy_pattern,
        recommendation=recommendation,
    )
