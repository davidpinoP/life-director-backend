"""
Daily Plan Model
The core output: orders for the day.
"""

import uuid
from datetime import datetime, date
from typing import List, Dict, Optional

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, JSON, Float
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin


# =============================================================================
# SQLAlchemy Model
# =============================================================================

class DailyPlan(Base, TimestampMixin):
    """Daily plan database model."""
    
    __tablename__ = "daily_plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # The plan
    no_hoy = Column(JSON, nullable=False, default=list)  # What NOT to do
    si_hoy = Column(JSON, nullable=False, default=list)  # What TO do
    horarios = Column(JSON, nullable=False, default=dict)  # Time blocks
    regla_clave = Column(String(200), nullable=False)  # Key rule for the day
    
    # Metadata
    diagnosis_snapshot = Column(JSON, nullable=True)  # Diagnosis at time of creation
    llm_tokens_used = Column(Float, nullable=True)
    

# =============================================================================
# Pydantic Schemas
# =============================================================================

class TimeBlock(BaseModel):
    """Single time block."""
    start: str = Field(..., pattern=r"^\d{1,2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{1,2}:\d{2}$")
    activity: str = Field(..., max_length=100)


class DailyPlanRequest(BaseModel):
    """Request for daily plan generation."""
    
    # Optional context for the day
    available_hours: Optional[float] = Field(None, ge=0, le=24)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    existing_commitments: Optional[List[str]] = Field(default_factory=list)
    yesterday_completion: Optional[float] = Field(None, ge=0, le=1)  # 0-100% completion


class DailyPlanOutput(BaseModel):
    """
    The core plan output format.
    This is the ONLY format the LLM must return.
    """
    
    no_hoy: List[str] = Field(..., max_length=5)
    si_hoy: List[str] = Field(..., max_length=3)
    horarios: Dict[str, str] = Field(...)
    regla_clave: str = Field(..., max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "no_hoy": [
                    "Redes sociales",
                    "Reuniones innecesarias",
                    "Proyecto secundario"
                ],
                "si_hoy": [
                    "90 minutos trabajo profundo",
                    "Caminar 30 minutos"
                ],
                "horarios": {
                    "07:00": "Despertar",
                    "07:30": "Trabajo profundo",
                    "09:00": "Pausa",
                    "22:30": "Cama"
                },
                "regla_clave": "Hoy no entrenas. Hoy trabajas."
            }
        }


class DailyPlanResponse(BaseModel):
    """Full daily plan response."""
    
    id: str
    user_id: str
    date: date
    
    no_hoy: List[str]
    si_hoy: List[str]
    horarios: Dict[str, str]
    regla_clave: str
    
    created_at: datetime
    is_completed: bool = False
    
    class Config:
        from_attributes = True


class PlanValidationResult(BaseModel):
    """Result of plan validation."""
    
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PlanHistoryItem(DailyPlanResponse):
    """Extended plan info with feedback status."""
    
    completion_rate: Optional[float] = None
    had_blockers: Optional[bool] = None
    feedback_id: Optional[str] = None
