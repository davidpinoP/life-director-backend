"""
Achievements Routes
Endpoints for gamification system.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.services.achievement_service import AchievementService

router = APIRouter()

class AchievementSchema(BaseModel):
    id: str
    month: int
    title: str
    description: str
    progress: float
    is_unlocked: bool
    is_active: bool
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[AchievementSchema])
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the user's achievement roadmap."""
    achievements = await crud.get_user_achievements(db, current_user.id)
    
    # Map model to schema (handle field name difference: month_number vs month)
    result = []
    for a in achievements:
        result.append(AchievementSchema(
            id=a.id,
            month=a.month_number,
            title=a.title,
            description=a.description,
            progress=a.progress,
            is_unlocked=a.is_unlocked,
            is_active=a.is_active
        ))
        
    return result

@router.post("/generate", response_model=List[AchievementSchema])
async def generate_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate roadmap based on primary goal."""
    # Check if already exists
    existing = await crud.get_user_achievements(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Roadmap already exists")
    
    # Get goal
    onboarding = await crud.get_user_onboarding(db, current_user.id)
    if not onboarding:
        raise HTTPException(status_code=400, detail="Onboarding not completed")
        
    service = AchievementService(db)
    new_achievements = await service.generate_user_roadmap(current_user.id, onboarding.primary_goal)
    
    # Map to schema
    result = []
    for a in new_achievements:
        result.append(AchievementSchema(
            id=a.id,
            month=a.month_number,
            title=a.title,
            description=a.description,
            progress=a.progress,
            is_unlocked=a.is_unlocked,
            is_active=a.is_active
        ))
        
    return result

@router.get("/active", response_model=AchievementSchema)
async def get_active_achievement(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the currently active achievement."""
    achievement = await crud.get_active_achievement(db, current_user.id)
    if not achievement:
        raise HTTPException(status_code=404, detail="No active achievement")
        
    return AchievementSchema(
        id=achievement.id,
        month=achievement.month_number,
        title=achievement.title,
        description=achievement.description,
        progress=achievement.progress,
        is_unlocked=achievement.is_unlocked,
        is_active=achievement.is_active
    )
