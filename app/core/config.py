from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import json

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    FRONTEND_URL: str
    ENVIRONMENT: str = "development"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]  # Default to allowing all origins
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "NZX Energy Platform"
    
    # Override how this field is parsed from environment variables
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 