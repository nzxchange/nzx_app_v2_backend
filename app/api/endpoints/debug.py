from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.core.db import supabase
from datetime import datetime
import logging
import threading
import os
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/new-asset-page")
async def debug_new_asset_page():
    """Debug endpoint for new asset page"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/routes")
async def debug_routes():
    """List all available routes"""
    return {"message": "Routes listing endpoint"}

@router.get("/auth")
async def debug_auth(current_user: str = Depends(get_current_user)):
    """Test authentication"""
    return {"authenticated": True, "user_id": current_user}

@router.get("/supabase")
async def debug_supabase():
    """Test Supabase connection"""
    try:
        response = supabase.table("profiles").select("count").limit(1).execute()
        return {"status": "ok", "data": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/db-test")
async def test_database_connection():
    """Test Supabase connection"""
    try:
        response = supabase.table("profiles").select("count").limit(1).execute()
        return {
            "status": "connected",
            "data": response.data,
            "error": None
        }
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/supabase-test")
async def test_supabase_simple():
    """Simple Supabase test with timeout protection"""
    result = {"status": "unknown", "error": None}
    
    def supabase_call():
        try:
            # Set a flag to indicate the call started
            result["started"] = True
            
            # Make a simple call to Supabase
            response = supabase.auth.get_session()
            
            # Update result with success
            result["status"] = "success"
            result["data"] = "Connected"
        except Exception as e:
            # Update result with error
            result["status"] = "error"
            result["error"] = str(e)
    
    # Start the Supabase call in a thread
    t = threading.Thread(target=supabase_call)
    t.daemon = True
    t.start()
    
    # Wait for the thread to finish, but with a timeout
    t.join(timeout=5.0)
    
    if result["status"] == "unknown":
        result["status"] = "timeout"
        result["error"] = "Supabase call timed out after 5 seconds"
    
    return result 

@router.get("/env-check")
async def check_environment():
    """Check environment variables"""
    # Get a sanitized version of environment variables (hide secrets)
    env_vars = {}
    for key, value in os.environ.items():
        if "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
            env_vars[key] = "***REDACTED***"
        else:
            env_vars[key] = value
            
    return {
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "env_vars": env_vars,
        "supabase_url": os.getenv("SUPABASE_URL", "not set")
    }

@router.get("/test-assets-types")
async def test_assets_types():
    """Test endpoint for asset types"""
    return {
        "status": "ok",
        "message": "Debug endpoint working",
        "cors_origins": settings.CORS_ORIGINS,
        "test_types": [
            {"id": "test", "name": "Test"}
        ]
    } 