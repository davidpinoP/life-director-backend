"""
Security Module
JWT tokens, password hashing, authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    exp: datetime


class Token(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # El hash almacenado es: salt$hash
    try:
        salt, stored_hash = hashed_password.split("$")
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode(), 
            salt.encode(), 
            100000
        ).hex()
        return secrets.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    salt = secrets.token_hex(16)
    hash_value = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode(), 
        salt.encode(), 
        100000
    ).hex()
    return f"{salt}${hash_value}"


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token.
    Returns None if invalid.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, exp=exp)
        
    except JWTError:
        return None
