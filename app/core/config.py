"""
Application Configuration
Environment variables and settings.
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # App
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/life_director"
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 500
    
    # Rate limiting
    MAX_LLM_CALLS_PER_DAY: int = 50
    
    # CORS - string que se convierte a lista
    ALLOWED_ORIGINS_STR: str = "http://localhost:8080,http://localhost:3000,http://127.0.0.1:8080,http://127.0.0.1:3000"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if self.ALLOWED_ORIGINS_STR == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
