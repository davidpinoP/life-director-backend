"""
IA Life Director - Main Application Entry Point
Sistema Operativo Personal. Decide. No aconseja.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, onboarding, director, feedback, status, achievements, reports, finances
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
allowed_origins = settings.ALLOWED_ORIGINS
is_wildcard = allowed_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not is_wildcard,
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
app.include_router(finances.router, prefix="/finances", tags=["finances"])
app.include_router(status.router, tags=["status"])


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool."""
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections."""
    await close_db()
