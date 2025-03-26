from fastapi import APIRouter
from app.api.endpoints import (
    auth,
    assets,
    portfolios,
    organizations,
    users,
    debug
)
from datetime import datetime
import os

api_router = APIRouter()

# Auth routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Asset management routes
api_router.include_router(
    assets.router,
    prefix="/assets",
    tags=["assets"]
)

# Portfolio routes
api_router.include_router(
    portfolios.router,
    prefix="/portfolios",
    tags=["portfolios"]
)

# Organization routes
api_router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["organizations"]
)

# User routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Debug routes (only in development)
if os.getenv("ENVIRONMENT") == "development":
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