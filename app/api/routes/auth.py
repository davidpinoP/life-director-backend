"""
Authentication Routes
Login and user management.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    Token,
)
from app.db.session import get_db
from app.db import crud
from app.models.user import User, UserCreate, UserLogin, UserResponse
from app.utils.logger import log_auth


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access token.
    """
    
    user = await crud.get_user_by_email(db, credentials.email)
    
    if not user:
        log_auth("login_failed", credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        log_auth("login_failed", credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.flush()
    
    # Generate token
    access_token = create_access_token(user.id)
    
    log_auth("login_success", user.id)
    
    return Token(access_token=access_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user.
    """
    
    # Check if email exists
    existing = await crud.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado",
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    
    created_user = await crud.create(db, user)
    
    log_auth("register", created_user.id)
    
    return UserResponse.model_validate(created_user)
