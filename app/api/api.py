from fastapi import APIRouter
from app.api.endpoints import assets, auth, debug

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