from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.core.auth import get_current_user
from app.core.db import supabase
from app.models.user import UserProfile, UserUpdate, UserCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: str = Depends(get_current_user)):
    """Get the current user's profile"""
    try:
        response = supabase.table("profiles").select("""
            id,
            email,
            first_name,
            last_name,
            organization_id,
            organizations (
                id,
                name,
                domain
            )
        """).eq("id", current_user).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return response.data
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    profile_update: UserUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update the current user's profile"""
    try:
        # First check if organization exists if organization_id is provided
        if profile_update.organization_id:
            org = supabase.table("organizations").select("id").eq("id", profile_update.organization_id).single().execute()
            if not org.data:
                raise HTTPException(status_code=404, detail="Organization not found")

        response = supabase.table("profiles").update(
            profile_update.dict(exclude_unset=True)
        ).eq("id", current_user).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/organization/{org_id}/members", response_model=List[UserProfile])
async def get_organization_members(
    org_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get all members of an organization"""
    try:
        # First verify user belongs to organization
        user = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        if not user.data or user.data["organization_id"] != org_id:
            raise HTTPException(status_code=403, detail="Not authorized to view organization members")

        response = supabase.table("profiles").select("""
            id,
            email,
            first_name,
            last_name,
            created_at,
            updated_at
        """).eq("organization_id", org_id).execute()
        
        return response.data
    except Exception as e:
        logger.error(f"Error getting organization members: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/invite", response_model=UserProfile)
async def invite_user(
    invite: UserCreate,
    current_user: str = Depends(get_current_user)
):
    """Invite a new user to the organization"""
    try:
        # Verify current user belongs to organization
        user = supabase.table("profiles").select("organization_id").eq("id", current_user).single().execute()
        if not user.data or not user.data["organization_id"]:
            raise HTTPException(status_code=403, detail="Must belong to an organization to invite users")

        # Create auth user and profile
        auth_user = supabase.auth.admin.create_user({
            "email": invite.email,
            "email_confirm": True,
            "password": "temporary123", # User will reset this
            "user_metadata": {
                "first_name": invite.first_name,
                "last_name": invite.last_name
            }
        })

        profile = supabase.table("profiles").insert({
            "id": auth_user.user.id,
            "email": invite.email,
            "first_name": invite.first_name,
            "last_name": invite.last_name,
            "organization_id": user.data["organization_id"]
        }).execute()

        return profile.data[0]
    except Exception as e:
        logger.error(f"Error inviting user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 