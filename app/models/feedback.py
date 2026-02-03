"""
Feedback Model
User execution feedback on daily plans.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Boolean
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin


# =============================================================================
# SQLAlchemy Model
# =============================================================================

class Feedback(Base, TimestampMixin):
    """Feedback database model."""
    
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String, ForeignKey("daily_plans.id"), nullable=False, index=True)
    
    # Completion
    completion_rate = Column(Float, nullable=False)  # 0.0 to 1.0
    completed_items = Column(JSON, nullable=False, default=list)
    skipped_items = Column(JSON, nullable=False, default=list)
    
    # Blockers
    had_blockers = Column(Boolean, default=False)
    blocker_type = Column(String(100), nullable=True)  # energy, time, external, motivation
    blocker_details = Column(String(500), nullable=True)
    
    # Energy
    energy_at_start = Column(Float, nullable=True)  # 1-10
    energy_at_end = Column(Float, nullable=True)  # 1-10
    
    # Sleep (for next day planning)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(Float, nullable=True)  # 1-10


# =============================================================================
# Pydantic Schemas
# =============================================================================

class FeedbackInput(BaseModel):
    """Feedback input schema."""
    
    plan_id: str
    
    # What was done
    completed_items: List[str] = Field(default_factory=list)
    skipped_items: List[str] = Field(default_factory=list)
    
    # Blockers
    had_blockers: bool = False
    blocker_type: Optional[str] = Field(
        None, 
        pattern="^(energy|time|external|motivation|other)$"
    )
    blocker_details: Optional[str] = Field(None, max_length=500)
    
    # Energy tracking
    energy_at_start: Optional[int] = Field(None, ge=1, le=10)
    energy_at_end: Optional[int] = Field(None, ge=1, le=10)
    
    # Sleep tracking
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)


class FeedbackResponse(BaseModel):
    """Feedback response schema."""
    
    id: str
    user_id: str
    plan_id: str
    completion_rate: float
    had_blockers: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackAnalysis(BaseModel):
    """Analysis of user feedback patterns."""
    
    average_completion: float
    total_plans: int
    
    most_common_blocker: Optional[str] = None
    blocker_frequency: float = 0.0
    
    average_sleep: Optional[float] = None
    sleep_trend: Optional[str] = None  # improving, declining, stable
    
    energy_pattern: Optional[str] = None  # high-am, high-pm, consistent, erratic
    
    recommendation: str
