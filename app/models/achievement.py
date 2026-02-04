import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin


class Achievement(Base, TimestampMixin):
    """Achievement database model."""
    __tablename__ = "achievements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    month_number = Column(Integer, nullable=False) # 1 to 6
    title = Column(String, nullable=False)
    description = Column(String)
    
    progress = Column(Float, default=0.0) # 0.0 to 100.0
    is_unlocked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False) # Only current month is active?
    
    unlocked_at = Column(DateTime, nullable=True)


# =============================================================================
# Pydantic Schemas
# =============================================================================

class AchievementResponse(BaseModel):
    """Achievement response schema."""
    id: str
    user_id: str
    month_number: int
    title: str
    description: Optional[str]
    progress: float
    is_unlocked: bool
    is_active: bool
    unlocked_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AchievementUpdate(BaseModel):
    """Schema for updating achievement progress."""
    progress: float = Field(..., ge=0, le=100)
    is_unlocked: Optional[bool] = None
    is_active: Optional[bool] = None


class AchievementBatchCreate(BaseModel):
    """Schema for creating a batch of achievements."""
    month_number: int
    title: str
    description: str
