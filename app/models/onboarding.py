"""
Onboarding Model
User intake data for diagnosis.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, JSON
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin


# =============================================================================
# SQLAlchemy Model
# =============================================================================

class OnboardingData(Base, TimestampMixin):
    """Onboarding data database model."""
    
    __tablename__ = "onboarding_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Primary goal
    primary_goal = Column(String(500), nullable=False)
    goal_deadline = Column(String(100), nullable=True)
    
    # Current situation
    current_activities = Column(JSON, nullable=False, default=list)  # List of activities
    hours_work = Column(Float, nullable=True)
    hours_sleep = Column(Float, nullable=True)
    hours_exercise = Column(Float, nullable=True)
    
    # Obstacles
    main_obstacle = Column(String(500), nullable=True)
    secondary_obstacles = Column(JSON, nullable=True, default=list)
    
    # Energy patterns
    peak_energy_time = Column(String(50), nullable=True)  # morning/afternoon/evening
    low_energy_time = Column(String(50), nullable=True)
    
    # Commitments
    fixed_commitments = Column(JSON, nullable=True, default=list)  # Non-negotiable times
    
    # Diagnosis scores (calculated)
    bottleneck_score = Column(Float, nullable=True)
    dispersion_score = Column(Float, nullable=True)
    sleep_debt_score = Column(Float, nullable=True)
    energy_leak_score = Column(Float, nullable=True)
    incoherence_score = Column(Float, nullable=True)


# =============================================================================
# Pydantic Schemas
# =============================================================================

class ActivityInput(BaseModel):
    """Single activity input."""
    name: str = Field(..., max_length=100)
    hours_per_week: float = Field(..., ge=0, le=168)
    priority: int = Field(default=5, ge=1, le=10)  # 1 = lowest, 10 = highest
    aligned_with_goal: bool = False


class OnboardingInput(BaseModel):
    """Onboarding input schema."""
    
    primary_goal: str = Field(..., min_length=5, max_length=500)
    goal_deadline: Optional[str] = None
    
    current_activities: List[ActivityInput] = Field(..., min_length=1, max_length=20)
    
    hours_work: float = Field(..., ge=0, le=24)
    hours_sleep: float = Field(..., ge=0, le=24)
    hours_exercise: float = Field(default=0, ge=0, le=24)
    
    main_obstacle: Optional[str] = Field(None, max_length=500)
    secondary_obstacles: Optional[List[str]] = Field(default_factory=list)
    
    peak_energy_time: Optional[str] = Field(None, pattern="^(morning|afternoon|evening|night)$")
    low_energy_time: Optional[str] = Field(None, pattern="^(morning|afternoon|evening|night)$")
    
    fixed_commitments: Optional[List[str]] = Field(default_factory=list)


class OnboardingResponse(BaseModel):
    """Onboarding response schema."""
    
    id: str
    user_id: str
    primary_goal: str
    
    # Diagnosis summary
    bottleneck_score: Optional[float] = None
    dispersion_score: Optional[float] = None
    sleep_debt_score: Optional[float] = None
    energy_leak_score: Optional[float] = None
    incoherence_score: Optional[float] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiagnosisSummary(BaseModel):
    """Diagnosis result summary."""
    
    primary_bottleneck: str
    bottleneck_severity: float = Field(..., ge=0, le=1)
    
    is_dispersed: bool
    dispersion_count: int
    
    sleep_debt_hours: float
    has_sleep_debt: bool
    
    energy_leak_percentage: float
    
    is_incoherent: bool
    incoherence_details: Optional[str] = None
    
    overall_score: float = Field(..., ge=0, le=1)
    priority_action: str
