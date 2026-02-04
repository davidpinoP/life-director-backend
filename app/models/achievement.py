"""
Achievement Model
Stores monthly milestones and progress.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from app.db.base import Base, TimestampMixin
import uuid

class Achievement(Base, TimestampMixin):
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
