# Import everything needed
try:
    # For Pydantic v1.x
    from pydantic import BaseSettings
    USING_V1 = True
except ImportError:
    # For Pydantic v2.x
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator
    USING_V1 = False

from functools import lru_cache
from typing import Optional, List, Any, Dict
import os

# Function to parse string to list
def parse_cors_origin(v: Any) -> List[str]:
    if isinstance(v, List):
        return v
    if v == "*":
        return ["*"]
    if isinstance(v, str):
        if "," in v:
            return [item.strip() for item in v.split(",")]
    return [v]

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NZX API"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = ENVIRONMENT == "development"
    PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS_STR: str = (
        "https://app.netzeroxchange.com,"
        "http://localhost:3000"
    )
    CORS_METHODS: str = "*"
    CORS_HEADERS: str = "*"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str | None = None

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from environment variable or use default"""
        origins = os.getenv("CORS_ORIGINS", self.CORS_ORIGINS_STR)
        return [origin.strip() for origin in origins.split(",")]

    class Config:
        env_file = ".env.development" if os.getenv("ENVIRONMENT") == "development" else ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Debug info about CORS settings
    print(f"CORS_ORIGINS type: {type(settings.CORS_ORIGINS)}, value: {settings.CORS_ORIGINS}")
    return settings

settings = get_settings() 