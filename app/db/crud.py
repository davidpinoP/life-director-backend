"""
CRUD Operations
Database create, read, update, delete operations.
"""

from typing import Optional, List, Type, TypeVar
from datetime import datetime, date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


# =============================================================================
# Generic CRUD
# =============================================================================

async def get_by_id(
    db: AsyncSession, 
    model: Type[ModelType], 
    id: str
) -> Optional[ModelType]:
    """Get a record by ID."""
    result = await db.execute(select(model).where(model.id == id))
    return result.scalar_one_or_none()


async def get_all(
    db: AsyncSession, 
    model: Type[ModelType], 
    limit: int = 100
) -> List[ModelType]:
    """Get all records with limit."""
    result = await db.execute(select(model).limit(limit))
    return result.scalars().all()


async def create(
    db: AsyncSession, 
    obj: ModelType
) -> ModelType:
    """Create a new record."""
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete(
    db: AsyncSession, 
    obj: ModelType
) -> None:
    """Delete a record."""
    await db.delete(obj)
    await db.flush()


# =============================================================================
# User CRUD
# =============================================================================

async def get_user_by_email(
    db: AsyncSession, 
    email: str
) -> Optional["User"]:
    """Get user by email."""
    from app.models.user import User
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession, 
    user_id: str
) -> Optional["User"]:
    """Get user by ID."""
    from app.models.user import User
    return await get_by_id(db, User, user_id)


# =============================================================================
# Onboarding CRUD
# =============================================================================

async def get_user_onboarding(
    db: AsyncSession, 
    user_id: str
) -> Optional["OnboardingData"]:
    """Get user's onboarding data."""
    from app.models.onboarding import OnboardingData
    result = await db.execute(
        select(OnboardingData).where(OnboardingData.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_onboarding(
    db: AsyncSession, 
    user_id: str, 
    data: dict
) -> "OnboardingData":
    """Create or update onboarding data."""
    from app.models.onboarding import OnboardingData
    
    existing = await get_user_onboarding(db, user_id)
    
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        await db.flush()
        return existing
    else:
        onboarding = OnboardingData(user_id=user_id, **data)
        return await create(db, onboarding)


# =============================================================================
# Daily Plan CRUD
# =============================================================================

async def get_today_plan(
    db: AsyncSession, 
    user_id: str
) -> Optional["DailyPlan"]:
    """Get user's plan for today."""
    from app.models.daily_plan import DailyPlan
    
    today = date.today()
    result = await db.execute(
        select(DailyPlan).where(
            and_(
                DailyPlan.user_id == user_id,
                DailyPlan.date == today
            )
        )
    )
    return result.scalar_one_or_none()


async def create_daily_plan(
    db: AsyncSession, 
    user_id: str, 
    plan_data: dict
) -> "DailyPlan":
    """Create a new daily plan."""
    from app.models.daily_plan import DailyPlan
    
    plan = DailyPlan(
        user_id=user_id,
        date=date.today(),
        **plan_data
    )
    return await create(db, plan)


async def get_recent_plans(
    db: AsyncSession, 
    user_id: str, 
    days: int = 7
) -> List["DailyPlan"]:
    """Get user's plans from last N days."""
    from app.models.daily_plan import DailyPlan
    
    result = await db.execute(
        select(DailyPlan)
        .where(DailyPlan.user_id == user_id)
        .order_by(DailyPlan.date.desc())
        .limit(days)
    )
    return result.scalars().all()


# =============================================================================
# Feedback CRUD
# =============================================================================

async def create_feedback(
    db: AsyncSession, 
    user_id: str, 
    plan_id: str, 
    feedback_data: dict
) -> "Feedback":
    """Create feedback for a daily plan."""
    from app.models.feedback import Feedback
    
    feedback = Feedback(
        user_id=user_id,
        plan_id=plan_id,
        **feedback_data
    )
    return await create(db, feedback)


async def get_user_feedback_history(
    db: AsyncSession, 
    user_id: str, 
    limit: int = 30
) -> List["Feedback"]:
    """Get user's feedback history."""
    from app.models.feedback import Feedback
    
    result = await db.execute(
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
