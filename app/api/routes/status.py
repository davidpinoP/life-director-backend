"""
Status Routes
Health check and system status.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


class StatusResponse(BaseModel):
    """Full status response."""
    status: str
    timestamp: str
    version: str
    database: str
    llm_configured: bool


@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Full system status check.
    """
    
    # Check database
    try:
        await db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Check LLM config
    llm_configured = bool(settings.OPENAI_API_KEY)
    
    return StatusResponse(
        status="operational",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        database=db_status,
        llm_configured=llm_configured,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Simple health check. No dependencies.
    """
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )
