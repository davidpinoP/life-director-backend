"""
Director Routes
Core functionality: daily plan generation.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.models.daily_plan import (
    DailyPlanRequest, 
    DailyPlanResponse,
    DailyPlanOutput,
)
from app.models.feedback import FeedbackInput, FeedbackResponse
from app.services.diagnosis_service import run_diagnosis
from app.services.decision_engine import generate_plan
from app.services.memory_service import MemoryService
from app.services.anti_block_engine import AntiBlockEngine
from app.utils.logger import log_plan_generated


router = APIRouter()


@router.post("/daily-plan", response_model=DailyPlanResponse)
async def create_daily_plan(
    request: DailyPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate daily plan.
    
    The core endpoint. Analyzes user, decides priorities, returns orders.
    """
    
    # Check if user has onboarding
    onboarding = await crud.get_user_onboarding(db, current_user.id)
    
    if not onboarding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completa onboarding primero",
        )
    
    # Check if plan already exists for today
    existing_plan = await crud.get_today_plan(db, current_user.id)
    
    if existing_plan:
        # Return existing plan
        return DailyPlanResponse.model_validate(existing_plan)
    
    # Build onboarding data dict
    onboarding_data = {
        "primary_goal": onboarding.primary_goal,
        "current_activities": onboarding.current_activities or [],
        "hours_work": onboarding.hours_work,
        "hours_sleep": onboarding.hours_sleep,
        "main_obstacle": onboarding.main_obstacle,
        "peak_energy_time": onboarding.peak_energy_time,
    }
    
    # Run diagnosis
    diagnosis = run_diagnosis(onboarding_data)
    
    # Get memory/history
    memory = MemoryService(db)
    context = await memory.get_user_context(current_user.id)
    
    # Check for blocking patterns
    feedback_history = context.get("feedback_history", [])
    blocker = AntiBlockEngine.get_primary_blocker(feedback_history)
    
    # Build request context
    from datetime import datetime
    import locale
    
    # Calculate days active
    days_active = (datetime.utcnow() - onboarding.created_at).days + 1
    
    # Calculate day name in Spanish
    days_map = {
        0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
        4: "Viernes", 5: "Sábado", 6: "Domingo"
    }
    current_day = days_map[datetime.utcnow().weekday()]
    
    plan_context = {
        "available_hours": request.available_hours,
        "energy_level": request.energy_level,
        "existing_commitments": request.existing_commitments,
        "yesterday_completion": request.yesterday_completion,
        
        # New context for goal-oriented planning
        "primary_goal": onboarding.primary_goal,
        "goal_deadline": onboarding.goal_deadline or "Sin fecha límite",
        "day_of_week": current_day,
        "days_active": days_active,
    }
    
    if blocker and blocker.pattern_detected:
        plan_context["blocker_intervention"] = blocker.intervention
    
    # Generate plan
    try:
        result = await generate_plan(
            diagnosis=diagnosis,
            context=plan_context,
            history=feedback_history,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando plan: {str(e)}"
        )
    
    plan_data = result["plan"]
    
    # Store plan
    stored_plan = await crud.create_daily_plan(
        db,
        current_user.id,
        {
            "no_hoy": plan_data["no_hoy"],
            "si_hoy": plan_data["si_hoy"],
            "horarios": plan_data["horarios"],
            "regla_clave": plan_data["regla_clave"],
            "diagnosis_snapshot": {
                "bottleneck": diagnosis.primary_bottleneck,
                "overall_score": diagnosis.overall_score,
            },
            "llm_tokens_used": result["tokens_used"],
        }
    )
    
    log_plan_generated(current_user.id, result["tokens_used"])
    
    return DailyPlanResponse.model_validate(stored_plan)


@router.get("/today", response_model=DailyPlanResponse)
async def get_today_plan(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get today's plan if it exists.
    """
    
    plan = await crud.get_today_plan(db, current_user.id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay plan para hoy",
        )
    
    return DailyPlanResponse.model_validate(plan)


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Submit feedback on a daily plan.
    """
    
    # Validate plan exists
    from app.db.crud import get_by_id
    from app.models.daily_plan import DailyPlan
    
    plan = await get_by_id(db, DailyPlan, feedback.plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado",
        )
    
    if plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        )
    
    # Calculate completion rate
    total_items = len(plan.si_hoy)
    completed = len(feedback.completed_items)
    completion_rate = completed / total_items if total_items > 0 else 0.0
    
    # Create feedback
    feedback_record = await crud.create_feedback(
        db,
        current_user.id,
        feedback.plan_id,
        {
            "completion_rate": completion_rate,
            "completed_items": feedback.completed_items,
            "skipped_items": feedback.skipped_items,
            "had_blockers": feedback.had_blockers,
            "blocker_type": feedback.blocker_type,
            "blocker_details": feedback.blocker_details,
            "energy_at_start": feedback.energy_at_start,
            "energy_at_end": feedback.energy_at_end,
            "sleep_hours": feedback.sleep_hours,
            "sleep_quality": feedback.sleep_quality,
        }
    )

    # Update achievement progress
    from app.services.achievement_service import AchievementService
    achievement_service = AchievementService(db)
    await achievement_service.update_active_achievement_progress(current_user.id, completion_rate)
    
    return FeedbackResponse.model_validate(feedback_record)

from app.models.daily_plan import DailyPlanResponse, PlanHistoryItem

@router.get("/history", response_model=List[PlanHistoryItem])
async def get_plan_history(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get full history of daily plans.
    """
    
    # Get recent plans
    plans = await crud.get_recent_plans(db, current_user.id, limit)
    
    # Get feedback dict
    feedback_list = await crud.get_user_feedback_history(db, current_user.id, limit)
    feedback_map = {f.plan_id: f for f in feedback_list}
    
    history_items = []
    for plan in plans:
        item = PlanHistoryItem.model_validate(plan)
        
        # Attach feedback info if exists
        if plan.id in feedback_map:
            fb = feedback_map[plan.id]
            item.completion_rate = fb.completion_rate
            item.had_blockers = fb.had_blockers
            item.feedback_id = fb.id
            
        history_items.append(item)
        
    return history_items
