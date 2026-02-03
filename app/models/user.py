"""
User Model
Database model and Pydantic schemas.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean
from pydantic import BaseModel, EmailStr, Field

from app.db.base import Base, TimestampMixin


# =============================================================================
# SQLAlchemy Model
# =============================================================================

class User(Base, TimestampMixin):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)


# =============================================================================
# Pydantic Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema."""
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """User in database schema."""
    id: str
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
