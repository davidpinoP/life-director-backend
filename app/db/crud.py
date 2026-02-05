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


async def update_user_elite_status(
    db: AsyncSession, 
    user_id: str, 
    is_elite: bool
) -> Optional["User"]:
    """Update user's elite status."""
    from app.models.user import User
    
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
        
    user.is_elite = is_elite
    await db.flush()
    return user


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


async def get_feedback_by_plan_id(
    db: AsyncSession, 
    plan_id: str
) -> Optional["Feedback"]:
    """Get feedback for a specific plan."""
    from app.models.feedback import Feedback
    
    result = await db.execute(
        select(Feedback).where(Feedback.plan_id == plan_id)
    )
    return result.scalar_one_or_none()


# =============================================================================
# Achievement CRUD
# =============================================================================

async def get_user_achievements(
    db: AsyncSession, 
    user_id: str
) -> List["Achievement"]:
    """Get all achievements for a user."""
    from app.models.achievement import Achievement
    
    result = await db.execute(
        select(Achievement)
        .where(Achievement.user_id == user_id)
        .order_by(Achievement.month_number.asc())
    )
    return result.scalars().all()


async def get_active_achievement(
    db: AsyncSession, 
    user_id: str
) -> Optional["Achievement"]:
    """Get the currently active achievement for a user."""
    from app.models.achievement import Achievement
    
    result = await db.execute(
        select(Achievement).where(
            and_(
                Achievement.user_id == user_id,
                Achievement.is_active == True
            )
        )
    )
    return result.scalar_one_or_none()


async def create_achievements_batch(
    db: AsyncSession, 
    user_id: str, 
    achievements_data: List[dict]
) -> List["Achievement"]:
    """Create multiple achievements for a user."""
    from app.models.achievement import Achievement
    
    created_items = []
    for i, data in enumerate(achievements_data):
        achievement = Achievement(
            user_id=user_id,
            month_number=data.get("month", i + 1),
            title=data.get("title"),
            description=data.get("description"),
            is_active=(i == 0), # First month is active by default
            is_unlocked=False,
            progress=0.0
        )
        db.add(achievement)
        created_items.append(achievement)
    
    await db.flush()
    return created_items


async def update_achievement_progress(
    db: AsyncSession, 
    achievement_id: str, 
    progress: float
) -> Optional["Achievement"]:
    """Update progress of an achievement."""
    from app.models.achievement import Achievement
    
    achievement = await get_by_id(db, Achievement, achievement_id)
    if not achievement:
        return None
        
    achievement.progress = min(100.0, max(0.0, progress))
    
    if achievement.progress >= 100.0 and not achievement.is_unlocked:
        achievement.is_unlocked = True
        achievement.unlocked_at = datetime.utcnow()
        
    await db.flush()
    return achievement


# =============================================================================
# Report CRUD
# =============================================================================

async def create_daily_report(
    db: AsyncSession, 
    user_id: str, 
    content: str,
    director_response: str
) -> "DailyReport":
    """Create a daily report."""
    from app.models.report import DailyReport
    
    report = DailyReport(
        user_id=user_id,
        date=date.today(),
        content=content,
        director_response=director_response
    )
    return await create(db, report)


async def get_daily_report_by_date(
    db: AsyncSession, 
    user_id: str,
    report_date: date
) -> Optional["DailyReport"]:
    """Get report for a specific date."""
    from app.models.report import DailyReport
    
    result = await db.execute(
        select(DailyReport).where(
            and_(
                DailyReport.user_id == user_id,
                DailyReport.date == report_date
            )
        )
    )
    return result.scalar_one_or_none()


async def create_post_mortem(
    db: AsyncSession, 
    user_id: str, 
    week_start: date,
    data: dict
) -> "WeeklyPostMortem":
    """Create a weekly post-mortem."""
    from app.models.report import WeeklyPostMortem
    
    pm = WeeklyPostMortem(
        user_id=user_id,
        week_start_date=week_start,
        **data
    )
    return await create(db, pm)


async def get_post_mortem_by_week(
    db: AsyncSession, 
    user_id: str, 
    week_start: date
) -> Optional["WeeklyPostMortem"]:
    """Get post-mortem for a specific week."""
    from app.models.report import WeeklyPostMortem
    
    result = await db.execute(
        select(WeeklyPostMortem).where(
            and_(
                WeeklyPostMortem.user_id == user_id,
                WeeklyPostMortem.week_start_date == week_start
            )
        )
    )
    return result.scalar_one_or_none()
