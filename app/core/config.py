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
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: Optional[str] = None
    FRONTEND_URL: Optional[str] = "http://localhost:3000"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: Any = "*"
    CORS_METHODS: Any = ["*"]
    CORS_HEADERS: Any = ["*"]
    
    # Different config for Pydantic v1 vs v2
    if USING_V1:
        class Config:
            env_file = ".env.development"
            env_file_encoding = "utf-8"
            
            @classmethod
            def customise_sources(cls, init_settings, env_settings, file_secret_settings):
                # Prioritize environment variables over .env file
                return env_settings, init_settings, file_secret_settings
    else:
        # Pydantic v2 configuration
        model_config = SettingsConfigDict(
            env_file=".env.development", 
            env_file_encoding="utf-8",
            extra="ignore"
        )
        
        # Use field validators for Pydantic v2
        @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
        @classmethod
        def parse_cors_values(cls, v):
            return parse_cors_origin(v)

    def get_cors_origins(self) -> List[str]:
        """Safe method to get CORS origins regardless of how they're stored"""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return parse_cors_origin(self.CORS_ORIGINS)

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Debug info about CORS settings
    print(f"CORS_ORIGINS type: {type(settings.CORS_ORIGINS)}, value: {settings.CORS_ORIGINS}")
    return settings

settings = get_settings() 