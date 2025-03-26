from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.auth import get_current_user
from app.core.db import supabase
from app.models.organization import Organization, OrganizationCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[Organization])
async def get_organizations(current_user: str = Depends(get_current_user)):
    """Get all organizations for the current user"""
    try:
        response = supabase.table("organizations").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting organizations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=Organization)
async def create_organization(
    org: OrganizationCreate,
    current_user: str = Depends(get_current_user)
):
    """Create a new organization"""
    try:
        # First check if user already has an organization
        user_profile = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        
        if user_profile.data and user_profile.data.get("organization_id"):
            raise HTTPException(
                status_code=400,
                detail="User already belongs to an organization"
            )
        
        # Create organization
        org_response = supabase.table("organizations").insert(org.dict()).execute()
        if not org_response.data:
            raise HTTPException(status_code=400, detail="Failed to create organization")
        
        new_org = org_response.data[0]
        
        # Update user's profile with organization_id
        supabase.table("profiles").update(
            {"organization_id": new_org["id"]}
        ).eq("id", current_user).execute()
        
        return new_org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 