"""
Onboarding Routes
User intake and diagnosis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.models.onboarding import (
    OnboardingInput, 
    OnboardingResponse, 
    DiagnosisSummary,
)
from app.services.diagnosis_service import run_diagnosis
from app.utils.logger import log_diagnosis


router = APIRouter()


@router.post("", response_model=OnboardingResponse)
async def submit_onboarding(
    data: OnboardingInput,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Submit onboarding data.
    Triggers diagnosis and stores results.
    """
    try:
        # Convert activities to dict format
        activities = [
            {
                "name": a.name,
                "hours_per_week": a.hours_per_week,
                "priority": a.priority,
                "aligned_with_goal": a.aligned_with_goal,
            }
            for a in data.current_activities
        ]
        
        # Prepare data for storage
        onboarding_data = {
            "primary_goal": data.primary_goal,
            "goal_deadline": data.goal_deadline,
            "current_activities": activities,
            "hours_work": data.hours_work,
            "hours_sleep": data.hours_sleep,
            "hours_exercise": data.hours_exercise,
            "main_obstacle": data.main_obstacle,
            "secondary_obstacles": data.secondary_obstacles,
            "peak_energy_time": data.peak_energy_time,
            "low_energy_time": data.low_energy_time,
            "fixed_commitments": data.fixed_commitments,
        }
        
        # Run diagnosis
        diagnosis = run_diagnosis(onboarding_data)
        
        # Add diagnosis scores to data
        onboarding_data.update({
            "bottleneck_score": diagnosis.bottleneck_score,
            "dispersion_score": diagnosis.dispersion_score,
            "sleep_debt_score": diagnosis.sleep_debt_score,
            "energy_leak_score": diagnosis.energy_leak_score,
            "incoherence_score": diagnosis.incoherence_score,
        })
        
        # Store onboarding
        onboarding = await crud.upsert_onboarding(
            db, 
            current_user.id, 
            onboarding_data
        )

        # Generate achievements roadmap
        try:
            from app.services.achievement_service import AchievementService
            achievement_service = AchievementService(db)
            await achievement_service.generate_user_roadmap(current_user.id, data.primary_goal)
        except Exception as e:
            # Don't fail onboarding if achievement generation fails, but log it
            print(f"Error generating roadmap: {e}")
        
        log_diagnosis(current_user.id, diagnosis.overall_score)
        
        return OnboardingResponse.model_validate(onboarding)
    except Exception as e:
        import traceback
        print(f"ERROR in submit_onboarding: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnosis", response_model=DiagnosisSummary)
async def get_diagnosis(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get current diagnosis for user.
    """
    
    onboarding = await crud.get_user_onboarding(db, current_user.id)
    
    if not onboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding no completado",
        )
    
    # Rebuild diagnosis from stored data
    onboarding_data = {
        "primary_goal": onboarding.primary_goal,
        "current_activities": onboarding.current_activities or [],
        "hours_work": onboarding.hours_work,
        "hours_sleep": onboarding.hours_sleep,
        "main_obstacle": onboarding.main_obstacle,
        "peak_energy_time": onboarding.peak_energy_time,
    }
    
    diagnosis = run_diagnosis(onboarding_data)
    
    return DiagnosisSummary(
        primary_bottleneck=diagnosis.primary_bottleneck,
        bottleneck_severity=diagnosis.bottleneck_score,
        is_dispersed=diagnosis.is_dispersed,
        dispersion_count=diagnosis.active_goals_count,
        sleep_debt_hours=diagnosis.sleep_debt_hours,
        has_sleep_debt=diagnosis.sleep_debt_hours > 1.5,
        energy_leak_percentage=diagnosis.energy_leak_percentage,
        is_incoherent=diagnosis.is_incoherent,
        incoherence_details=diagnosis.incoherence_details,
        overall_score=diagnosis.overall_score,
        priority_action=diagnosis.priority_action,
    )
