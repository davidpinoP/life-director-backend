"""
Achievements Routes
Endpoints for viewing and tracking progress.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db import crud
from app.models.user import UserInDB
from app.models.achievement import AchievementResponse


router = APIRouter()


@router.get("/", response_model=List[AchievementResponse])
async def get_my_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """List all achievements for the current user."""
    achievements = await crud.get_user_achievements(db, current_user.id)
    return achievements


@router.get("/active", response_model=AchievementResponse)
async def get_active_achievement(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get the currently active achievement."""
    achievement = await crud.get_active_achievement(db, current_user.id)
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay logros activos"
        )
    return achievement
