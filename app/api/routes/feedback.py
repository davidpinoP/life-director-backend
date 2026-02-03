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
    """
    
    feedback_list = await crud.get_user_feedback_history(db, current_user.id, limit=30)
    
    if not feedback_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay feedback registrado",
        )
    
    # Convert to dict format
    feedback_dicts = [
        {
            "completion_rate": f.completion_rate,
            "had_blockers": f.had_blockers,
            "blocker_type": f.blocker_type,
            "sleep_hours": f.sleep_hours,
            "energy_at_start": f.energy_at_start,
            "energy_at_end": f.energy_at_end,
        }
        for f in feedback_list
    ]
    
    # Calculate stats
    avg_completion = sum(f["completion_rate"] for f in feedback_dicts) / len(feedback_dicts)
    
    # Analyze blockers
    blocker = AntiBlockEngine.get_primary_blocker(feedback_dicts)
    most_common = blocker.blocker_type.value if blocker else None
    blocker_freq = blocker.frequency if blocker else 0.0
    
    # Sleep analysis
    sleep_hours = [f["sleep_hours"] for f in feedback_dicts if f["sleep_hours"]]
    avg_sleep = sum(sleep_hours) / len(sleep_hours) if sleep_hours else None
    
    # Trend analysis
    trend_result = AntiBlockEngine.detect_completion_trend(feedback_dicts)
    
    # Energy pattern
    energy_start = [f["energy_at_start"] for f in feedback_dicts if f["energy_at_start"]]
    energy_end = [f["energy_at_end"] for f in feedback_dicts if f["energy_at_end"]]
    
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
    
    # Build recommendation
    if avg_completion < 0.5:
        recommendation = "Reduce carga diaria 50%"
    elif blocker_freq > 0.3:
        recommendation = blocker.intervention if blocker else "Identifica bloqueos"
    elif trend_result["trend"] == "declining":
        recommendation = trend_result["intervention"] or "Ajusta objetivos"
    else:
        recommendation = "Mantén consistencia"
    
    return FeedbackAnalysis(
        average_completion=avg_completion,
        total_plans=len(feedback_list),
        most_common_blocker=most_common,
        blocker_frequency=blocker_freq,
        average_sleep=avg_sleep,
        sleep_trend=trend_result["trend"] if avg_sleep else None,
        energy_pattern=energy_pattern,
        recommendation=recommendation,
    )
