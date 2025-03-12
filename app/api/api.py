from fastapi import APIRouter
from app.api.endpoints import assets, auth, debug
from datetime import datetime
import os

api_router = APIRouter()

# Core business endpoints
api_router.include_router(
    assets.router, 
    prefix="/assets", 
    tags=["assets"]
)

api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["auth"]
)

# Remove all duplicate routes and keep only these core endpoints:
# /assets/* - All asset related operations
# /auth/* - All authentication operations
# /debug/* - Only in development mode

# Debug routes only in development
from app.core.config import settings
if settings.ENVIRONMENT == "development":
    api_router.include_router(
        debug.router, 
        prefix="/debug", 
        tags=["debug"]
    )

@api_router.get("/")
async def root():
    """Root API endpoint"""
    return {
        "message": "Welcome to the NetZeroXchange API",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@api_router.get("/version")
async def version():
    """Get API version information"""
    return {
        "version": "0.1.0",
        "build": "development",
        "timestamp": datetime.utcnow().isoformat()
    } 