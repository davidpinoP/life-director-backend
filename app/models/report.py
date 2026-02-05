"""
Report Models
Models for "Informe al Director" module.
"""

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Column, String, Date, ForeignKey, Text
from pydantic import BaseModel, Field

from app.db.base import Base, TimestampMixin


# =============================================================================
# SQLAlchemy Models
# =============================================================================

class DailyReport(Base, TimestampMixin):
    """Daily factual report from user."""
    
    __tablename__ = "daily_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    content = Column(Text, nullable=False)  # Max 5-6 lines
    director_response = Column(Text, nullable=False) # Decision


class WeeklyPostMortem(Base, TimestampMixin):
    """Weekly reflection for Elite users."""
    
    __tablename__ = "weekly_post_mortems"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False, index=True) # Monday of the week
    
    # The 3 Questions
    content_good = Column(Text, nullable=False) # What worked
    content_bad = Column(Text, nullable=False) # What didn't work
    content_delusion = Column(Text, nullable=False) # Where did I fool myself?
    
    # The 3 Responses
    response_adjustments = Column(Text, nullable=False)
    response_cuts = Column(Text, nullable=False)
    response_rules = Column(Text, nullable=False)


# =============================================================================
# Pydantic Schemas
# =============================================================================

# --- Daily Report ---

class DailyReportInput(BaseModel):
    content: str = Field(..., max_length=1000)

class DailyReportResponse(BaseModel):
    id: str
    date: date
    content: str
    director_response: str
    
    class Config:
        from_attributes = True

# --- Post Mortem ---

class PostMortemInput(BaseModel):
    week_start_date: date
    content_good: str
    content_bad: str
    content_delusion: str

class PostMortemResponse(BaseModel):
    id: str
    week_start_date: date
    response_adjustments: str
    response_cuts: str
    response_rules: str
    
    class Config:
        from_attributes = True
