"""
IA Life Director - Main Application Entry Point
Sistema Operativo Personal. Decide. No aconseja.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, onboarding, director, feedback, status, achievements, reports
from app.core.config import settings
from app.db.session import init_db, close_db

app = FastAPI(
    title="IA Life Director",
    description="Sistema de decisión. Sin motivación. Sin conversación.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# CORS for mobile apps and dev
# Note: allow_credentials=True cannot be used with allow_origins=["*"]
is_wildcard = "*" in settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if not is_wildcard else ["*"],
    allow_credentials=not is_wildcard, # Only allow credentials if we have specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
app.include_router(director.router, prefix="/director", tags=["director"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
app.include_router(reports.router, prefix="/director", tags=["reports"])
app.include_router(status.router, tags=["status"])


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool."""
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections."""
    await close_db()
