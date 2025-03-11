from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.core.db import supabase
from datetime import datetime
import logging

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