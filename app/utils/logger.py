"""
Logger Utility
Minimal logging. Essential info only.
"""

import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings


# Configure logger
logger = logging.getLogger("life_director")
logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

# Console handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Minimal format
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)


def log_request(endpoint: str, user_id: Optional[str] = None) -> None:
    """Log API request."""
    if settings.DEBUG:
        user_str = f" | user:{user_id}" if user_id else ""
        logger.debug(f"REQ | {endpoint}{user_str}")


def log_error(message: str, error: Optional[Exception] = None) -> None:
    """Log error."""
    error_str = f" | {type(error).__name__}: {error}" if error else ""
    logger.error(f"ERR | {message}{error_str}")


def log_llm_call(tokens: int, model: str) -> None:
    """Log LLM API call for cost tracking."""
    logger.info(f"LLM | {model} | tokens:{tokens}")


def log_diagnosis(user_id: str, overall_score: float) -> None:
    """Log diagnosis run."""
    logger.info(f"DX | user:{user_id} | score:{overall_score:.2f}")


def log_plan_generated(user_id: str, tokens: int) -> None:
    """Log plan generation."""
    logger.info(f"PLAN | user:{user_id} | tokens:{tokens}")


def log_auth(event: str, user_id: Optional[str] = None) -> None:
    """Log authentication event."""
    user_str = user_id if user_id else "unknown"
    logger.info(f"AUTH | {event} | {user_str}")


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self, label: str):
        self.label = label
        self.start = None
    
    def __enter__(self):
        self.start = datetime.now()
        return self
    
    def __exit__(self, *args):
        if settings.DEBUG and self.start:
            elapsed = (datetime.now() - self.start).total_seconds() * 1000
            logger.debug(f"TIME | {self.label} | {elapsed:.0f}ms")
