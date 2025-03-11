from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    FRONTEND_URL: str
    ENVIRONMENT: str = "development"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000" if ENVIRONMENT == "development" 
        else "https://app.netzeroxchange.com"
    ]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "NZX Energy Platform"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 